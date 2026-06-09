"""A module of functions for calculating the constraint solving residuals while solving geometry
systems.
"""
from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

import math
import numpy as np

from pancad.constants import SketchConstraint as SC, ConstraintEquationName as CEN

from pancad.geometry.line import Axis, Line
from pancad.geometry.plane import Plane
from pancad.geometry.point import Point

if TYPE_CHECKING:
    from typing import Literal, Type

    import numpy.typing as npt

    from pancad.abstract import PancadThing


################################################################################
# Helpers
################################################################################

def get_3_plane_points(point: npt.NDArray, normal: npt.NDArray
                       ) -> tuple[npt.NDArray, npt.NDArray, npt.NDArray]:
    """Returns three non-collinear points on the same plane as a point. The first returned point
    will be the closest point on the origin, the 2nd is arbitrarily offset from the first, and the
    3rd is placed away from the first point at the cross product of the vector from the first
    point to the second point and the plane's normal vector.

    :raises ValueError: When provided a zero vector for the normal vector or when either the
        normal or point vector is 2D.
    """
    points = []
    # Point closest to origin first.
    with np.errstate(divide="raise", invalid="raise"):
        try:
            points.append(normal * np.dot(point, normal) / sum(normal**2))
        except FloatingPointError as exc:
            msg = f"Expected nonzero normal, got point: {point} and normal: {normal}"
            raise ValueError(msg) from exc
        except ValueError as exc:
            if any(len(v) != 3 for v in (point, normal)):
                exc.add_note(f"Expected 3D vectors, got: {point} and {normal}")
            raise
    vec = np.ones(3)
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
    points.extend([points[0] + vec, points[0] + np.cross(normal, vec)])
    return points

def get_plane_to_point_distance(plane_point: npt.NDArray, normal: npt.NDArray,
                                point: npt.NDArray) -> np.float64:
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
    return np.copysign(np.linalg.norm(distance_vector), np.dot(distance_vector, unit_normal))

def get_unique_vector(vector: npt.NDArray) -> npt.NDArray:
    """Checks the vector against unique direction rules and inverts it if any are violated.

    Example of the algorithm using 3D vectors:
    1. The z component must be nonnegative.
    2. If z is exactly 0 or the vector is 2D, y must be nonnegative.
    3. If both y and z are exactly 0 or the vector is 2D, x must be nonnegative.
    4. Zero vectors are considered already unique and returned as is.

    :param vector: An n-dimensional vector.
    """
    for component in vector[::-1]:
        if component < 0:
            return -vector
        if component > 0:
            return vector
    return vector



################################################################################
# Residuals
################################################################################

_param_order_map = {}
"""Mapping for ordering parameters by their geometry type for cases where the order matters.
Any residual function where ordering does matter are omitted from the mapping.
"""

def unit_vector(vector: npt.NDArray) -> np.float64:
    """Calculates how far a vector is from being a unit vector."""
    return np.linalg.norm(vector) - 1

def non_zero_vector(vector: npt.NDArray, zero_atol: np.float64=np.float64(1e-15)) -> np.float64:
    """Produces a residual to constrain a vector to being non-zero."""
    if np.isclose(np.linalg.norm(vector), 0, atol=zero_atol):
        return np.float64(1)
    return np.float64(0)

def _direction(v1: npt.NDArray, v2: npt.NDArray,
               comp: Literal[SC.CODIRECTIONAL, SC.ANTIPARALLEL, SC.PARALLEL]) -> npt.NDArray:
    """Calculates how close a second vector is to pointing in the same direction (codirectional),
    opposite directions (antiparallel), or in the generically parallel direction as the first
    vector.

    :param v1: An n-dimensional vector.
    :param v2: Another n-dimensional vector.
    :param comp: Which direction constraint to calculate residuals for.
    :raises TypeError: When provided an unexpected comp(arison) value.
    """
    norm1, norm2 = map(np.linalg.norm, (v1, v2))
    dot = np.dot(v1, v2)
    comp_signs = {SC.CODIRECTIONAL: 1, SC.ANTIPARALLEL: -1, SC.PARALLEL: np.copysign(1, dot)}
    try:
        # Get the sign for the respective comparison difference equation.
        sign = comp_signs[comp]
    except KeyError as exc:
        msg = (f"Unexpected comparison {comp}."
               f" Expected {SC.CODIRECTIONAL}, {SC.ANTIPARALLEL}, or {SC.PARALLEL}")
        raise TypeError(msg) from exc
    if sign * dot > 0:
        try:
            with np.errstate(divide="raise", invalid="raise"):
                return v1 / norm1 - sign * v2 / norm2
        except FloatingPointError as exc:
            if not any(s in str(exc) for s in ("invalid value", "divide by zero")):
                # Ensure unexpected warnings are still raised.
                raise
    # sign * dot being less than or equal to 0 indicates the vectors are pointing in opposite
    # directions to the goal of being codirection or antiparallel. Return the difference to get
    # the solver to switch them.
    return v1 - sign * v2

