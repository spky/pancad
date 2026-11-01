"""A module of functions for calculating the constraint solving residuals while solving geometry
systems.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections import Counter
from collections.abc import Mapping, Collection, Iterable, Sequence
import itertools
from functools import partial, cached_property, singledispatchmethod
from typing import TYPE_CHECKING, NamedTuple, Generic, Type, TypeVar, TypedDict, overload

import math
import numpy as np

from pancad.abstract import AbstractConstraint, AbstractGeometry, PancadThing
from pancad.constants import SketchConstraint as SC, ConstraintEquationName as CEN
from pancad.constraints.snapto import Fixed
from pancad.constraints.state_constraint import Coincident, Parallel, Codirectional, Antiparallel
from pancad.geometry.line import Axis, Line
from pancad.geometry.plane import Plane
from pancad.geometry.point import Point
from pancad.utils.geometry import get_unique_vector

T = TypeVar("T")
U = TypeVar("U")
V = TypeVar("V")

# An unordered list of distinct geometry types. Indicates applicability.
GeoCombo = frozenset[Type[AbstractGeometry]]



if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from typing import Self, NotRequired, Final, Never

    from pancad.utils.pancad_types import Numpy1D, SpaceVector, Space3DVector

    # A geometry type or recursively nested tuples of geometry types.
    GeometryTerm = Type[AbstractGeometry] | Iterable["GeometryTerm"]

    # In this file, 'Mixed' means an iterable consisting of types and an iterable of the types.
    # Mixed of PancadThing types and iterables of PancadThing types. Indicates applicability.
    MixedThing = Type[PancadThing] | Iterable[Type[PancadThing]]
    MixedGeo = Type[AbstractGeometry] | Iterable[Type[AbstractGeometry]]
    MixedStr = str | Iterable[str]

    # A cartesian product expression of geometry types. Used to specify GeoCombos succinctly.
    GeoComboSpec = Type[AbstractGeometry] | Iterable[MixedGeo]

    # A specification for a mapping from geometry types to an iterable of value names.
    ValueMapSpec = Mapping[MixedGeo, MixedStr]

    # A cartesian product expression of geometry combos and applicable dimensions.
    ComboDimSpec = tuple[GeoComboSpec, Iterable[int]]

    # A mapping key consisting of a calculation source, geometry combination, and dimension
    # integer. Represents a context for a calculation.
    CalcKey = tuple[Type[PancadThing], GeoCombo, int]

LINE_LIKE_TYPES = (Axis, Line)

Vector2D = NamedTuple("Vector2D", [("x", float), ("y", float)])

NamedScalar = NamedTuple("NamedScalar", [("name", str), ("scalar", float)])
"""A numerical value with a name.

