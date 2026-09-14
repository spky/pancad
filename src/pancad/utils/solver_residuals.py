"""A module of functions for calculating the constraint solving residuals while solving geometry
systems.
"""
from __future__ import annotations

from functools import partial, cached_property, singledispatchmethod
from typing import TYPE_CHECKING, NamedTuple, Generic, TypeVar

import math
import numpy as np

from pancad.abstract import AbstractConstraint
from pancad.constants import SketchConstraint as SC, ConstraintEquationName as CEN
from pancad.constraints.state_constraint import Coincident, Parallel, Codirectional, Antiparallel
from pancad.geometry.line import Axis, Line
from pancad.geometry.plane import Plane
from pancad.geometry.point import Point
from pancad.utils.geometry import get_unique_vector


if TYPE_CHECKING:
    from collections.abc import Callable, Collection
    from typing import Type, Self

    from pancad.abstract import PancadThing, AbstractGeometry
    from pancad.utils.pancad_types import Numpy1D, SpaceVector, Space3DVector

T = TypeVar("T")

NamedScalar = NamedTuple("NamedScalar", [("name", str), ("scalar", float)])
"""A numerical value with a name.

:param name: The name.
:param scalar: The scalar value.
"""

LineLike = NamedTuple("LineLike", [("ref", "SpaceVector"), ("direction", "SpaceVector")])
PlaneParam = NamedTuple("PlaneParam",
                        [("ref", "Space3DVector"), ("normal", "Space3DVector")])

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