codirectional = partial(_direction, comp=SC.CODIRECTIONAL)
codirectional.__doc__ = """
    Calculates how close two vectors are to pointing in the same direction.

    :param v1: An n-dimensional vector.
    :param v2: Another n-dimensional vector.
""".strip()

antiparallel = partial(_direction, comp=SC.ANTIPARALLEL)
antiparallel.__doc__ = """
    Calculates how close two vectors are to pointing in opposite directions.

    :param v1: An n-dimensional vector.
    :param v2: Another n-dimensional vector.
""".strip()

parallel = partial(_direction, comp=SC.PARALLEL)
parallel.__doc__ = """
    Calculates how close two vectors are to pointing in the same or opposite directions.

    :param v1: An n-dimensional vector.
    :param v2: Another n-dimensional vector.
""".strip()

def equal_vector(v1: npt.NDArray, v2: npt.NDArray) -> npt.NDArray:
    """Calculates how close a each component of a second vector is to being equal to the first
    vector's components.
    """
    return v1 - v2

def perpendicular(v1: npt.NDArray, v2: npt.NDArray) -> np.float64:
    """Calculates how close two vectors are to being perpendicular to each other."""
    n1, n2 = map(np.linalg.norm, (v1, v2))
    try:
        with np.errstate(divide="raise", invalid="raise"):
            # Normalize to reduce round-off by making sure vectors are the same magnitude.
            # nv1, nv2 = map(lambda v: v / np.linalg.norm(v), (v1, v2))
            return np.dot(v1, v2) / (n1 * n2)
    except FloatingPointError as exc:
        msg = f"Cannot normalize, one of the vectors is likely a zero vector: {v1}, {v2}"
        raise ValueError(msg) from exc

def point_line_distance(line_pt: npt.NDArray, direction: npt.NDArray,
                        pt: npt.NDArray, distance: np.float64) -> np.float64:
    """Calculates how close a point is to being a specified closest distance from a line.

    :param line_pt: A point on the line.
    :param direction: A vector in the direction of the line.
    :param pt: The point's position vector.
    :param distance: The distance the point should be from the line.
    """
    unit_d = direction / np.linalg.norm(direction)
    line_pt_sub_pt = line_pt - pt
    return np.linalg.norm(line_pt_sub_pt - np.dot(line_pt_sub_pt, unit_d) * unit_d) - distance

point_line_coincident = partial(point_line_distance, distance=np.float64(0))
point_line_coincident.__doc__ = """
    Calculates how close a point is to being on a line.

    :param line_pt: A point on the line.
    :param direction: A vector in the direction of the line.
    :param pt: The point's position vector.
""".strip()

_param_order_map[CEN.POINT_LINE_DISTANCE] = (Axis, Line, Point)
_param_order_map[CEN.POINT_LINE_COINCIDENT] = _param_order_map[CEN.POINT_LINE_DISTANCE]

def point_plane_distance(plane_point: npt.NDArray, normal: npt.NDArray,
                         point: npt.NDArray, distance: np.float64) -> np.float64:
    """Calculates how close a point is to being a specified closest distance from a plane.

    :param plane_point: A point on the plane.
    :param normal: The plane's normal vector.
    :param point: The point's position vector.
    :param distance: The distance the point should be from the plane.
    :raises ValueError: When the normal vector is a zero vector.
    """
    return get_plane_to_point_distance(plane_point, normal, point) - distance

point_plane_coincident = partial(point_plane_distance, distance=np.float64(0))
point_plane_coincident.__doc__ = """
    Calculates how close a point is to being on a plane.

    :param pln_pt: The plane's closest to the origin reference point position vector.
    :param normal: The plane's normal vector.
    :param pt: The point's position vector.
""".strip()

_param_order_map[CEN.POINT_PLANE_DISTANCE] = (Plane, Point)
_param_order_map[CEN.POINT_PLANE_COINCIDENT] = _param_order_map[CEN.POINT_PLANE_DISTANCE]