:param name: The name.
:param scalar: The scalar value.
"""

LineLike = NamedTuple("LineLike", [("ref", "SpaceVector"), ("direction", "SpaceVector")])
PlaneParam = NamedTuple("PlaneParam", [("ref", "Space3DVector"), ("normal", "Space3DVector")])

class ValueSource(NamedTuple):
    """The metadata indicating where a system value originated."""
    thing: PancadThing
    name: str

class ValueCategory(NamedTuple):
    """The metadata indicating the source type and name of a value."""
    type_: Type[PancadThing]
    name: str

class SystemValue(NamedTuple, Generic[T]):
    """A value inside a pancad geometry system.

    :param source: The ValueSource for where the value is from.
    :param value: The value.
    """
    source: ValueSource
    value: T

################################################################################
# Helpers
################################################################################

def get_3_plane_points(point: Numpy1D, normal: Numpy1D) -> tuple[Numpy1D, Numpy1D, Numpy1D]:
    """Returns three non-collinear points on the same plane as a point. The first returned point
    will be the closest point on the origin, the 2nd is arbitrarily offset from the first, and the
    3rd is placed away from the first point at the cross product of the vector from the first
    point to the second point and the plane's normal vector.

    :raises ValueError: When provided a zero vector for the normal vector or when either the
        normal or point vector is 2D.
    """
    # Point closest to origin first.
    with np.errstate(divide="raise", invalid="raise"):
        try:
            closest_point = normal * np.dot(point, normal) / sum(normal**2)
        except FloatingPointError as exc:
            msg = f"Expected nonzero normal, got point: {point} and normal: {normal}"
            raise ValueError(msg) from exc
        except ValueError as exc:
            if any(len(v) != 3 for v in (point, normal)):
                exc.add_note(f"Expected 3D vectors, got: {point} and {normal}")
            raise
    vec = np.ones(3) # Offset vector
    normal_zero_indices = []
    with np.errstate(divide="raise", invalid="raise"):
        for i in range(3):
            try:
                vec[i] = -(sum(n * v for j, (n, v) in enumerate(zip(normal, vec)) if j != i)
                           / normal[i])
            except FloatingPointError as exc:
                normal_zero_indices.append(i)
                if len(normal_zero_indices) > 2:
                    raise ValueError("Normal vector cannot be zero vector") from exc
    vec = vec / np.linalg.norm(vec)
    return closest_point, closest_point + vec, closest_point + np.cross(normal, vec)

def get_plane_to_point_distance(plane_point: Numpy1D, normal: Numpy1D, point: Numpy1D) -> float:
    """Returns the distance from the plane to the point.

    :param plane_point: A point position vector on the plane.
    :param normal: The plane's normal vector.
    :param point: An arbitrary point position vector.
    :returns: The distance from the point to the plane. Negative when the point is opposite of the
        plane's normal vector.
    :raises ValueError: When the normal vector is a zero vector.
    """
    try:
        with np.errstate(divide="raise", invalid="raise"):
            unit_normal = normal / np.linalg.norm(normal) # Will error when normal vector is zero.
    except FloatingPointError as exc:
        raise ValueError("Plane's normal vector cannot be a zero vector") from exc
    # Find the vector from plane's point to the point and take the portion of it aligned with the
    # plane's normal vector.
    distance_vector = unit_normal * np.dot(unit_normal, point - plane_point)
    # Make the norm positive if it's in the direction of the normal using dot product sign.
    return float(
        np.copysign(np.linalg.norm(distance_vector), np.dot(distance_vector, unit_normal))
    )

################################################################################
# Residuals
################################################################################

def geo_product(*terms: GeometryTerm) -> list[tuple[Type[AbstractGeometry], ...]]:
    """Returns the cartesian-like-product of geometry types and tuples of types recursively."""
    while len(terms) == 1 and isinstance(terms[0], Iterable):
        terms = tuple(terms[0]) # Single nested-nested elements have to be elevated.
    tuples: list[tuple[Type[AbstractGeometry], ...]] = []
    for term in terms:
        if isinstance(term, Iterable): # Expand nested term expressions recursively.
            tuples.append(tuple(*geo_product(*term)))
        else:
            tuples.append((term,)) # Turn plain types into tuples for itertools.product
    return list(tuple(p) for p in itertools.product(*tuples))

def tuplify_keys(mapping: Mapping[T | Iterable[T], U], /) -> dict[tuple[T, ...], U]:
    """Converts all iterable and non-iterables of a generic mapping key type into tuples."""
    return {tuple(k) if isinstance(k, Iterable) else (k,): v for k, v in mapping.items()}

class SpecMap(Mapping[T, U]):
    """A mapping that just contains an internal dictionary, usually created from a smaller form of
    data."""
    def __init__(self, spec: Mapping[T, U]) -> None:
        self._map: dict[T, U] = dict(spec)

    @staticmethod
    def _tuplify(v: V | Iterable[V], /) -> tuple[V, ...]:
        # Turns mixed values into tuples and prevents strings from counting as Iterables.
        return tuple(v) if isinstance(v, Iterable) and not isinstance(v, str) else (v,)

    def __getitem__(self, key: T) -> U:
        return self._map[key]

    def __iter__(self) -> Iterator[T]:
        yield from self._map

    def __len__(self) -> int:
        return len(self._map)

class SplitKeyMap(SpecMap[T, U]):
    """A SpecMap that splits its specification keys into individual entries."""
    def __init__(self, spec: Mapping[T | Iterable[T], U]) -> None:
        mapping: dict[T, U] = {}
        for key, value in spec.items():
            for split_key in self._tuplify(key):
                mapping[split_key] = value
        super().__init__(mapping)

class MixedKeyMap(SpecMap[tuple[T, ...], U]):
    """A SpecMap that ensures its keys are only made of tuples."""
    def __init__(self, spec: Mapping[T | Iterable[T], U]) -> None:
        mapping: dict[tuple[T, ...], U] = {}
        for key, value in spec.items():
            mapping[self._tuplify(key)] = value
        super().__init__(mapping)

class MixedValueMap(SpecMap[T, tuple[U, ...]]):
    """A SpecMap that ensures its values are only made of tuples."""
    def __init__(self, spec: Mapping[T, U | Iterable[U]]) -> None:
        mapping: dict[T, tuple[U, ...]] = {}
        for key, value in spec.items():
            mapping[key] = self._tuplify(value)
        super().__init__(mapping)

class FlippedMultiMap(SpecMap[T, U]):
    """A SpecMap that splits an iterable value into keys and flips the key to the new values."""
    def __init__(self, spec: Mapping[U, Iterable[T]]) -> None:
        mapping: dict[T, U] = {}
        seen_keys: set[T] = set()
        for value, keys in spec.items():
            if duped := seen_keys.intersection(keys):
                # Duplicate keys would overwrite old values and cause unpredictable behavior.
                raise ValueError(f"Duplicated keys: {duped}")
            seen_keys.update(keys)
            mapping.update(dict.fromkeys(keys, value))
        super().__init__(mapping)

class GeoProductMap(SpecMap[GeoCombo, U]):
    """A SpecMap that creates a key for each possible geometry combination in a cartesian product
    of geometry types.
    """
    def __init__(self, spec: Mapping[GeoComboSpec, U]) -> None:
        mapping: dict[GeoCombo, U] = {}
        for combo_spec, value in spec.items():
            combos = set(frozenset(p) for p in geo_product(combo_spec))
            mapping.update(dict.fromkeys(combos, value))
        super().__init__(mapping)

class ValueMap(Mapping[Type[AbstractGeometry], U]):
    """Mapping from geometry types to anything. Also maps the cartesian product of possible
    geometry type combinations to the same thing in groups.
    """

    def __init__(self, spec: Mapping[GeoComboSpec, U]) -> None:
        self.groups = frozenset(frozenset(p) for p in geo_product(spec))
        combo_map: dict[GeoCombo, U] = {}
        # Split geometry combo spec map to every possible combo
        for combo_spec, v in spec.items():
            combos = set(frozenset(p) for p in geo_product(combo_spec))
            combo_map.update(dict.fromkeys(combos, v))
        self._map = {g: v for combo, v in combo_map.items() for g in combo}

    def __getitem__(self, key: Type[AbstractGeometry]) -> U:
        return self._map[key]

    def __iter__(self) -> Iterator[Type[AbstractGeometry]]:
        yield from self._map

    def __len__(self) -> int:
        return len(self._map)

class ComboDimMap(Mapping[tuple[Type[PancadThing], GeoCombo, int], T]):
    """Mapping from groups of PancadThing type, a geometry combo, and a dimension to anything."""

    def __init__(self,
                 specs: Mapping[tuple[Type[PancadThing], ...], dict[ComboDimSpec, T]]):
        self._map: dict[tuple[Type[PancadThing], GeoCombo, int], T]= {}
        things_to_applicability = {type_: v for types, v in specs.items() for type_ in types}
        for thing, app_specs in things_to_applicability.items():
            for (geo_combo, dim), calc in self._split_app_specs(app_specs).items():
                self._map[thing, geo_combo, dim] = calc

    @staticmethod
    def _split_app_specs(specs: Mapping[ComboDimSpec, T]
                        ) -> dict[tuple[GeoCombo, int], T]:
        """Splits a mapping of geometry combo specification tuples and dimension integer tuples
        into a mapping for each possible geometry combo and dimension.
        """
        new = {}
        for (geometry_spec, dimensions), v in specs.items():
            geometry_combos = set(frozenset(p) for p in geo_product(geometry_spec))
            new.update(dict.fromkeys(itertools.product(geometry_combos, dimensions), v))
        return new

    def __getitem__(self, key: tuple[Type[PancadThing], GeoCombo, int]
                    ) -> T:
        return self._map[key]

    def __iter__(self
                 ) -> Iterator[tuple[Type[PancadThing], GeoCombo, int]]:
        yield from self._map

    def __len__(self) -> int:
        return len(self._map)

    def __repr__(self) -> str:
        return repr(self._map)

class GeometryComboMap(Mapping[tuple[Type[PancadThing], GeoCombo, Type[AbstractGeometry]],
                               T]):
    """A mapping of constraint types and geometry combos to anything."""

    def __init__(self,
                 spec: Mapping[Iterable[Type[PancadThing]], Iterable[Mapping[GeoComboSpec, T]]]):
        group_map = {}
        for constraints, value_def_specs in spec.items():
            for value_def_spec in value_def_specs:
                value_map = ValueMap(value_def_spec)
                # Map every possible constraint and geometry combo to the value_map.
                con_geo_map = dict.fromkeys(itertools.product(constraints, value_map.groups),
                                            value_map)
                group_map.update(con_geo_map)
        # Only include the keys whose geometry are in their respective groups (g below).
        self._map = {(c, g, geo): v for (c, g), vm in group_map.items() for geo, v in vm.items()
                     if geo in g}

    def __getitem__(self, key: tuple[Type[PancadThing], GeoCombo, Type[AbstractGeometry]]
                    ) -> T:
        return self._map[key]

    def __iter__(self) -> Iterator[tuple[Type[PancadThing],
                                         GeoCombo,
                                         Type[AbstractGeometry]]]:
        yield from self._map

    def __len__(self) -> int:
        return len(self._map)

    def __repr__(self) -> str:
        return repr(self._map)

class SolverConstraint:
    """A solver-only constraint asserting that system vectors/scalars must meet a geometric
    condition.

    :param type_: The name of the constraint type.
    :param vectors: The ordered sources and initial values of the constrained system vectors.
    :param scalars: The ordered sources and initial values of the constrained system scalars.
    """

    class _CategoryValues(TypedDict):
        vectors: dict[Type[AbstractGeometry], tuple[str, ...]]
        scalars: NotRequired[dict[Type[PancadThing], tuple[str, ...]]]

    class _ConstraintSettings(TypedDict):
        combos: dict[GeoCombo, "_CategoryValues"]

    def __init__(self, type_: CEN, *,
                 vectors: Sequence[SystemValue[SpaceVector]] | None=None,
                 scalars: Sequence[SystemValue[float]] | None=None,
                 ) -> None:
        self._type = type_
        self._vectors = tuple(vectors) if vectors else tuple()
        self._scalars = tuple(scalars) if scalars else tuple()
        self._vector_method_map = {
            CEN.COINCIDENT: self._coincident,
            CEN.ZERO_DOT: self._zero_dot,
            CEN.NON_ZERO: self._non_zero,
        }

    # Constraint Addition ########################################################################
    @singledispatchmethod
    @classmethod
    def from_constraint(cls, constraint: AbstractConstraint) -> tuple[Self, ...]:
        """Produces one or more solver constraints from an AbstractConstraint."""
        raise NotImplementedError(f"Cannot produce a solver constraint from {constraint}")

    @from_constraint.register(Coincident)
    @classmethod
    def _(cls, constraint: Coincident) -> tuple[Self, ...]:
        categories: tuple[tuple[Type[AbstractGeometry], str], ...] = (
            (Point, "cartesian"),
            (Plane, "normal"),
            *tuple((t, "direction") for t in LINE_LIKE_TYPES),
            *tuple((t, "ref") for t in LINE_LIKE_TYPES + (Plane,)),
        )
        vectors = cls._add_vectors(constraint.get_geometry(),
                                   tuple(ValueCategory(*c) for c in categories))
        return (cls(CEN(constraint.type_name), vectors=tuple(vectors)),)

    @from_constraint.register(Parallel)
    @from_constraint.register(Antiparallel)
    @from_constraint.register(Codirectional)
    @classmethod
    def _(cls, constraint: Parallel | Codirectional | Antiparallel) -> tuple[Self, ...]:
        categories: tuple[tuple[Type[AbstractGeometry], str], ...] = (
            (Plane, "normal"),
            *tuple((t, "direction") for t in LINE_LIKE_TYPES),
        )
        vectors = cls._add_vectors(constraint.get_geometry(),
                                   tuple(ValueCategory(*c) for c in categories))
        return (cls(CEN(constraint.type_name), vectors=vectors),)

    @from_constraint.register(Fixed)
    @classmethod
    def _(cls, constraint: Fixed) -> tuple[Self, ...]:
        categories: tuple[tuple[Type[AbstractGeometry], str], ...] = (
            (Point, "cartesian"),
            (Plane, "normal"),
            *tuple((t, "direction") for t in LINE_LIKE_TYPES),
            *tuple((t, "ref") for t in LINE_LIKE_TYPES + (Plane,)),
        )
        vectors = cls._add_vectors(constraint.get_geometry(),
                                   tuple(ValueCategory(*c) for c in categories))
        return (cls(CEN(constraint.type_name), vectors=vectors),)

    # Geometry Addition ##########################################################################
    @singledispatchmethod
    @classmethod
    def from_geometry(cls, geometry: AbstractGeometry) -> tuple[Self, ...]:
        """Produces one or more solver constraints from an AbstractGeometry."""
        raise NotImplementedError(f"Cannot produce a solver constraint from {geometry}")

    @from_geometry.register(Point)
    @classmethod
    def _(cls, _: Point) -> tuple[Self, ...]:
        return () # Points have no internal constraints

    @from_geometry.register(Line)
    @from_geometry.register(Axis)
    @classmethod
    def _(cls, geometry: Axis | Line) -> tuple[Self, ...]:
        categories: tuple[tuple[Type[AbstractGeometry], str], ...] = (
            *tuple((t, "direction") for t in LINE_LIKE_TYPES),
            *tuple((t, "ref") for t in LINE_LIKE_TYPES),
        )
        vectors = cls._add_vectors((geometry,), tuple(ValueCategory(*c) for c in categories))
        return (
            cls(CEN.NON_ZERO, vectors=tuple(v for v in vectors if v.source.name == "direction")),
            cls(CEN.ZERO_DOT, vectors=vectors),
        )

    # Residual Calculation #######################################################################
    def calc(self, values: Collection[SystemValue[SpaceVector] | SystemValue[float]]
             ) -> tuple[NamedScalar, ...]:
        """Returns the residuals of the constraint for the given values."""
        vectors = tuple(v for v in values
                        if isinstance(v.value, tuple) and v.source in self.sources)
        scalars = tuple(v for v in values
                        if isinstance(v.value, (float, int)) and v.source in self.sources)
        if missing := self.sources - self._get_sources(vectors, scalars):
            raise ValueError(f"Missing sources: {missing}")
        if scalars:
            raise NotImplementedError("Scalars not yet supported")
        if self._type == CEN.FIXED: # Fixed constraints return an empty tuple as their residual.
            return tuple()
        with np.errstate(all="raise"): # Context used in case any of the values use numpy floats.
            return self._vector_method_map[self._type](vectors)

    def _coincident(self, vectors: Sequence[SystemValue[SpaceVector]]) -> tuple[NamedScalar, ...]:
        assert len(self.things) == 2 # Should always be the case per equation name.
        if self._thing_types == frozenset({Point}): # 2 Coincident points
            cartesians = tuple(next(v.value for v in vectors if v.source == s)
                               for s in self._value_sources())
            return tuple(NamedScalar(n, c)
                         for n, c in zip(("x", "y", "z"), self._equal_vectors(*cartesians)))
        if Point in self._thing_types: # Single Point coincident to other type.
            point = next(v.value for v in vectors if v.source == self._value_sources(Point)[0])
            if not self._thing_types.isdisjoint(LINE_LIKE_TYPES): # Point/LineLike
                linelike = LineLike(
                    next(v.value for v in vectors if v.source.name == "ref"),
                    next(v.value for v in vectors if v.source.name == "direction"),
                )
                residuals = self._point_linelike_distance_value(linelike, point, 0)
                return (NamedScalar("distance", residuals),)
        raise NotImplementedError(f"Unsupported type combo: {self._thing_types}")

    def _non_zero(self, vectors: Sequence[SystemValue[SpaceVector]]) -> tuple[NamedScalar, ...]:
        assert len(vectors) == 1 # Residual can only apply to a single vector
        return (NamedScalar("value", self._non_zero_vector_value(vectors[0].value)),)

    def _zero_dot(self, vectors: Sequence[SystemValue[SpaceVector]]) -> tuple[NamedScalar, ...]:
        values = tuple(v.value for v in vectors)
        assert len(values) == 2 # Residual can only apply to a pair of vectors
        return (NamedScalar("value", self._dot_value(*values, 0)),)

    @cached_property
    def category(self) -> frozenset[ValueCategory]:
        """The constraint's residual calculation categorization properties."""
        categories: set[ValueCategory] = set()
        for source, *_ in self.values:
            if not isinstance(type_ := type(source.thing), AbstractConstraint):
                categories.add(ValueCategory(type_, source.name))
        return frozenset(categories)

    @cached_property
    def sources(self) -> frozenset[ValueSource]:
        """Returns the *unordered* sources of all variable values for the constraint."""
        return self._get_sources(self._vectors, self._scalars)

    @cached_property
    def constants(self) -> tuple[SystemValue[float], ...]:
        """The sources and values of the constraint's constant scalars."""
        return tuple(s for s in self._scalars if isinstance(s.source.thing, AbstractConstraint))

    @property
    def scalars(self) -> tuple[SystemValue[float], ...]:
        """The constrained scalar sources and their initial values."""
        return self._scalars

    @property
    def type_(self) -> CEN:
        """The name of the constraint type."""
        return self._type

    @property
    def values(self) -> tuple[SystemValue[float] | SystemValue[SpaceVector], ...]:
        """Returns all variable sources and their initial values."""
        return self._scalars + self._vectors

    @property
    def vectors(self) -> tuple[SystemValue[SpaceVector], ...]:
        """The constrained vector sources and their initial values."""
        return self._vectors

    @cached_property
    def things(self) -> frozenset[PancadThing]:
        """The *unordered* unique things being constrained"""
        return frozenset({s.thing for s in self.sources})

    @cached_property
    def _thing_types(self) -> frozenset[Type[PancadThing]]:
        # The *unordered* types of things being constrained.
        return frozenset({c.type_ for c in self.category})

    def _value_sources(self, types: Type[PancadThing] | tuple[Type[PancadThing], ...] | None=None
                       ) -> tuple[ValueSource, ...]:
        # Return the *ordered* sources. Filters to a thing source type when provided.
        if types:
            return tuple(v.source for v in self.values if isinstance(v.source.thing, types))
        return tuple(v.source for v in self.values)

    @staticmethod
    def _get_sources(vectors: tuple[SystemValue[SpaceVector], ...],
                     scalars: tuple[SystemValue[float], ...]
                     ) -> frozenset[ValueSource]:
        # Returns the sources of the values for a given constraint input.
        return frozenset(source for group in (vectors, scalars) for source, *_ in group)

    @classmethod
    def _add_vectors(cls, geometry: Sequence[AbstractGeometry],
                     categories: Sequence[ValueCategory],
                     vectors: list[SystemValue[SpaceVector]] | None=None
                     ) -> tuple[SystemValue[SpaceVector], ...]:
        # Adds geometry vectors matching the categories to vectors. Returns a tuple of the updated
        # or new vectors.
        vectors = [] if vectors is None else vectors
        for element in geometry:
            for category in categories:
                if isinstance(element, category.type_):
                    vectors.append(SystemValue(ValueSource(element, category.name),
                                               cls._get_vector(element, category.name)))
        return tuple(vectors)

    @staticmethod
    def _get_vector(geometry: AbstractGeometry, name: str) -> SpaceVector:
        try:
            match name:
                case "direction":
                    if not isinstance(geometry, LINE_LIKE_TYPES):
                        raise TypeError
                    return geometry.direction
                case "ref":
                    if not isinstance(geometry, LINE_LIKE_TYPES + (Plane,)):
                        raise TypeError
                    return geometry.reference_point.cartesian
                case "normal":
                    if not isinstance(geometry, Plane):
                        raise TypeError
                    return geometry.normal
                case "cartesian":
                    if not isinstance(geometry, Point):
                        raise TypeError
                    return geometry.cartesian
                case _:
                    raise ValueError(f"Unsupported vector name: {name}")
        except TypeError as exc:
            raise ValueError(f"Geometry '{geometry}' has no '{name}' vector") from exc

    @classmethod
    def _codirection(cls, a: Collection[float], b: Collection[float], /) -> tuple[float, ...]:
        # Residuals for how close vector a is to pointing in the same direction as vector b.
        return cls._equal_vectors(cls._unitize(a), cls._unitize(b))

    @classmethod
    def _antiparallel(cls, a: Collection[float], b: Collection[float], /) -> tuple[float, ...]:
        # Residuals for how close vector a is to pointing in the opposite direction of vector b.
        return cls._equal_vectors(cls._unitize(a), tuple(-c for c in cls._unitize(b)))

    @classmethod
    def _parallel(cls, a: Collection[float], b: Collection[float], /) -> tuple[float, ...]:
        # Residuals for how close vector a is to pointing codirectional/antiparallel to vector b.
        sign = int(math.copysign(1, cls._normed_dot(a, b)))
        return cls._equal_vectors(cls._unitize(a), tuple(sign * c for c in cls._unitize(b)))

    @staticmethod
    def _equal_vectors(a: Collection[float], b: Collection[float], /) -> tuple[float, ...]:
        # Residual for how close vector a is to vector b.
        return tuple(c_a - c_b for c_a, c_b in zip(a, b, strict=True))

    @classmethod
    def _non_zero_vector_value(cls, vector: Collection[float], /) -> float:
        # Residual for whether a vector is too close to the zero vector.
        try:
            cls._unitize(vector)
        except ValueError:
            return 1
        return 0

    @classmethod
    def _point_linelike_distance_value(cls, line: LineLike, point: SpaceVector,
                                          value: float) -> float:
        # Residual for how close a linelike and point are to being a set distance from each other.
        return cls._point_linelike_distance(line, point) - value

    @classmethod
    def _point_linelike_coincident(cls, line: LineLike, point: SpaceVector) -> SpaceVector:
        point_to_projected = cls._sub(cls._projected_linelike_point(line, point), point)
        assert len(point_to_projected) == 2 or len(point_to_projected) == 3
        return point_to_projected

    @classmethod
    def _point_plane_distance_value(cls, plane: PlaneParam, point: SpaceVector,
                                       value: float) -> float:
        # Residual for how close a plane and point are to being a set signed distance from each
        # other.
        return cls._point_plane_distance(plane, point) - value

    @classmethod
    def _norm_value(cls, vector: Collection[float], value: float, /) -> float:
        # Residual for how close the norm of a vector is to the value.
        return cls._norm(vector) - value

    @classmethod
    def _dot_value(cls, a: Collection[float], b: Collection[float], value: float, /) -> float:
        # Residual for how close the dot product of two vectors is to the value.
        return cls._dot(a, b) - value

    @classmethod
    def _point_linelike_distance(cls, line: LineLike, point: SpaceVector) -> float:
        # Returns the magnitude of distance from a line to a point.
        try:
            direction = cls._unitize(line.direction) # unit vector of the linelike's direction.
        except ZeroDivisionError as exc:
            raise ValueError(f"Line direction is a zero vector: {line.direction}") from exc
        point_to_line_ref_vector = cls._sub(line.ref, point) # vector: p_L - p_p
        # Multiply the unit direction vector by the amount of (p_L - p_p) in linelike's direction
        projected_vector_length = cls._dot(point_to_line_ref_vector, direction)
        perpendicular_vector = cls._scalar_mul(projected_vector_length, direction)
        return cls._norm(cls._sub(point_to_line_ref_vector, perpendicular_vector))

    @classmethod
    def _point_plane_distance(cls, plane: PlaneParam, point: SpaceVector) -> float:
        # Returns the distance from a plane to a point. The distance's sign is positive in the
        # plane's normal direction.
        try:
            normal = cls._unitize(plane.normal)
        except ValueError as exc:
            raise ValueError(f"Plane normal is a zero vector: {plane.normal}") from exc
        plane_point_to_point = cls._sub(point, plane.ref) # Vector from Plane's Point to Point.
        distance_vector = cls._scalar_mul(cls._dot(normal, plane_point_to_point), normal)
        # Make the norm positive if it's in the direction of the plane's normal vector.
        return math.copysign(cls._norm(distance_vector), cls._dot(distance_vector, normal))

    @classmethod
    def _unitize(cls, vector: Collection[float]) -> tuple[float, ...]:
        # Returns a unit vector in the same direction as the vector.
        norm = cls._norm(vector)
        return tuple(c / norm for c in vector)

    @classmethod
    def _dot(cls, a: Collection[float], b: Collection[float], /) -> float:
        """Returns the dot product of two vectors.

        :raises ValueError: When the vector lengths do not match.
        """
        try:
            return sum(ca * cb for ca, cb in zip(a, b, strict=True))
        except ValueError as exc:
            if len(a) != len(b):
                raise ValueError(f"Vector lengths do not match: {a}, {b}") from exc
            raise

    @classmethod
    def _normed_dot(cls, a: Collection[float], b: Collection[float], /,
                    accept_zero: bool=False) -> float:
        """Returns the dot product of the two normalized vectors.

        :param accept_zero: Sets whether a zero vector can be provided to return 0 dot product.
        :raises ZeroDivisionError: When either vector's norm is 0.
        """
        try:
            return cls._dot(a, b) / cls._norm(a) * cls._norm(b)
        except ZeroDivisionError as exc:
            if accept_zero:
                return 0
            raise ZeroDivisionError(f"Cannot normalize: got a zero vector: {a}, {b}") from exc
        except FloatingPointError as exc: # Invalid numpy error handling.
            if "invalid value encountered in scalar divide" in str(exc) and accept_zero:
                return 0
            raise

    @staticmethod
    def _sub(a: Collection[float], b: Collection[float], /) -> tuple[float, ...]:
        # Returns the vector subtraction a - b
        return tuple(c_a - c_b for c_a, c_b in zip(a, b, strict=True))

    @staticmethod
    def _add(a: Collection[float], b: Collection[float], /) -> tuple[float, ...]:
        # Returns the vector addition a - b
        return tuple(c_a + c_b for c_a, c_b in zip(a, b, strict=True))

    @staticmethod
    def _scalar_mul(scalar: float, vector: Collection[float], /) -> tuple[float, ...]:
        # Returns a vector multiplied by a scalar.
        return tuple(scalar * c for c in vector)

    @staticmethod
    def _norm(vector: Collection[float]) -> float:
        # Returns the 2-norm of the vector.
        return math.sqrt(sum(c**2 for c in vector))

    @classmethod
    def _projected_linelike_point(cls, line: LineLike, point: SpaceVector) -> SpaceVector:
        try:
            direction = cls._unitize(line.direction) # unit vector of the linelike's direction.
        except ZeroDivisionError as exc:
            raise ValueError(f"Line direction is a zero vector: {line.direction}") from exc
        point_to_line_ref_vector = cls._sub(line.ref, point) # vector: p_L - p_p
        # Multiply the unit direction vector by the amount of (p_L - p_p) in linelike's direction
        projected_vector_length = cls._dot(point_to_line_ref_vector, direction)
        perpendicular_vector = cls._scalar_mul(projected_vector_length, direction)
        projected_point = cls._add(line.ref, perpendicular_vector)
        assert len(projected_point) == 2 or len(projected_point) == 3
        return projected_point

    def __repr__(self) -> str:
        source_things = list(dict.fromkeys(repr(v.source.thing).strip("<>") for v in self.values))
        return f"<{self.type_}:{'-'.join(source_things)}>"

