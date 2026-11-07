"""A module of functions for calculating the constraint solving residuals while solving geometry
systems.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Iterable, Sequence
from functools import cached_property, singledispatchmethod
import itertools
from typing import TYPE_CHECKING, NamedTuple, Type, TypeVar, overload

import numpy as np
import scipy

from pancad.abstract import (
    AbstractConstraint, AbstractGeometry, AbstractGeometrySystem, PancadThing
)
from pancad.constraints.snapto import Fixed
from pancad.geometry.line import Axis, Line
from pancad.geometry.point import Point
from pancad.utils.solver_schemas import SCHEMAS

if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import NotRequired, Final, Never, Literal

    from pancad.utils.pancad_types import Numpy1D, SpaceVector, Space3DVector
    from pancad.utils.residual_calculations import ResidualCalculation
    from pancad.utils.solver_schemas import MixedThing, GeoComboSpec, ValueMapSpec

    T = TypeVar("T")
    U = TypeVar("U")
    V = TypeVar("V")

    # An unordered list of distinct geometry types. Indicates applicability.
    GeoCombo = frozenset[Type[AbstractGeometry]]
    # A geometry type or recursively nested tuples of geometry types.
    GeometryTerm = Type[AbstractGeometry] | Iterable["GeometryTerm"]

    # A cartesian product expression of geometry combos and applicable dimensions.
    ComboDimSpec = tuple[GeoComboSpec, Iterable[int]]

    # A mapping key consisting of a calculation source, geometry combination, and dimension
    # integer. Represents a context for a calculation.
    CalcKey = tuple[Type[PancadThing], GeoCombo, int]

    ScipyMethod = Literal[
        'lm',
        'hybr',
        'broyden1',
        'broyden2',
        'anderson',
        'linearmixing',
        'diagbroyden',
        'excitingmixing',
        'krylov'
    ]

class GeometryData(NamedTuple):
    """The vectors and values defining geometry."""
    vectors: dict[str, SpaceVector]
    scalars: dict[str, float]

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

class SpecMap(Mapping["T", "U"]):
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

class SplitKeyMap(SpecMap["T", "U"]):
    """A SpecMap that splits its specification keys into individual entries."""
    def __init__(self, spec: Mapping[T | Iterable[T], U]) -> None:
        mapping: dict[T, U] = {}
        for key, value in spec.items():
            for split_key in self._tuplify(key):
                mapping[split_key] = value
        super().__init__(mapping)

class MixedKeyMap(SpecMap[tuple["T", ...], "U"]):
    """A SpecMap that ensures its keys are only made of tuples."""
    def __init__(self, spec: Mapping[T | Iterable[T], U]) -> None:
        mapping: dict[tuple[T, ...], U] = {}
        for key, value in spec.items():
            mapping[self._tuplify(key)] = value
        super().__init__(mapping)

class MixedValueMap(SpecMap["T", tuple["U", ...]]):
    """A SpecMap that ensures its values are only made of tuples."""
    def __init__(self, spec: Mapping[T, U | Iterable[U]]) -> None:
        mapping: dict[T, tuple[U, ...]] = {}
        for key, value in spec.items():
            mapping[key] = self._tuplify(value)
        super().__init__(mapping)

class FlippedMultiMap(SpecMap["T", "U"]):
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

class GeoProductMap(SpecMap["GeoCombo", "U"]):
    """A SpecMap that creates a key for each possible geometry combination in a cartesian product
    of geometry types.
    """
    def __init__(self, spec: Mapping[GeoComboSpec, U]) -> None:
        mapping: dict[GeoCombo, U] = {}
        for combo_spec, value in spec.items():
            combos = set(frozenset(p) for p in geo_product(combo_spec))
            mapping.update(dict.fromkeys(combos, value))
        super().__init__(mapping)

class ValueMap(Mapping[Type[AbstractGeometry], "U"]):
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

class ComboDimMap(Mapping[tuple[Type[PancadThing], "GeoCombo", int], "T"]):
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

class GeometryComboMap(Mapping[tuple[Type[PancadThing], "GeoCombo", Type[AbstractGeometry]],
                               "T"]):
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

    class ContextMap(SpecMap[Type["ResidualCalculation"], tuple["CalcKey", ...]]):
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
        self._spec = spec

    @cached_property
    def contexts(self) -> CalculationSchema.ContextMap:
        """The mapping of calculation types to calculation scenario keys."""
        return self.ContextMap(self._spec)

    @cached_property
    def values(self) -> CalculationSchema.GeometryValueNameMap:
        """The mapping of calculation scenario key and geometry type combos to names."""
        return self.GeometryValueNameMap(self._spec)

    @cached_property
    def order(self) -> CalculationSchema.OrderMap:
        """The mapping of calculation scenario key, geometry type, and name to its int order."""
        return self.OrderMap(self.values)

    @cached_property
    def calcs(self) -> FlippedMultiMap[CalcKey, Type[ResidualCalculation]]:
        """The mapping of constraint calculation scenario keys to the calculation type."""
        return FlippedMultiMap(self.contexts)

class SpecSequence(Sequence["T"]):
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
        self.constraints: Final[tuple[AbstractConstraint, ...]] = tuple(constraints)
        self.schema: Final[CalculationSchema] = schema
        # Initialize fixed geometry with the always fixed geometry in the system.
        fixed_geo: list[AbstractGeometry] = self._fixed_sys_geo(self.constraints)
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

    @staticmethod
    def _system(constraints: Iterable[AbstractConstraint]) -> AbstractGeometrySystem:
        # Returns the geometry system containing the constraints.
        if not constraints:
            raise ValueError("No constraints were provided")
        if len(systems := {c.system for c in constraints}) != 1:
            raise ValueError("Got constraints from multiple systems")
        if system := next(iter(systems)):
            return system
        raise ValueError("Constraints must be in a system to be solved.")

    @staticmethod
    def _fixed_sys_geo(constraints: Iterable[AbstractConstraint]) -> list[AbstractGeometry]:
        # Returns the default fixed coordinate system geometry from the constraints' system.
        system = GuessVector._system(constraints)
        return list(set(system.coordinate_system.children.values()))

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
        self.inputs: Final[Mapping[tuple[AbstractGeometry, str, int],
                                   int]] = {key: i for i, key in enumerate(self)}

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
        self.residuals: Final[Mapping[tuple[AbstractConstraint, int],
                              int]] = {key: i for i, key in enumerate(self)}

    @property
    def constrained(self) -> bool:
        """Whether the number of residuals meets or exceeds the number of inputs."""
        return len(self) >= len(self.guess)

    @cached_property
    def jacobian(self) -> tuple[tuple[tuple[AbstractConstraint, int, int], ...], ...]:
        """The definition matrix of the residual jacobian matrix that indicates which constraint,
        result index, and gradient index each matrix element came from.
        """
        matrix = []
        for constraint, calc_result_index in self:
            row: list[tuple[AbstractConstraint, int, int]] = []
            calc_input = self.calcs[constraint]
            for value_key in self.guess:
                gradient_index = calc_input.inputs.get(value_key, 0) # Values not in gradient = 0
                row.append((constraint, calc_result_index, gradient_index))
            matrix.append(tuple(row))
        return tuple(matrix)

    def make_jac(self, x: Sequence[float] | np.ndarray[tuple[int], np.dtype[np.float64]], /
                 ) -> tuple[tuple[float, ...], ...]:
        """Creates the jacobian matrix corresponding to the system's result at the input."""
        calcs = self._make_calcs(x)
        matrix = []
        for row_definition in self.jacobian:
            row: list[float] = []
            for constraint, result_index, grad_index in row_definition:
                residual_index = self.residuals[constraint, result_index]
                row.append(calcs[residual_index].gradient[result_index][grad_index])
            matrix.append(tuple(row))
        return tuple(matrix)

    def __call__(self, x: Sequence[float] | np.ndarray[tuple[int], np.dtype[np.float64]], /
                 ) -> tuple[float, ...]:
        residuals: list[float] = []
        for (_, residual_index), calc in zip(self, self._make_calcs(x), strict=True):
            residuals.append(calc.residual[residual_index])
        return tuple(residuals)

    def _make_input(self, calc_input: CalcInput, vector: Sequence[float]) -> tuple[float, ...]:
        return tuple(vector[self.guess.sources[key]] for key in calc_input)

    def _make_calcs(self, x: Sequence[float] | np.ndarray[tuple[int], np.dtype[np.float64]]
                    ) -> tuple[ResidualCalculation, ...]:
        # Sets up all the ResidualCalculations for an input vector without evaluating them.
        with_fixed = tuple(x) + self.guess.fixed
        calcs: dict[AbstractConstraint, ResidualCalculation] = {}
        for constraint, input_ in self.calcs.items():
            calcs[constraint] = input_.calc.from_floats(self._make_input(input_, with_fixed))
        return tuple(calcs[constraint] for constraint, _ in self)

    def _eval_residual(self, calc_input: CalcInput, vector: Sequence[float]) -> tuple[float, ...]:
        return calc_input.calc.from_floats(self._make_input(calc_input, vector)).residual