def plane_line_distance(plane_point: npt.NDArray, normal: npt.NDArray,
                        line_point: npt.NDArray, direction: npt.NDArray,
                        distance: np.float64) -> np.float64:
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
    return distance_residuals[np.argmax(abs(distance_residuals))]

plane_line_coincident = partial(plane_line_distance, distance=np.float64(0))
plane_line_coincident.__doc__ = """
    Calculates how close a line or axis is to being on a plane.

    :param pln_pt: The plane's closest to the origin reference point position vector.
    :param normal: The plane's normal vector.
    :param pt: The point's position vector.
""".strip()

_param_order_map[CEN.PLANE_LINE_DISTANCE] = (Plane, Axis, Line)
_param_order_map[CEN.PLANE_LINE_DISTANCE] = _param_order_map[CEN.PLANE_LINE_DISTANCE]

def plane_plane_distance(point_1: npt.NDArray, normal_1: npt.NDArray,
                         point_2: npt.NDArray, normal_2: npt.NDArray,
                         distance: np.float64) -> np.float64:
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
    return distance_residuals[np.argmax(abs(distance_residuals))]

plane_plane_coincident = partial(plane_plane_distance, distance=np.float64(0))
plane_plane_coincident.__doc__ = """
    Calculates how close two planes are to being coincident with each other.

    :param p1: A point on the first Plane.
    :param n1: The normal vector of the first Plane.
    :param p2: A point on the second Plane.
    :param n2: The normal vector of the second Plane.
""".strip()

def line_line_coincident(p1: npt.NDArray, d1: npt.NDArray,
                         p2: npt.NDArray, d2: npt.NDArray) -> npt.NDArray:
    """Calculates how close two lines are to being coincident with each other."""
    offset_p = p2 + d2 / np.linalg.norm(d2)
    return np.array([point_line_coincident(p1, d1, point) for point in (p2, offset_p)])


def line_ref_point(ref_pt: npt.NDArray, direction: npt.NDArray) -> np.float64:
    """Calculates how close a Line or Axis' reference point is to being the closest to origin
    point. This is the same as the vectors being perpendicular except when the reference point is
    a zero vector.
    """
    try:
        return perpendicular(ref_pt, direction)
    except ValueError:
        # Should only execute when the point is a zero vector.
        return np.linalg.norm(ref_pt)

def unique_vector(vector: npt.NDArray, zero_atol: np.float64=np.float64(1e-16)) -> npt.NDArray:
    """Calculates how far a vector is into the non-unique set of vectors. All pancad
    non-unique vectors are opposites of a unique vector.

    Unique pancad vectors must meet these conditions:

    1. If 3D, the z component must be nonnegative.
    2. If 2D or z is 0, the y component must be nonnegative.
    3. If both y and z is 0, the x component must be nonnegative.

    :param vector: A vector that must be unique.
    :param zero_atol: The absolute tolerance to use when checking whether components are 0.
    :returns: A numpy array of the residuals for z (if 3D), y, and x.
    """
    residuals = []
    if len(vector) == 3:
        x, y, z = vector
        # If z is the negative zero_atol, this function should treat z as 0 and move to 2D case.
        # If z is positive zero_atol, this function should treat z as 0 and move to 2D case.
        # If z is less than negative zero_atol, this function should return the z residual and 0.
        # If z is a nonzero positive number, this function should return np.array([0, 0]).
        residuals.append(z - abs(z))
        if abs(residuals[0]) >= 0 and not np.isclose(z, 0, atol=zero_atol):
            # z is either positive or is a negative number that is not close to 0.
            # Should return z residual and 0.
            residuals.extend([0, 0])
            return np.array(residuals)
        # Z must be zero at this point, so the 3D problem reduces to 2D.
    else:
        x, y = vector
    # Direction is 2D or z is 0.
    if np.isclose(y, 0, atol=zero_atol):
        # Y is close to 0, so return x residual.
        residuals.extend([y - abs(y), x - abs(x)])
    else:
        # Y is not close to 0, so return y residual.
        residuals.extend([y - abs(y), 0])
    return np.array(residuals)

def get_param_sort_key(type_: Type[PancadThing],
                   equation_name: CEN) -> float:
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
    CEN.UNIQUE_VECTOR: unique_vector,
    CEN.NON_ZERO: non_zero_vector,
}