_param_order_map: dict[CEN, tuple[Type[PancadThing], ...]] = {}
"""Mapping for ordering parameters by their geometry type for cases where the order matters.
Any residual function where ordering does not matter are omitted from the mapping.
"""

def unit_vector(vector: Numpy1D) -> float:
    """Calculates how far a vector is from being a unit vector."""
    return float(np.linalg.norm(vector) - 1)

def non_zero_vector(vector: Numpy1D, zero_atol: float=1e-15) -> float:
    """Produces a residual to constrain a vector to being non-zero."""
    return 1 if np.isclose(np.linalg.norm(vector), 0, atol=zero_atol) else 0

def _direction(vector_1: Numpy1D, vector_2: Numpy1D, comp: SC) -> Numpy1D:
    """Calculates how close a second vector is to pointing in the same direction (codirectional),
    opposite directions (antiparallel), or in the generically parallel direction as the first
    vector.

    :param vector_1: An n-dimensional vector.
    :param vector_2: Another n-dimensional vector.
    :param comp: Which direction constraint to calculate residuals for.
    :raises TypeError: When provided an unexpected comp(arison) value.
    """
    norm1, norm2 = map(np.linalg.norm, (vector_1, vector_2))
    dot = float(np.dot(vector_1, vector_2))
    comp_map = {SC.CODIRECTIONAL: 1, SC.ANTIPARALLEL: -1, SC.PARALLEL: int(np.copysign(1, dot))}
    try:
        sign = comp_map[comp]
    except KeyError as exc:
        msg = f"Unexpected comparison {comp}. Expected one of: {comp_map.keys()}"
        raise ValueError(msg) from exc
    if sign * dot > 0:
        try:
            with np.errstate(divide="raise", invalid="raise"):
                return vector_1 / norm1 - sign * vector_2 / norm2
        except FloatingPointError as exc:
            if not any(s in str(exc) for s in ("invalid value", "divide by zero")):
                # Ensure unexpected warnings are still raised.
                raise
    # sign * dot being less than or equal to 0 indicates the vectors are pointing in opposite
    # directions to the goal of being codirection or antiparallel. Return the difference to get
    # the solver to switch them.
    return vector_1 - sign * vector_2