class SystemSolution(SpecSequence[float]):
    """The solution to a geometry system with constraints."""

    _schemas = SCHEMAS

    _methods: Mapping[str, Literal["lm", "hybr"]] = {"lm": "lm", "hybr": "hybr"}

    def __init__(self,
                 system: AbstractGeometrySystem,
                 method: str="lm",
                 schema: str="pancad_default"):
        self.system: Final[AbstractGeometrySystem] = system
        self.updates: list[GeometryUpdate] = [] # Will only be filled after calling update()
        try:
            schema_spec = self._schemas[schema]
        except KeyError as err:
            msg = f"Invalid schema '{schema}'. Must be one of: {tuple(self._schemas)}"
            raise ValueError(msg) from err
        try:
            self.method: Final[ScipyMethod] = self._methods[method]
        except KeyError as err:
            msg = f"Invalid method '{method}'. Must be one of: {tuple(self._methods)}"
            raise ValueError(msg) from err
        guess = GuessVector(self.system.constraints, CalculationSchema(schema_spec))
        self.factory: Final[ResidualFactory] = ResidualFactory(guess)
        self.solution = scipy.optimize.root(fun=self.factory.__call__,
                                            x0=np.array(self.factory.guess.initial),
                                            jac=self.factory.make_jac,
                                            method=self.method)
        super().__init__(tuple(i.item() for i in self.solution.x)) # Breakout array into floats

    def to_dict(self) -> dict[tuple[AbstractGeometry, str, int], float]:
        """Returns dictionary mapping the source to each value in the solution vector."""
        return dict(zip(self.factory.guess, self, strict=True))

    def update(self) -> None:
        """Update the geometry system using the solution's values."""
        for geometry in {g for g, *_ in self.factory.guess}:
            self.updates.append(GeometryUpdate(geometry, self))