class SolverConstraint:
    """A solver-only constraint asserting that system vectors/scalars must meet a geometric
    condition.

    :param type_: The name of the constraint type.
    :param vectors: The source and initial values of the constrained system vectors.
    :param scalars: The source and initial values of the constrained system scalars.
    """

    def __init__(self, type_: CEN, *,
                 vectors: tuple[SystemValue[SpaceVector], ...] | None=None,
                 scalars: tuple[SystemValue[float], ...] | None=None,
                 ) -> None:
        self._type = type_
        self._vectors = vectors if vectors else tuple()
        self._scalars = scalars if scalars else tuple()
        self._vector_method_map = {CEN.COINCIDENT: self._coincident,}

    @singledispatchmethod
    @classmethod
    def from_constraint(cls, constraint: AbstractConstraint) -> tuple[Self, ...]:
        """Produces one or more solver constraints from an AbstractConstraint."""
        raise NotImplementedError(f"Cannot produce a solver constraint from {constraint}")

    @from_constraint.register(Coincident)
    @classmethod
    def _(cls, constraint: Coincident) -> tuple[Self, ...]:
        vectors: list[SystemValue[SpaceVector]] = []
        geometry = constraint.get_geometry()
        types = {type(g) for g in geometry}
        cls._add_point_vector(vectors, geometry, types)
        cls._add_line_like_vectors(vectors, geometry, types, ("direction", "ref"))
        cls._add_plane_vectors(vectors, geometry, types, ("normal", "ref"))
        if types:
            raise NotImplementedError(f"Unsupported geometry type(s): {types}")
        return (cls(CEN(constraint.type_name), vectors=tuple(vectors)),)

    @from_constraint.register(Parallel)
    @from_constraint.register(Antiparallel)
    @from_constraint.register(Codirectional)
    @classmethod
    def _(cls, constraint: Parallel | Codirectional | Antiparallel) -> tuple[Self, ...]:
        vectors: list[SystemValue[SpaceVector]] = []
        geometry = constraint.get_geometry()
        types = {type(g) for g in geometry}
        cls._add_line_like_vectors(vectors, geometry, types, "direction")
        cls._add_plane_vectors(vectors, geometry, types, "normal")
        if types:
            raise NotImplementedError(f"Unsupported geometry type(s): {types}")
        return (cls(CEN(constraint.type_name), vectors=tuple(vectors)),)

    def calc(self, *,
             vectors: tuple[SystemValue[SpaceVector], ...] | None=None,
             scalars: tuple[SystemValue[float], ...] | None=None
             ) -> tuple[NamedScalar, ...]:
        """Returns the residuals of the constraint for the given values."""
        vectors = vectors if vectors else tuple()
        scalars = scalars if scalars else tuple()
        if self.sources != self._get_sources(vectors, scalars):
            msg = f"Expected {self.sources} sources, got: {self._get_sources(vectors, scalars)}"
            raise ValueError(msg)
        if scalars:
            raise NotImplementedError("Scalars not yet supported")
        return self._vector_method_map[self._type](vectors)

    def _coincident(self, vectors: tuple[SystemValue[SpaceVector], ...]
                    ) -> tuple[NamedScalar, ...]:
        types = {c.type_ for c in self.category}
        linelike_types = (Line, Axis)
        if types == {Point}: # 2 Coincident points
            cartesians = tuple(v.value for v in vectors)
            return tuple(NamedScalar(n, c)
                         for n, c in zip(("x", "y", "z"), self._equal_vectors(*cartesians)))
        if Point in types: # Single Point coincident to other type.
            point = next(v.value for v in vectors if isinstance(v.source.thing, Point))
            if any(ll in types for ll in linelike_types): # Point/LineLike
                linelike = LineLike(
                    next(v.value for v in vectors if v.source.name == "ref"),
                    next(v.value for v in vectors if v.source.name == "direction"),
                )
                return (NamedScalar("distance",
                                    self._point_to_linelike_distance_value(linelike, point, 0)),)
        raise NotImplementedError(f"Unsupported type combo: {types}")

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
        """Returns the sources of all variable values for the constraint."""
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

    @staticmethod
    def _get_sources(vectors: tuple[SystemValue[SpaceVector], ...],
                     scalars: tuple[SystemValue[float], ...]
                     ) -> frozenset[ValueSource]:
        # Returns the sources of the values for a given constraint input.
        return frozenset(source for group in (vectors, scalars) for source, *_ in group)

    @staticmethod
    def _add_point_vector(vectors: list[SystemValue[SpaceVector]],
                          geometry: Collection[AbstractGeometry],
                          types: set[Type[AbstractGeometry]]) -> None:
        # Adds point vectors in the geometry to the vectors list and removes Point from types
        for element in geometry:
            if not isinstance(element, Point):
                continue
            vectors.append(SystemValue(ValueSource(element, "cartesian"), element.cartesian))
        types.discard(Point)

    @staticmethod
    def _add_line_like_vectors(vectors: list[SystemValue[SpaceVector]],
                               geometry: Collection[AbstractGeometry],
                               types: set[Type[AbstractGeometry]],
                               names: Collection[str] | str) -> None:
        # Adds line-like vectors in geometry to the vectors list and removes line-likes from types
        names = (names,) if isinstance(names, str) else names
        linelike_types = (Axis, Line)
        if "direction" in names:
            vectors.extend(SystemValue(ValueSource(g, "direction"), g.direction)
                           for g in geometry if isinstance(g, linelike_types))
        if "ref" in names:
            vectors.extend(SystemValue(ValueSource(g, "ref"), g.reference_point.cartesian)
                           for g in geometry if isinstance(g, linelike_types))
        for type_ in linelike_types:
            types.discard(type_)

    @staticmethod
    def _add_plane_vectors(vectors: list[SystemValue[SpaceVector]],
                           geometry: Collection[AbstractGeometry],
                           types: set[Type[AbstractGeometry]],
                           names: Collection[str] | str) -> None:
        # Adds plane vectors in geometry to the vectors list and removes line-likes from types
        names = (names,) if isinstance(names, str) else names
        if "normal" in names:
            vectors.extend(SystemValue(ValueSource(g, "normal"), g.normal)
                           for g in geometry if isinstance(g, Plane))
        if "ref" in names:
            vectors.extend(SystemValue(ValueSource(g, "ref"), g.reference_point.cartesian)
                           for g in geometry if isinstance(g, Plane))
        types.discard(Plane)

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
        sign = int(math.copysign(1, cls._dot(a, b)))
        return cls._equal_vectors(cls._unitize(a), tuple(sign * c for c in cls._unitize(b)))

    @staticmethod
    def _equal_vectors(a: Collection[float], b: Collection[float], /) -> tuple[float, ...]:
        # Residual for how close vector a is to vector b.
        return tuple(c_a - c_b for c_a, c_b in zip(a, b, strict=True))

    @classmethod
    def _point_to_linelike_distance_value(cls, line: LineLike, point: SpaceVector,
                                          value: float) -> float:
        # Residual for how close a linelike and point are to being a set distance from each other.
        return cls._point_to_linelike_distance(line, point) - value

    @classmethod
    def _norm_value(cls, vector: Collection[float], value: float, /) -> float:
        # Residual for how close the norm of a vector is to the value.
        return cls._norm(vector) - value

    @classmethod
    def _dot_value(cls, a: Collection[float], b: Collection[float], value: float, /) -> float:
        # Residual for how close the dot product of two vectors is to the value.
        return cls._dot(a, b) - value

    @classmethod
    def _point_to_linelike_distance(cls, line: LineLike, point: SpaceVector) -> float:
        # Returns the magniture of distance from a line to a point.
        try:
            direction = cls._unitize(line.direction) # unit vector of the linelike's direction.
        except ZeroDivisionError as exc:
            raise ValueError(f"Line direction is a zero vector: {line.direction}") from exc
        point_to_line_ref = cls._sub(line.ref, point) # vector: p_L - p_p
        # Multiply the unit direction vector by the amount of (p_L - p_p) in linelike's direction
        try:
            dotted_direction = cls._scalar_mul(cls._dot(point_to_line_ref, direction), direction)
        except ZeroDivisionError:
            # Can only occur when the point is already on the line's ref since the direction has
            # already been turned into a unit vector.
            return 0
        return cls._norm(cls._sub(point_to_line_ref, dotted_direction))

    @classmethod
    def _unitize(cls, vector: Collection[float]) -> tuple[float, ...]:
        # Returns a unit vector in the same direction as the vector.
        norm = cls._norm(vector)
        return tuple(c / norm for c in vector)

    @classmethod
    def _dot(cls, a: Collection[float], b: Collection[float], /,
             accept_zero: bool=False) -> float:
        """Returns the dot product of two vectors.

        :param accept_zero: Sets whether a zero vector can be provided to return 0.
        :raises ZeroDivisionError: When either vector's norm is 0.
        :raises ValueError: When the vector lengths do not match.
        """
        try:
            return sum(ca * cb for ca, cb in zip(a, b, strict=True)) / cls._norm(a) * cls._norm(b)
        except ZeroDivisionError as exc:
            if accept_zero:
                return 0
            raise ZeroDivisionError(f"Cannot normalize: got a zero vector: {a}, {b}") from exc
        except ValueError as exc:
            if len(a) != len(b):
                raise ValueError(f"Vector lengths do not match: {a}, {b}") from exc
            raise

    @staticmethod
    def _sub(a: Collection[float], b: Collection[float], /) -> tuple[float, ...]:
        # Returns the vector subtraction a - b
        return tuple(c_a - c_b for c_a, c_b in zip(a, b, strict=True))

    @staticmethod
    def _scalar_mul(scalar: float, vector: Collection[float], /) -> tuple[float, ...]:
        # Returns a vector multiplied by a scalar.
        return tuple(scalar * c for c in vector)

    @staticmethod
    def _norm(vector: Collection[float]) -> float:
        # Returns the 2-norm of the vector.
        return math.sqrt(sum(c**2 for c in vector))

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