codirectional: Callable[[Numpy1D, Numpy1D], Numpy1D] = partial(_direction, comp=SC.CODIRECTIONAL)
codirectional.__doc__ = """
    Calculates how close two vectors are to pointing in the same direction.

    :param vector_1: An n-dimensional vector.
    :param vector_2: Another n-dimensional vector.
""".strip()

antiparallel: Callable[[Numpy1D, Numpy1D], Numpy1D] = partial(_direction, comp=SC.ANTIPARALLEL)
antiparallel.__doc__ = """
    Calculates how close two vectors are to pointing in opposite directions.

    :param vector_1: An n-dimensional vector.
    :param vector_2: Another n-dimensional vector.
""".strip()

parallel: Callable[[Numpy1D, Numpy1D], Numpy1D] = partial(_direction, comp=SC.PARALLEL)
parallel.__doc__ = """
    Calculates how close two vectors are to pointing in the same or opposite directions.

    :param vector_1: An n-dimensional vector.
    :param vector_2: Another n-dimensional vector.
""".strip()

def equal_vector(vector_1: Numpy1D, vector_2: Numpy1D) -> Numpy1D:
    """Calculates how close a each component of a second vector is to being equal to the first
    vector's components.
    """
    return vector_1 - vector_2

def perpendicular(vector_1: Numpy1D, vector_2: Numpy1D) -> float:
    """Calculates how close the second vector is to being on the plane created by the first vector
    and the origin for the 3D case and just the dot product for the 2D case. Performing a dot
    product on the vectors squares the values.

    :param vector_1: A 2D or 3D vector.
    :param vector_2: Another 2D or 3D vector that is the same length as vector_1.
    :returns: When 3D, the signed distance from the tip of the normalized vector_2 to the virtual
        plane created by vector_1 and the origin point. When 2D, the value of the vector dot
        product divided by the two vector norms multiplied together.
    :raises ValueError: When provided a zero vector or differing length vectors.
    """
    if any(len(v) == 2 for v in (vector_1, vector_2)):
        norm_1, norm_2 = map(lambda x: float(np.linalg.norm(x)), (vector_1, vector_2))
        try:
            with np.errstate(divide="raise", invalid="raise"):
                return float(np.dot(vector_1, vector_2) / (norm_1 * norm_2))
        except FloatingPointError as exc:
            msg = f"Cannot normalize, one of the vectors a zero vector: {vector_1}, {vector_2}"
            raise ValueError(msg) from exc
        except ValueError as exc:
            if len(vector_1) != len(vector_2):
                exc.add_note(f"Expected both vectors to be 2D, got: {vector_1}, {vector_2}")
            raise
    try:
        with np.errstate(divide="raise", invalid="raise"):
            # Normalize the second vector to make perpendicularity independent of vector length.
            unit_vector_2 = vector_2 / np.linalg.norm(vector_2)
    except FloatingPointError as exc:
        msg = f"Cannot normalize vector 2, likely a zero vector: {vector_2}"
        raise ValueError(msg) from exc
    return point_plane_coincident(np.array([0,0,0], dtype=np.float64), vector_1, unit_vector_2)