class GeometryUpdate:
    """An update to a geometry element after a system has been solved."""

    def __init__(self, geometry: AbstractGeometry, solution: SystemSolution):
        self.geometry: Final[AbstractGeometry] = geometry
        self.solution: Final[SystemSolution] = solution
        self._initial = self.solution.factory.guess.initial # Save the initial vector beforehand.
        self._post = tuple(self.solution) # Save the new vector in case there are future updates.
        self._update(geometry, self.new)

    @cached_property
    def old(self) -> GeometryData:
        """The geometry's values before the update."""
        return self._group(self._initial)

    @cached_property
    def new(self) -> GeometryData:
        """The geometry's values after the update."""
        return self._group(self._post)

    def _group(self, vector: Sequence[float]) -> GeometryData:
        components: dict[str, list[float]] = {}
        for value_index, (guess_geo, name, _) in enumerate(self.solution.factory.guess):
            # The guess already has the value indicies sorted, so it is not sorted here.
            if guess_geo == self.geometry:
                components.setdefault(name, []).append(vector[value_index])
        vectors: dict[str, SpaceVector] = {}
        scalars: dict[str, float] = {}
        for name, values in components.items():
            candidate = tuple(values)
            if len(candidate) == 1:
                scalars[name] = candidate[0]
            elif len(candidate) == 2 or len(candidate) == 3:
                vectors[name] = candidate
            else:
                raise ValueError(f"Expected values 1 to 3 long, got: {candidate}")
        return GeometryData(vectors, scalars)

    @singledispatchmethod
    def _update(self, geo: AbstractGeometry, new: GeometryData) -> None:
        raise NotImplementedError(f"Cannot update {geo} geometry types yet.")

    @_update.register
    def _(self, geo: Point, new: GeometryData) -> None:
        cartesian = new.vectors["cartesian"]
        if len(cartesian) != len(geo):
            raise ValueError("Point update vector dimension mismatch.")
        geo.cartesian = cartesian