def point_line_distance(line_point: Numpy1D, direction: Numpy1D,
                        point: Numpy1D, distance: float) -> float:
    """Calculates how close a point is to being a specified closest distance from a line.

    :param line_point: A point on the line.
    :param direction: A vector in the direction of the line.
    :param point: The point's position vector.
    :param distance: The distance the point should be from the line.
    """
    unit_d = direction / np.linalg.norm(direction)
    line_pt_sub_pt = line_point - point
    actual_distance = np.linalg.norm(line_pt_sub_pt - np.dot(line_pt_sub_pt, unit_d) * unit_d)
    return float(actual_distance) - distance

point_line_coincident: Callable[[Numpy1D, Numpy1D, Numpy1D],
                                float] = partial(point_line_distance, distance=0)
point_line_coincident.__doc__ = """
    Calculates how close a point is to being on a line.

    :param line_point: A point on the line.
    :param direction: A vector in the direction of the line.
    :param point: The point's position vector.
""".strip()

_param_order_map[CEN.POINT_LINE_DISTANCE] = (Axis, Line, Point)
_param_order_map[CEN.POINT_LINE_COINCIDENT] = _param_order_map[CEN.POINT_LINE_DISTANCE]

def point_plane_distance(plane_point: Numpy1D, normal: Numpy1D,
                         point: Numpy1D, distance: float) -> float:
    """Calculates how close a point is to being a specified closest distance from a plane.

    :param plane_point: A point on the plane.
    :param normal: The plane's normal vector.
    :param point: The point's position vector.
    :param distance: The distance the point should be from the plane.
    :raises ValueError: When the normal vector is a zero vector.
    """
    return get_plane_to_point_distance(plane_point, normal, point) - distance

point_plane_coincident: Callable[[Numpy1D, Numpy1D, Numpy1D],
                                 float] = partial(point_plane_distance, distance=0)
point_plane_coincident.__doc__ = """
    Calculates how close a point is to being on a plane.

    :param plane_point: The plane's closest to the origin reference point position vector.
    :param normal: The plane's normal vector.
    :param point: The point's position vector.
""".strip()

_param_order_map[CEN.POINT_PLANE_DISTANCE] = (Plane, Point)
_param_order_map[CEN.POINT_PLANE_COINCIDENT] = _param_order_map[CEN.POINT_PLANE_DISTANCE]

def plane_line_distance(plane_point: Numpy1D, normal: Numpy1D,
                        line_point: Numpy1D, direction: Numpy1D,
                        distance: float) -> float:
    """Calculates how close a line is to being a specified distance from a plane. Also works on
    axes.

    :param plane_point: A point on the plane.
    :param normal: The plane's normal vector.
    :param line_point: A point on the line.
    :param direction: A vector in the direction of the line.
    :param distance: The distance the line should be from the plane.
    :raises ValueError: When the normal vector is a zero vector.
    """
    distance_residuals = np.empty(2)
    for i, point in enumerate((line_point, line_point + direction / np.linalg.norm(direction))):
        distance_residuals[i] = point_plane_distance(plane_point, normal, point, distance)
    return float(distance_residuals[np.argmax(abs(distance_residuals))])

plane_line_coincident: Callable[[Numpy1D, Numpy1D, Numpy1D, Numpy1D],
                                float] = partial(plane_line_distance, distance=np.float64(0))
plane_line_coincident.__doc__ = """
    Calculates how close a line or axis is to being on a plane.

    :param plane_point: The plane's closest to the origin reference point position vector.
    :param normal: The plane's normal vector.
    :param line_point: A point on the line.
    :param direction: A vector in the direction of the line.
""".strip()

_param_order_map[CEN.PLANE_LINE_DISTANCE] = (Plane, Axis, Line)
_param_order_map[CEN.PLANE_LINE_COINCIDENT] = _param_order_map[CEN.PLANE_LINE_DISTANCE]

def plane_plane_distance(point_1: Numpy1D, normal_1: Numpy1D,
                         point_2: Numpy1D, normal_2: Numpy1D,
                         distance: float) -> float:
    """Calculates how close two planes are to being a specified distance from each other.

    :param point_1: A point on the first Plane.
    :param normal_1: The normal vector of the first Plane.
    :param point_2: A point on the second Plane.
    :param normal_2: The normal vector of the second Plane.
    :param distance: The required distance between the two planes. Positive in the direction of
        the first plane's normal vector.
    """
    # Enforce normal uniqueness to make the choice of plane points independent of normal direction
    unique_normal_1, unique_normal_2 = map(get_unique_vector, (normal_1, normal_2))
    distance_residuals = np.empty(3)
    for i, arbitrary_plane_1_point in enumerate(get_3_plane_points(point_1, unique_normal_1)):
        try:
            with np.errstate(divide="raise", invalid="raise"):
                projected_point = (
                    arbitrary_plane_1_point
                    + unique_normal_1
                    * np.dot(unique_normal_2, point_2 - arbitrary_plane_1_point)
                    / np.dot(unique_normal_1, unique_normal_2)
                )
        except FloatingPointError:
            # The normal vectors are perpendicular, so the effective distance is infinity.
            return np.inf
        distance_residuals[i] = point_plane_distance(point_1, normal_1, projected_point, distance)
    return float(distance_residuals[np.argmax(abs(distance_residuals))])

plane_plane_coincident: Callable[[Numpy1D, Numpy1D, Numpy1D, Numpy1D],
                                 float] = partial(plane_plane_distance, distance=0)
plane_plane_coincident.__doc__ = """
    Calculates how close two planes are to being coincident with each other.

    :param point_1: A point on the first Plane.
    :param normal_1: The normal vector of the first Plane.
    :param point_2: A point on the second Plane.
    :param normal_2: The normal vector of the second Plane.
""".strip()

def line_line_coincident(point_1: Numpy1D, direction_1: Numpy1D,
                         point_2: Numpy1D, direction_2: Numpy1D) -> Numpy1D:
    """Calculates how close two lines are to being coincident with each other."""
    offset_p = point_2 + direction_2 / np.linalg.norm(direction_2)
    return np.array(
        [point_line_coincident(point_1, direction_1, point) for point in (point_2, offset_p)]
    )


def line_ref_point(ref_pt: Numpy1D, direction: Numpy1D) -> float:
    """Calculates how close a Line or Axis' reference point is to being the closest to origin
    point. This is the same as the vectors being perpendicular except when the reference point is
    a zero vector.
    """
    try:
        return perpendicular(ref_pt, direction)
    except ValueError:
        # Should only execute when the point is a zero vector.
        return float(np.linalg.norm(ref_pt))

def unique_vector(vector: Numpy1D) -> Numpy1D:
    """Calculates how far a vector is into the non-unique set of vectors. All pancad
    non-unique vectors are opposites of a unique vector.

    :param vector: A vector that must be unique.
    :returns: A numpy array of the residuals for x and y (and z, if 3D).
    """
    return vector - get_unique_vector(vector)

def get_param_sort_key(type_: Type[PancadThing], equation_name: CEN) -> float:
    """Returns the parameter sorting key of the type for the named equation.

    :param type_: The parameter's source type.
    :param equation_name: The name of the equation to sort parameters for.
    :raises ValueError: When provided a geometry type not in the equation's ordering list.
    :returns: The index of the type in the ordering map's equation list. Returns infinity when the
        equation is not in the ordering map.
    """
    try:
        order = _param_order_map[equation_name]
    except KeyError:
        # Equation name not being in the ordering map indicates the parameters can be unordered.
        return math.inf
    try:
        return order.index(type_)
    except ValueError as exc:
        exc.add_note(f"Type {type_} is not in the {equation_name} ordering list")
        raise


RESIDUAL_FUNCS = {
    CEN.UNIT_VECTOR: unit_vector,
    CEN.EQUAL_VECTOR: equal_vector,
    CEN.LINE_REF_POINT: line_ref_point, # Line Ref Point Vector and Direction Perpendicularity
    CEN.POINT_LINE_COINCIDENT: point_line_coincident,
    CEN.POINT_PLANE_COINCIDENT: point_plane_coincident,
    CEN.LINE_LINE_COINCIDENT: line_line_coincident,
    CEN.PLANE_PLANE_COINCIDENT: plane_plane_coincident,
    CEN.PLANE_LINE_COINCIDENT: plane_line_coincident,
    CEN.PLANE_PLANE_DISTANCE: plane_plane_distance,
    CEN.CODIRECTIONAL: codirectional,
    CEN.ANTIPARALLEL: antiparallel,
    CEN.PARALLEL: parallel,
    CEN.PERPENDICULAR: perpendicular,
    CEN.UNIQUE_VECTOR: unique_vector,
    CEN.NON_ZERO: non_zero_vector,
}

class ResidualCalculation(ABC):
    """A calculation of one or more residual errors and the respective gradient vectors evaluated
    at a sequence of inputs.

    :param inputs: The ordered input values.
    :param names: The ordered input value names.
    :param no_vectors: The number of input vectors at the front of the input vector.
    :param dimension: The dimension the residual is calculated for, e.g., 1, 2, or 3.
    :param scale: The scale factor for the residual.
    """
    dimensions: tuple[int, ...] = ()
    """The dimensions this calculation can support."""

    def __init__(self,
                 inputs: Sequence[float],
                 names: Sequence[str],
                 no_vectors: int,
                 dimension: int,
                 scale: float=1):
        self._inputs: Final[tuple[float, ...]] = tuple(inputs)
        self._names: Final[tuple[str, ...]] = tuple(names)
        self._no_vectors: Final[int] = no_vectors
        self._dimension: Final[int] = dimension
        self._scale: Final[float] = scale

    @classmethod
    @abstractmethod
    def from_floats(cls, inputs: Sequence[float], scale: float=1) -> Self:
        """Creates a new calculation from the raw float values.

        :param inputs: The ordered input values.
        :param scale: The scale factor for the residual.
        :raises ValueError: When the length of inputs is not valid for the residual.
        """

    class ReadableData(TypedDict):
        """A dictionary format allowing residual inputs and outputs to be printed easily."""
        type_: type
        no_vectors: int
        dimension: int
        scale: float
        inputs: dict[str, float | tuple[float, ...]]
        residual: tuple[float, ...]
        gradient: tuple[dict[str, float | tuple[float, ...]], ...]

    @property
    @abstractmethod
    def residual(self) -> tuple[float, ...]:
        """The error of the residual functions current state(s)."""

    @property
    @abstractmethod
    def gradient(self) -> tuple[tuple[float, ...], ...]:
        """The gradient(s) of the residual function(s) in the current state."""

    def _map_names_to_vector(self, v: Sequence[float], /) -> dict[str, float | tuple[float, ...]]:
        # Maps the names of the input vector to the input/gradient vector.
        values = iter(v)
        names = iter(self._names)
        name_to_value: dict[str, float | tuple[float, ...]] = {}
        for _ in range(self._no_vectors):
            # Assumes all vectors are the same dimension.
            name_to_value[next(names)] = tuple(next(values) for __ in range(self._dimension))
        name_to_value.update(dict(zip(names, values, strict=True)))
        return name_to_value

    def to_dict(self) -> ReadableData:
        """Returns the inputs value mapped to their names for debugging."""
        return {
            "type_": type(self),
            "no_vectors": self._no_vectors,
            "dimension": self._dimension,
            "scale": self._scale,
            "inputs": self._map_names_to_vector(self._inputs),
            "residual": self.residual,
            "gradient": tuple(self._map_names_to_vector(g) for g in self.gradient),
        }

class CalculationSchema:
    """Multiple maps specified by calculation types and their applicable scenarios/values."""

    class GeometryValueNameMap(SpecMap[tuple["CalcKey", Type[AbstractGeometry]],
                                       tuple[str, ...]]):
        """Mapping from a calculation scenario and a geometry in the scenario to its names."""

        def __init__(self, spec: Mapping[Type[ResidualCalculation],
                                         Mapping[MixedThing,
                                                 Mapping[GeoComboSpec, ValueMapSpec]]]) -> None:
            mapping: dict[tuple[CalcKey, Type[AbstractGeometry]], tuple[str, ...]] = {}
            for calc, thing_spec in spec.items(): # Split MixedThings to PancadThing
                for thing, combo_spec in SplitKeyMap(thing_spec).items():
                    mapping.update(self._app_map_to_name_map(calc.dimensions, thing, combo_spec))
            super().__init__(mapping)

        def _app_map_to_name_map(self, dimensions: Iterable[int], thing: Type[PancadThing],
                                 spec: Mapping[GeoComboSpec, ValueMapSpec]
                                 ) -> Mapping[tuple[CalcKey, Type[AbstractGeometry]],
                                              tuple[str, ...]]:
            mapping: dict[tuple[CalcKey, Type[AbstractGeometry]], tuple[str, ...]] = {}
            geo_to_value: Mapping[Type[AbstractGeometry], tuple[str, ...]]
            for geo_combo, value_map_spec in GeoProductMap(spec).items():
                calc_keys = [(thing, geo_combo, dim) for dim in dimensions]
                geo_to_value = SplitKeyMap(MixedValueMap(value_map_spec))
                for geo_type, names in geo_to_value.items():
                    keys = [(key, geo_type) for key in calc_keys if geo_type in geo_combo]
                    mapping.update(dict.fromkeys(keys, names))
            return mapping

    class ContextMap(SpecMap[Type[ResidualCalculation], tuple["CalcKey", ...]]):
        """Mapping from a calculation type to its valid calculation scenarios."""

        def __init__(self, spec: Mapping[Type[ResidualCalculation],
                                         Mapping[MixedThing,
                                                 Mapping[GeoComboSpec, ValueMapSpec]]]) -> None:
            mapping: dict[Type[ResidualCalculation], tuple[CalcKey, ...]] = {}
            seen_calc_keys: set[CalcKey] = set()
            for calc, thing_spec in spec.items(): # Split MixedThings to PancadThing
                calc_keys: list[CalcKey] = []
                for thing, combo_spec in SplitKeyMap(thing_spec).items():
                    new_calc_keys = self._app_map_to_calc_keys(calc.dimensions, thing, combo_spec)
                    if duped := seen_calc_keys.intersection(new_calc_keys):
                        # Duplicate calculation scenarios would cause uncontrolled behavior by
                        # overwriting some calculations.
                        raise ValueError(f"Duplicate calculation scenarios: {duped}")
                    seen_calc_keys.update(new_calc_keys)
                    calc_keys.extend(new_calc_keys)
                mapping[calc] = tuple(calc_keys)
            super().__init__(mapping)

        def _app_map_to_calc_keys(self, dimensions: Iterable[int], thing: Type[PancadThing],
                              spec: Mapping[GeoComboSpec, ValueMapSpec]) -> tuple[CalcKey, ...]:
            # Splits a mapping of geometry combo specs into combos
            keys: list[CalcKey] = []
            for geo_combo in GeoProductMap(spec):
                keys.extend((thing, geo_combo, dim) for dim in dimensions)
            return tuple(keys)

    class OrderMap(SpecMap[tuple["CalcKey", Type[AbstractGeometry], str], int]):
        """Mapping from a calculation type to its valid calculation scenarios."""

        def __init__(self, values: CalculationSchema.GeometryValueNameMap) -> None:
            mapping: dict[tuple[CalcKey, Type[AbstractGeometry], str], int] = {}
            key_count: Counter[CalcKey] = Counter()
            for (calc_key, geometry), names in values.items():
                for name in names:
                    mapping[calc_key, geometry, name] = key_count[calc_key]
                    key_count[calc_key] += 1
            super().__init__(mapping)

    def __init__(self, spec: Mapping[Type[ResidualCalculation],
                                     Mapping[MixedThing, Mapping[GeoComboSpec, ValueMapSpec]]]):
        #: The mapping of calculation types to calculation scenario keys.
        self.contexts: Final[CalculationSchema.ContextMap] = self.ContextMap(spec)
        #: The mapping of calculation scenario key and geometry type combos to names.
        self.values: Final[CalculationSchema.GeometryValueNameMap] = (
            self.GeometryValueNameMap(spec)
        )
        #: The mapping of calculation scenario key, geometry type, and name to its integer order.
        self.order: Final[CalculationSchema.OrderMap] = self.OrderMap(self.values)
        #: The mapping of constraint calculation scenario keys to the calculation type.
        self.calcs: Final[FlippedMultiMap[CalcKey, Type[ResidualCalculation]]]  = (
            FlippedMultiMap(self.contexts)
        )

class SpecSequence(Sequence[T]):
    """A sequence that just contains an internal tuple, usually created from smaller form of
    data.
    """
    def __init__(self, values: Sequence[T]):
        self._values: Final[tuple[T, ...]] = tuple(values)

    @overload
    def __getitem__(self, index: int) -> T: ...
    @overload
    def __getitem__(self, index: slice[int | None, int | None, int | None]
                    ) -> tuple[T, ...]: ...
    def __getitem__(self, index: int | slice[int | None, int | None, int | None]
                    ) -> T | tuple[T, ...]:
        return self._values[index]

    def __len__(self) -> int:
        return len(self._values)

class GeometryValue(SpecSequence[float]):
    """A named value inside a geometry element. Scalar values are treated as single element
    tuples.
    """

    def __init__(self, geometry: AbstractGeometry, name: str):
        self.geometry: Final[AbstractGeometry] = geometry
        self.name: Final[str] = name
        super().__init__(self._read_value(geometry, name))

    def _missing_property(self) -> Never:
        raise ValueError(f"{type(self.geometry)} does not have a property named '{self.name}'")

    @singledispatchmethod
    def _read_value(self, geometry: AbstractGeometry, name: str) -> tuple[float, ...]:
        raise NotImplementedError(f"{type(geometry)} not supported")

    @_read_value.register
    def _(self, geometry: Point, name: str) -> tuple[float, ...]:
        if name != "cartesian":
            self._missing_property()
        return geometry.cartesian

    @_read_value.register
    def _(self, geometry: Line | Axis, name: str) -> tuple[float, ...]:
        match name:
            case "ref":
                return geometry.reference_point.cartesian
            case "direction":
                return geometry.direction
        self._missing_property()

def constraint_calc_key(constraint: AbstractConstraint) -> CalcKey:
    """Returns a key used to indicate the unique calculation scenario for a constraint.

    :raises ValueError: When the constraint has a mix of 2D and 3D geometry.
    """
    geometry = constraint.get_geometry()
    geo_combo = frozenset(type(geo) for geo in geometry)
    if len(set(len(geo) for geo in geometry)) != 1:
        raise ValueError("All constraint geometry must be the same dimension")
    return (type(constraint), geo_combo, len(next(iter(geometry))))

class GuessVector(SpecSequence[tuple[AbstractGeometry, str, int]]):
    """A vector that can be fed to a equation solving system. Sets the vector value order for the
    solver's input.

    :param constraints: A geometry system's constraints.
    :param schema: A schema to set what calculations are performed and the order of their
        inputs for each constraint.
    """

    def __init__(self, constraints: Iterable[AbstractConstraint], schema: CalculationSchema):
        vector = []
        fixed_geo: list[AbstractGeometry] = []
        self.constraints: Final[tuple[AbstractConstraint, ...]] = tuple(constraints)
        self.schema: Final[CalculationSchema] = schema
        seen: set[tuple[AbstractGeometry, str]] = set()
        for constraint in constraints:
            if isinstance(constraint, Fixed):
                fixed_geo.extend(constraint.get_geometry()) # Store so geometry can be removed.
                continue # Fixed constraints do not need to be included in Guesses.
            calc_key = constraint_calc_key(constraint)
            values = {g: schema.values[calc_key, type(g)] for g in constraint.get_geometry()}
            keys = [(geometry, name) for geometry, names in values.items() for name in names]
            # Sorting the keys is not needed here since the order is deterministically read from
            # first the constraint appearance and then the value name order in the schema.
            # Calculation inputs can do their own sorting.
            for geometry, name in keys:
                if (geometry, name) in seen:
                    continue # Geometry Values should never be repeated in the vector
                for i in range(len(GeometryValue(geometry, name))):
                    vector.append((geometry, name, i))
                seen.add((geometry, name))
        self.fixed_values: Final[tuple[tuple[AbstractGeometry, str, int], ...]] = tuple(
            key for f in fixed_geo for key in vector if f in key
        )
        vector = [v for v in vector if v not in self.fixed_values]
        super().__init__(vector)
        # Create a backwards mapping from the geometry, name, and index to the vector index to
        # enable external cross-referencing.
        self.sources: Final[Mapping[tuple[AbstractGeometry, str, int], int]] = {
            key: i for i, key in enumerate(tuple(self) + self.fixed_values)
        }

    @property
    def initial(self) -> tuple[float, ...]:
        """The initial variable geometry values as read from the constraints' geometry."""
        return tuple(GeometryValue(g, n)[i] for g, n, i in self)

    @property
    def fixed(self) -> tuple[float, ...]:
        """The fixed geometry values in the full guess vector."""
        return tuple(GeometryValue(g, n)[i] for g, n, i in self.fixed_values)

class CalcInput(SpecSequence[tuple[AbstractGeometry, str, int]]):
    """The ordered input sources for a constraint's calculation.

    :param constraints: A geometry system's constraints.
    :param schema: A schema to set what calculations are performed and the order of their
        inputs for each constraint.
    """

    def __init__(self, constraint: AbstractConstraint, schema: CalculationSchema):
        vector: list[tuple[AbstractGeometry, str, int]] = []
        calc_key = constraint_calc_key(constraint)
        self.calc: Final[Type[ResidualCalculation]] = schema.calcs[calc_key]
        self.constraint: Final[AbstractConstraint] = constraint
        values = {g: schema.values[calc_key, type(g)] for g in constraint.get_geometry()}
        # Construct the geometry value input keys and sort them first by the schema and second
        # by their appearance in the constraint. Sorting by the schema ensures geometric
        # calculations can be performed and sorting by constraint appearance ensures vector
        # determinism.
        keys = [(geometry, name) for geometry, names in values.items() for name in names]
        keys.sort(key=lambda key: schema.order[calc_key, type(key[0]), key[1]])
        for geometry, name in keys:
            for i in range(len(GeometryValue(geometry, name))):
                vector.append((geometry, name, i))
        super().__init__(vector)

class ResidualFactory(SpecSequence[tuple[AbstractConstraint, int]]):
    """A factory for producing geometry system residual vectors.

    :param guess: The guess vector that sets the constraints and schema.
    """

    def __init__(self, guess: GuessVector):
        self.guess: Final[GuessVector] = guess
        calc_map: dict[AbstractConstraint, CalcInput] = {}
        vector: list[tuple[AbstractConstraint, int]] = []
        for constraint in guess.constraints:
            if isinstance(constraint, Fixed):
                continue # Fixed constraints have no residual value
            calc_input = CalcInput(constraint, guess.schema)
            calc_map[constraint] = calc_input
            for i in range(len(self._eval_residual(calc_input, guess.initial + guess.fixed))):
                vector.append((constraint, i))
        self.calcs: Final[Mapping[AbstractConstraint, CalcInput]] = calc_map
        super().__init__(vector)

    @property
    def constrained(self) -> bool:
        """Whether the number of residuals meets or exceeds the number of inputs."""
        return len(self) >= len(self.guess)

    def make(self, x: Sequence[float], /) -> tuple[float, ...]:
        """Returns the values of the residuals for a given input vector."""
        with_fixed = tuple(x) + self.guess.fixed
        residuals: list[float] = []
        for constraint, calc_input in self.calcs.items():
            if isinstance(constraint, Fixed):
                continue # Fixed constraints have no residual value
            residuals.extend(self._eval_residual(calc_input, with_fixed))
        return tuple(residuals)

    def _make_input(self, calc_input: CalcInput, vector: Sequence[float]) -> tuple[float, ...]:
        return tuple(vector[self.guess.sources[key]] for key in calc_input)

    def _eval_residual(self, calc_input: CalcInput, vector: Sequence[float]) -> tuple[float, ...]:
        return calc_input.calc.from_floats(self._make_input(calc_input, vector)).residual

class EqualScalars(ResidualCalculation):
    """The residuals and gradient of a constraint holding 2 scalars equal.

    :param a: A scalar value.
    :param b: Another scalar value.
    :param scale: Solver scale factor.
    """
    dimensions = (2, 3)

    def __init__(self, a: float, b: float, /, scale: float=1):
        super().__init__((a, b), ("a", "b"), 0, 1, scale)
        self.__inputs: tuple[float, float] = (a, b)

    @classmethod
    def from_floats(cls, inputs: Sequence[float], scale: float=1) -> Self:
        try:
            a, b = inputs
        except ValueError as exc:
            raise ValueError(f"Got {len(inputs)} inputs for {cls}, expected 2.") from exc
        return cls(a, b, scale)

    @property
    def residual(self) -> tuple[float]:
        return (self._residual(*self.__inputs, self._scale),)

    @property
    def gradient(self) -> tuple[tuple[float, float]]:
        return self._gradient(self._scale)

    @staticmethod
    def _residual(a: float, b: float, /, scale: float=1) -> float:
        return scale * (b - a)

    @staticmethod
    def _gradient(scale: float=1) -> tuple[tuple[float, float]]:
        return ((-scale, scale),) # Gradient is (-1, 1)

class EqualVectorComponents2D(ResidualCalculation):
    """The residuals/gradients of a constraint holding 2 2D vectors equal, solved component-wise.

    :param v0: A 2D Vector.
    :param v1: Another 2D Vector.
    :param scale: Solver scale factor.
    """
    dimensions = (2,)

    def __init__(self, v0: tuple[float, float], v1: tuple[float, float], /, scale: float=1):
        inputs = tuple(f for v in (v0, v1) for f in v)
        super().__init__(inputs, ("v0", "v1"), 2, 2, scale)
        self.__inputs = (Vector2D(*v0), Vector2D(*v1))

    @classmethod
    def from_floats(cls, inputs: Sequence[float], scale: float=1) -> Self:
        try:
            x0, y0, x1, y1 = inputs
        except ValueError as exc:
            raise ValueError(f"Got {len(inputs)} inputs for {cls}, expected 4.") from exc
        return cls((x0, y0), (x1, y1), scale)

    @property
    def residual(self) -> tuple[float, float]:
        return self._residual(*self.__inputs, self._scale)

    @property
    def gradient(self) -> tuple[tuple[float, float, float, float],
                                tuple[float, float, float, float]]:
        return self._gradient(*self.__inputs, self._scale)

    @staticmethod
    def _residual(v0: Vector2D, v1: Vector2D, scale: float=1) -> tuple[float, float]:
        return (*EqualScalars(v0.x, v1.x, scale).residual,
                *EqualScalars(v0.y, v1.y, scale).residual)

    @staticmethod
    def _gradient(v0: Vector2D, v1: Vector2D, /,
                  scale: float=1) -> tuple[tuple[float, float, float, float],
                                           tuple[float, float, float, float]]:
        # The respective component residual inputs are independent of each other, e.g., the
        # gradients of the x residual are independent of y so they're always 0.
        dr0dx0, dr0dx1 = EqualScalars(v0.x, v1.x, scale).gradient[0]
        dr1dy0, dr1dy1 = EqualScalars(v0.x, v1.x, scale).gradient[0]
        return ((dr0dx0, 0, dr0dx1, 0), (0, dr1dy0, 0, dr1dy1))

class EqualVectors2D(ResidualCalculation):
    """The residuals and gradient of a constraint holding 2 2D vectors equal.

    :param v0: A 2D Vector.
    :param v1: Another 2D Vector.
    :param scale: Solver scale factor.
    """
    dimensions = (2,)

    def __init__(self, v0: tuple[float, float], v1: tuple[float, float], /, scale: float=1):
        inputs = tuple(f for v in (v0, v1) for f in v)
        super().__init__(inputs, ("v0", "v1"), 2, 2, scale)
        self.__inputs = (Vector2D(*v0), Vector2D(*v1))

    @classmethod
    def from_floats(cls, inputs: Sequence[float], scale: float=1) -> Self:
        try:
            x0, y0, x1, y1 = inputs
        except ValueError as exc:
            raise ValueError(f"Got {len(inputs)} inputs for {cls}, expected 4.") from exc
        return cls((x0, y0), (x1, y1), scale)

    @property
    def residual(self) -> tuple[float]:
        return (self._residual(*self.__inputs, self._scale),)

    @property
    def gradient(self) -> tuple[tuple[float, float, float, float]]:
        return self._gradient(*self.__inputs, self._scale)

    @staticmethod
    def _residual(v0: Vector2D, v1: Vector2D, /, scale: float=1) -> float:
        return scale * math.sqrt((v1.x - v0.x)**2 + (v1.y - v0.x)**2)

    @staticmethod
    def _gradient(v0: Vector2D, v1: Vector2D, /,
                  scale: float=1) -> tuple[tuple[float, float, float, float]]:
        distance = EqualVectors2D._residual(v0, v1)
        return (
            (
                scale * (v0.x - v1.x) / distance,
                scale * (v0.y - v1.y) / distance,
                scale * (v1.x - v0.x) / distance,
                scale * (v1.y - v0.y) / distance
            ),
        )

class CoincidentLinePoint2D(ResidualCalculation):
    """The residuals and gradient of a 2D Line to Point coincident constraint.

    :param p0: The point vector.
    :param p1: The first line point.
    :param p2: The second line point.
    :param scale: Solver scale factor.
    """
    dimensions = (2,)

    # TODO: Revise the calculation to calculate the second point based on the line's direction.

    def __init__(self,
                 p0: tuple[float, float],
                 p1: tuple[float, float],
                 p2: tuple[float, float], /,
                 scale: float=1):
        inputs = tuple(f for v in (p0, p1, p2) for f in v)
        super().__init__(inputs, ("p0", "p1", "p2"), 3, 2, scale)
        self.__inputs = (Vector2D(*p0), Vector2D(*p1), Vector2D(*p2))

    @classmethod
    def from_floats(cls, inputs: Sequence[float], scale: float=1) -> Self:
        try:
            x0, y0, x1, y1, x2, y2 = inputs
        except ValueError as exc:
            raise ValueError(f"Got {len(inputs)} inputs for {cls}, expected 6.") from exc
        return cls((x0, y0), (x1, y1), (x2, y2), scale)

    @property
    def residual(self) -> tuple[float]:
        return (self._residual(*self.__inputs, self._scale),)

    @property
    def gradient(self) -> tuple[tuple[float, float, float, float, float, float]]:
        return self._gradient(*self.__inputs, self._scale)

    @staticmethod
    def _residual(p0: Vector2D, p1: Vector2D, p2: Vector2D, /, scale: float=1) -> float:
        delta_y = p2.y - p1.y
        delta_x = p2.x - p1.x
        dot = -p0.x * delta_y + p0.y * delta_x + p1.x * p2.y - p2.x * p1.y
        return scale * dot / math.sqrt(delta_x**2 + delta_y**2)

    @classmethod
    def _gradient(cls, p0: Vector2D, p1: Vector2D, p2: Vector2D, /,
                  scale: float=1) -> tuple[tuple[float, float, float, float, float, float]]:
        n_s = -p0.x * (p1.y - p2.y) - p1.x * (p0.y + p2.y) + p2.x * (p0.y - p1.y)
        d_s = p2.x**2 + p2.y**2 + p1.x**2 + p1.y**2 - 2 * (p1.x * p2.x + p1.y * p2.y)
        return (
            (
                scale * (p1.y + p2.y) / math.sqrt(d_s),
                scale * (p2.x - p1.x) / math.sqrt(d_s),
                2*scale * (d_s * (p2.y - p0.y) - n_s * (p1.x - p2.x)) / d_s**(3/2),
                -scale * (d_s * (p0.x - p2.x) - n_s * (p1.x - p2.x)) / d_s**(3/2),
                scale * (d_s * (p0.y - p1.y) - n_s * (p2.x - p1.x)) / d_s**(3/2),
                scale * (d_s * (p1.x - p0.x) - n_s * (p2.y - p1.y)) / d_s**(3/2),
            ),
        )
