"""A module providing secondary solving functions that perform operations on
pancad geometry. pancad geometry must not directly depend on these since doing
they would be cyclically dependent.
"""
from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING
import textwrap
from itertools import repeat
from functools import singledispatch, singledispatchmethod, partial
import warnings

import numpy as np
from scipy.optimize import root as find_root

from pancad.abstract import AbstractGeometry
from pancad.constants import (
    ConstraintVariableName as CVN, ConstraintEquationName as CEN, SketchConstraint as SC
)

from pancad.constraints.state_constraint import Coincident, Codirectional, Antiparallel, Parallel
from pancad.constraints.distance import Distance
from pancad.constraints.snapto import Fixed, Unique
from pancad.geometry.line_segment import LineSegment
from pancad.geometry.line import Axis, Line
from pancad.geometry.plane import Plane
from pancad.geometry.point import Point
from pancad.utils.pancad_types import FitBox2D
from pancad.utils.text_formatting import get_table_string

if TYPE_CHECKING:
    from collections.abc import Callable
    from numbers import Real
    from typing import Literal, Type, Optional
    from uuid import UUID

    import numpy.typing as npt

    from pancad.abstract import AbstractGeometrySystem, AbstractConstraint, PancadThing
    from pancad.utils.pancad_types import SpaceVector

    GeoCombo = frozenset[Type[AbstractGeometry]]

def get_length(segment: LineSegment,
               along: Literal["x", "y", "z"]=None) -> float:
    """Returns the length of the line segment, defined as the distance between
    the start and end points.

    :param segment: A LineSegment object.
    :param along: The cartesian direction to measure the length along. When
        None, the total length from start to end is returned.
    :raises TypeError: When provided an incorrect along value.
    """
    if along is None:
        start_to_end = np.array(segment.end) - np.array(segment.start)
        return np.linalg.norm(start_to_end)
    lengths = {"x": abs(segment.start.x - segment.end.x),
               "y": abs(segment.start.y - segment.end.y)}
    if len(segment) == 3:
        lengths["z"] = abs(segment.start.z - segment.end.z)
    try:
        return lengths[along]
    except KeyError as exc:
        expected = ["x", "y"]
        if len(segment) == 3:
            expected.append("z")
        msg = (f"Incorrect along. Expected one of {expected}"
               f" for a {len(segment)}D LineSegment. Got: {along}")
        raise TypeError(msg) from exc

def set_length(segment: LineSegment,
               value: Real,
               from_: Literal["start", "end"],
               along: Literal["x", "y", "z"]=None) -> LineSegment:
    """Sets the length of the line segment.

    .. note:: Cases similar to setting the y direction of a line segment
        initially parallel to the x axis assigns the correct length, but the
        direction the point moves in is dependent on both the from point and the
        segment's initial direction. This may be confusing and cause unexpected
        behavior, so it is recommended to confirm the positioning of such lines
        afterwards.

    :param segment: A LineSegment object.
    :param value: The new length of the line.
    :param from_: The LineSegment point to keep constant.
    :param along: The cartesian direction to measure the length along. When
        None, the total length is set in the segment's existing direction.
    :raises ValueError: When trying to set a LineSegment's length to 0.
    :raises TypeError: When provided an incorrect value for from_ or along.
    """
    if value == 0:
        raise ValueError("Length cannot be set to 0")

    pt_map = {"start": segment.start, "end":segment.end}
    try:
        from_pt = pt_map.pop(from_)
    except KeyError as exc:
        msg = f"Unexpected from_. Must be one of {list(pt_map)}. Got: {from_}"
        raise TypeError(msg) from exc
    _, move_pt = pt_map.popitem()

    if from_ == "start":
        vector_sign = 1
    else: # Always end as long as there are only 2 options
        vector_sign = -1

    if along is None:
        # Update in the same direction as the existing line segment.
        new_vector = np.array(segment.direction) * value
    else:
        along_map = {"x": 0, "y": 1}
        dim = len(segment)
        if dim == 3:
            along_map["z"] = 2
        try:
            axis = along_map[along]
        except KeyError as exc:
            msg = ("Unexpected along. Expected None or one"
                   f" of {list(along_map)} for a {dim}D LineSegment. Got: {along}")
            raise TypeError(msg) from exc
        new_vector = np.array(segment.end) - np.array(segment.start)
        new_vector[axis] = value * np.copysign(1, segment.direction[axis])
    move_pt.cartesian = from_pt.cartesian + vector_sign * new_vector
    return segment

@singledispatch
def get_fit_box(geometry: AbstractGeometry) -> FitBox2D:
    """Returns the minimum (bottom-left) and maximum (top-right) corner points
    of the smallest axis-aligned 2D box that fits over the geometry.

    :raises NotImplementedError: When provided AbstractGeometry that cannot have
        its FitBox solved for yet, or when provided 3D geometry.
    :raises TypeError: When provided a non-AbstractGeometry element.
    """
    if isinstance(geometry, AbstractGeometry):
        msg = f"Cannot get the fit box of {geometry.__class__} geometries yet."
        raise NotImplementedError(msg)
    raise TypeError(f"Expected a subclass of AbstractGeometry, got: {geometry}")

@get_fit_box.register
def _line_segment(geometry: LineSegment) -> FitBox2D:
    if len(geometry) != 2:
        msg = f"Fit boxes of 3D geometry are not supported. Got: {geometry}"
        raise NotImplementedError(msg)
    min_coords = (min(geometry.start.x, geometry.end.x),
                  min(geometry.start.y, geometry.end.y))
    max_coords = (max(geometry.start.x, geometry.end.x),
                  max(geometry.start.y, geometry.end.y))
    return FitBox2D(min_coords, max_coords)

def _norm_with_zero(vector: npt.NDArray | SpaceVector) -> npt.NDArray:
    """Normalizes a vector if its magnitude is not zero or returns it as is if it is zero."""
    if np.isclose(norm := np.linalg.norm(vector), 0):
        return np.array(vector)
    return np.array(vector) / norm

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
# Residual Calculators
################################################################################

def residual_unit_vector(vector: npt.NDArray) -> np.float64:
    """Calculates how far a vector is from being a unit vector."""
    return np.linalg.norm(vector) - 1

def residual_non_zero_vector(vector: npt.NDArray,
                             zero_atol: np.float64=np.float64(1e-15)) -> np.float64:
    """Produces a residual to constrain a vector to being non-zero."""
    if np.isclose(np.linalg.norm(vector), 0, atol=zero_atol):
        return 1
    return 0

def _residual_direction(v1: npt.NDArray, v2: npt.NDArray,
                        comp: Literal[SC.CODIRECTIONAL, SC.ANTIPARALLEL, SC.PARALLEL],
                        ) -> npt.NDArray:
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
        with warnings.catch_warnings():
            # numpy will raise a warning from division by zero (inf) or zero divided by zero (NaN)
            # Normalization cannot occur, so it's treated as an error rather than a warning.
            warnings.filterwarnings("error")
            try:
                return v1 / norm1 - sign * v2 / norm2
            except RuntimeWarning as warn:
                if not any(s in str(warn) for s in ("invalid value", "divide by zero")):
                    # Ensure unexpected warnings are still raised.
                    raise
    # sign * dot being less than or equal to 0 indicates the vectors are pointing in opposite
    # directions to the goal of being codirection or antiparallel. Return the difference to get
    # the solver to switch them.
    return v1 - sign * v2

residual_codirectional = partial(_residual_direction, comp=SC.CODIRECTIONAL)
residual_codirectional.__doc__ = """
    Calculates how close two vectors are to pointing in the same direction.

    :param v1: An n-dimensional vector.
    :param v2: Another n-dimensional vector.
""".strip()

residual_antiparallel = partial(_residual_direction, comp=SC.ANTIPARALLEL)
residual_antiparallel.__doc__ = """
    Calculates how close two vectors are to pointing in opposite directions.

    :param v1: An n-dimensional vector.
    :param v2: Another n-dimensional vector.
""".strip()

residual_parallel = partial(_residual_direction, comp=SC.PARALLEL)
residual_parallel.__doc__ = """
    Calculates how close two vectors are to pointing in the same or opposite directions.

    :param v1: An n-dimensional vector.
    :param v2: Another n-dimensional vector.
""".strip()

def residual_equal_vector(v1: npt.NDArray, v2: npt.NDArray) -> npt.NDArray:
    """Calculates how close a each component of a second vector is to being equal to the first
    vector's components.
    """
    return v1 - v2

def residual_perpendicular(v1: npt.NDArray, v2: npt.NDArray,
                           zero_atol: np.float64=np.float64(1e-16)) -> np.float64:
    """Calculates how close two vectors are to being perpendicular to each other."""
    norm1, norm2 = map(np.linalg.norm, (v1, v2))
    if any(np.isclose(n, 0, atol=zero_atol) for n in (norm1, norm2)):
        raise ValueError("Cannot check whether a zero vector is perpendicular")
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

def residual_point_line_distance(line_pt: npt.NDArray, direction: npt.NDArray,
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

residual_point_line_coincident = partial(residual_point_line_distance, distance=np.float64(0))
residual_point_line_coincident.__doc__ = """
    Calculates how close a point is to being on a line.

    :param ref_pt: The line's closest to the origin reference point position vector.
    :param direction: The line's direction vector.
    :param pt: The point's position vector.
""".strip()

def residual_point_plane_distance(pln_pt: npt.NDArray, normal: npt.NDArray,
                                  pt: npt.NDArray, distance: np.float64) -> np.float64:
    """Calculates how close a point is to being a specified closest distance from a plane.

    :param pln_pt: A point on the plane.
    :param normal: The plane's normal vector.
    :param pt: The point's position vector.
    :param distance: The distance the point should be from the plane.
    """
    return abs(np.dot(normal, pln_pt - pt) / np.linalg.norm(normal) - distance)

residual_point_plane_coincident = partial(residual_point_plane_distance, distance=np.float64(0))
residual_point_plane_coincident.__doc__ = """
    Calculates how close a point is to being on a plane.

    :param pln_pt: The plane's closest to the origin reference point position vector.
    :param normal: The plane's normal vector.
    :param pt: The point's position vector.
""".strip()

def residual_plane_plane_distance(p1: npt.NDArray, n1: npt.NDArray,
                                  p2: npt.NDArray, n2: npt.NDArray,
                                  distance: np.float64) -> np.float64:
    """Calculates how close two planes are to being a specified distance from each other.

    :param p1: A point on the first Plane.
    :param n1: The normal vector of the first Plane.
    :param p2: A point on the second Plane.
    :param n2: The normal vector of the second Plane.
    :param distance: The required distance between the two planes. Positive in the direction of
        the first plane's normal vector.
    """
    distances = []
    # Enforce normal uniqueness since distance is independent of normal vector direction
    un1, un2 = map(get_unique_vector, (n1, n2))
    distances = np.empty(3)
    for i, pt in enumerate(get_3_plane_points(p1, un1)):
        try:
            with np.errstate(divide="raise", invalid="raise"):
                proj_pt = pt + un1 * np.dot(un2, p2 - pt) / np.dot(un1, un2)
        except FloatingPointError:
            # The normal vectors are perpendicular, so the effective distance is infinity.
            return np.inf
        pt_to_proj = proj_pt - pt
        distances[i] = np.copysign(np.linalg.norm(pt_to_proj), np.dot(un1, pt_to_proj))
    return distances[np.argmax(abs(distances))] - distance

residual_plane_plane_coincident = partial(residual_plane_plane_distance, distance=np.float64(0))
residual_plane_plane_coincident.__doc__ = """
    Calculates how close two planes are to being coincident with each other.

    :param p1: A point on the first Plane.
    :param n1: The normal vector of the first Plane.
    :param p2: A point on the second Plane.
    :param n2: The normal vector of the second Plane.
""".strip()

def residual_line_line_coincident(p1: npt.NDArray, d1: npt.NDArray,
                                  p2: npt.NDArray, d2: npt.NDArray) -> npt.NDArray:
    """Calculates how close two lines are to being coincident with each other."""
    offset_p = p2 + d2 / np.linalg.norm(d2)
    return np.array([residual_point_line_coincident(p1, d1, point) for point in (p2, offset_p)])


def residual_line_ref_point(ref_pt: npt.NDArray, direction: npt.NDArray) -> np.float64:
    """Calculates how close a Line or Axis' reference point is to being the closest to origin
    point. This is the same as the vectors being perpendicular except when the reference point is
    a zero vector.
    """
    try:
        return residual_perpendicular(ref_pt, direction)
    except ValueError:
        # Should only execute when the point is a zero vector.
        return np.linalg.norm(ref_pt)

def residual_unique_vector(vector: npt.NDArray,
                           zero_atol: np.float64=np.float64(1e-16)) -> npt.NDArray:
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

RESIDUAL_FUNCS = {
    CEN.UNIT_VECTOR: residual_unit_vector,
    CEN.EQUAL_VECTOR: residual_equal_vector,
    CEN.LINE_REF_POINT: residual_line_ref_point,
    # Line Reference Point Vector and Direction Perpendicularity
    CEN.POINT_LINE_COINCIDENT: residual_point_line_coincident,
    CEN.POINT_PLANE_COINCIDENT: residual_point_plane_coincident,
    CEN.LINE_LINE_COINCIDENT: residual_line_line_coincident,
    CEN.PLANE_PLANE_COINCIDENT: residual_plane_plane_coincident,
    CEN.PLANE_PLANE_DISTANCE: residual_plane_plane_distance,
    CEN.FIXED_VECTOR: residual_equal_vector,
    # First vector must be held constant to a supplied initial vector
    CEN.CODIRECTIONAL: residual_codirectional,
    CEN.ANTIPARALLEL: residual_antiparallel,
    CEN.PARALLEL: residual_parallel,
    CEN.UNIQUE_VECTOR: residual_unique_vector,
    CEN.NON_ZERO: residual_non_zero_vector,
}

class ConstraintVariable:
    """A class for tracking variables used by constraint functions.

    :param element: The geometry or constraint source for the variable.
    :param name: The ConstraintVariableName that defines what part of the source
        element the variable is referring to.
    :param initial: The initial value of the variable.
    :param fixed: Whether the variable is a fixed value inside the system.
    """

    def __init__(self,
                 element: AbstractGeometry | AbstractConstraint,
                 name: CVN,
                 initial: npt.NDArray,
                 solver: SystemSolver):
        self.element = element
        self.name = name
        self.initial = initial
        self.fixed = False
        self._solver = solver
        self.value = np.copy(initial) # Initialize value

    @property
    def source(self) -> str | UUID:
        """The unique id of the source element."""
        return self.element.uid

    @property
    def value(self) -> npt.NDArray:
        """The variable's current value.

        :raises ValueError: When a new value's length does not match the current value length.
        :raises RuntimeError: When attempting to update a fixed variable value.
        """
        return self._value

    @value.setter
    def value(self, new_value: npt.NDArray):
        if self.fixed:
            raise RuntimeError("Cannot update variable value, variable is fixed")
        if len(new_value) != len(self):
            raise ValueError(f"Expected {len(self)} long vector, got: {new_value}")
        self._value = new_value

    def __len__(self) -> int:
        return len(self.initial)

@dataclasses.dataclass
class ConstraintEquation:
    """A dataclass for tracking imposed and internal constraint equation function
    names and parameter names.

    :param element: The geometry or constraint requiring the equation.
    :param name: The constraint equation name enumeration value.
    :param params: A list of constraint variables to reference during calculations.
    :param constants: A mapping of variable names to constant values used in each calculation.
        Ex: A Distance constraint may have its value set in here.
    """
    element: AbstractGeometry | AbstractConstraint
    name: CEN
    params: list[ConstraintVariable] = dataclasses.field(repr=False)
    constants: dict[str, np.float64] = dataclasses.field(default_factory=dict)

    @property
    def source(self) -> str | UUID:
        """The unique id of the source element."""
        return self.element.uid

    def calc(self) -> npt.NDArray:
        """Calculates the equation's residual based on the current parameter values."""
        param_values = []
        for p in self.params:
            if len(p) == 1:
                param_values.append(p.value[0])
            else:
                param_values.append(p.value)
        if self.name == CEN.FIXED_VECTOR:
            for p in self.params:
                if len(p) == 1:
                    param_values.append(p.initial[0])
                else:
                    param_values.append(p.initial)
        result = RESIDUAL_FUNCS[self.name](*param_values, **self.constants)
        if isinstance(result, np.ndarray):
            return result
        return np.array([result])

class SystemSolver:
    """A class that solves a geometry system's internal and imposed constraints
    and updates its geometry to meet them.
    """

    absolute_tol = np.finfo(np.float64).eps
    """The absolute tolerance to pass the solver by default. Scipy defaults to
    1.49012e-8 (2^-26), which is the square root of the numpy.float64 eps.
    """

    def __init__(self, system: AbstractGeometrySystem) -> None:
        self._system = system
        self._equations = []
        self._variables = []
        self.run_data = []
        for c in self._system.constraints:
            for geo in c.get_parents():
                # Make sure the geometry variables/constraints have been added
                if not any(v.source == geo.uid for v in self._variables):
                    self._add_geometry_variables(geo)
                    self._add_geometry_funcs(geo)
            self._add_constraint(c)

    @property
    def x(self) -> npt.NDArray:
        """The current non-fixed system variable values.

        :raises ValueError: When a new x vector is not the same length as the old one.
        """
        x = []
        for var in self._variables:
            if var.fixed:
                continue
            x.extend(var.value)
        return np.array(x)

    @x.setter
    def x(self, new_x: npt.NDArray):
        if len(new_x) != len(self.x):
            raise ValueError(f"Expected {len(self.x)} long vector, got: {new_x}")
        start = 0
        for var in self._variables:
            if var.fixed:
                continue
            end = start + len(var)
            var.value = new_x[start:end]
            start = end

    def fun(self, x: npt.NDArray) -> npt.NDArray:
        """Returns the residuals of the system for a given non-fixed vector value and updates
        the current x vector.
        """
        self.x = x
        try:
            result = np.concatenate([f.calc() for f in self._equations])
        except ValueError:
            if self.x.size == 0:
                return np.array([])
            raise
        return result

    def solve(self, method: str="lm",
              fun_wrap: Callable[[Callable[[npt.NDArray], npt.NDArray]],
                                 Callable[[npt.NDArray], npt.NDArray]]=None,
              **kwargs) -> npt.NDArray:
        """Returns the roots of the system's functions as a 1D numpy array.

        :param method: The type of solver that should be used. Defaults to
            Levenberg-Marquardt (lm). See scipy.optimize.root for other options.
        :param fun_wrap: A wrapper function to wrap around each residual function call. Must
            take the input vector x and output the residual function value vector.
        """
        if "tol" not in kwargs:
            kwargs["tol"] = self.absolute_tol
        if "options" not in kwargs:
            kwargs["options"] = {"ftol": np.finfo(np.float64).eps,}
        func = self.fun
        if fun_wrap is not None:
            func = fun_wrap(func)
        x0 = self.get_initial()
        solution = find_root(func, x0, method=method, **kwargs)
        return solution

    def get_initial(self, include_fixed: bool=False) -> npt.NDArray:
        """Returns the initial input vector to feed to the non-linear solver.

        :param include_fixed: Whether to include the values of the fixed system variables.
        """
        x0 = []
        for var in self._variables:
            if var.fixed and not include_fixed:
                continue
            x0.extend(var.initial)
        return np.array(x0)

    def get_var_slice(self, var: ConstraintVariable) -> tuple[int, int]:
        """Returns the start and end indicies of a variable in the x input vector."""
        start = 0
        for system_var in self._variables:
            if system_var.fixed:
                continue
            end = start + len(system_var)
            if system_var == var:
                return start, end
            start = end
        raise LookupError(f"Could not find variable {var} in system's variables")

    def get_eq_slice(self, eq: ConstraintEquation) -> tuple[int, int]:
        """Returns the start and end indicies of a equation in the fun output vector."""
        start = 0
        for system_eq in self._equations:
            end = start + len(system_eq.calc())
            if system_eq == eq:
                return start, end
            start = end
        raise LookupError(f"Could not find equation {eq} in system's equations")

    def get_variables(self, include_fixed: bool=False) -> list[ConstraintVariable]:
        """Returns the system's variables.

        :param include_fixed: Whether to include the fixed system variables.
        """
        if include_fixed:
            return self._variables
        return [v for v in self._variables if not v.fixed]

    def get_equations(self) -> list[ConstraintEquation]:
        """Returns the system's equations."""
        return self._equations

    def update(self, new_x: npt.NDArray) -> None:
        """Updates all the elements in the system to a new vector value."""
        updaters = {
            CVN.DIRECTION: _update_direction,
            CVN.LOCATION: _update_location,
            CVN.REF_POINT: _update_ref_point,
            CVN.NORMAL: _update_normal,
        }
        for v in self._variables:
            if v.fixed:
                continue
            start, end = self.get_var_slice(v)
            new_value = new_x[start:end]
            updaters[v.name](v.element, new_value)

    def label_x(self, x: npt.NDArray) -> str:
        """Returns a string table with each vector variable value labeled and indexed.

        :raises ValueError: When the x vector is not the same length as the current x.
        """
        if len(x) != len(self.x):
            raise ValueError(f"Expected {len(self.x)} long vector, got: {x}")
        column_map = {
            "#": "#",
            "Value": "value",
            "Name": "name",
            "Element": "element",
            "Source": "source",
        }
        data = []
        start = 0
        i = 0
        for var in self._variables:
            if var.fixed:
                continue
            end = start + len(var)
            x_var_values = x[start:end]
            for i, value in enumerate(x_var_values, start):
                data.append(
                    {
                        "#": i,
                        "value": value,
                        "name": var.name,
                        "element": var.element,
                        "source": var.source,
                    }
                )
            start = i + 1
        return get_table_string(data, column_map)

    def label_fun(self, results: npt.NDArray) -> str:
        """Returns a string table with each vector variable value labeled and
        indexed assuming the vector is in the same order as the equation function
        output.
        """
        column_map = {
            "#": "#",
            "Sub #": "sub",
            "Value": "value",
            "Name": "name",
            "Element": "element",
            "Source": "source"
        }
        data = []
        start = 0
        i = 0
        for f in self._equations:
            try:
                end = start + len(f.calc())
            except TypeError:
                end = start + 1
            for i, value in enumerate(results[slice(start, end)], start):
                data.append(
                    {
                        "#": i,
                        "sub": i - start,
                        "value": value,
                        "name": f.name,
                        "element": f.element,
                        "source": f.source,
                    }
                )
            start = i + 1
        return get_table_string(data, column_map)

    def _get_var(self, source: AbstractGeometry | AbstractConstraint, name: CVN
                 ) -> ConstraintVariable:
        """Returns the ConstraintVariable for a given source and variable name.

        :raises LookupError: When the source or variable could not be found.
        """
        source_vars = [v for v in self._variables if v.source == source.uid]
        try:
            return next(v for v in source_vars if v.name == name)
        except StopIteration as exc:
            if not source_vars:
                msg = ("Could not find any variables for source"
                       f" {source} while looking for {name}")
                raise LookupError(msg) from exc
            msg = f"Could not find a {name} variable for {source}"
            raise LookupError(msg) from exc

    @singledispatchmethod
    def _add_constraint(self, constraint: AbstractConstraint) -> None:
        """Adds a constraint to the residuals list.

        :raises NotImplementedError: When the constraint type or combination of
            constrained geometry types is not supported.
        """
        msg = f"Solving the constraint type of {constraint} has not yet been implemented"
        raise NotImplementedError(msg)

    @_add_constraint.register
    def _codirectional(self, constraint: Codirectional) -> None:
        var_map = {Axis: [CVN.DIRECTION], Plane: [CVN.NORMAL]}
        func = partial(self._new_constraint_eq, eq=CEN.CODIRECTIONAL, var_map=var_map)
        self._add_equation(constraint, {frozenset({c}): func for c in var_map})

    @_add_constraint.register
    def _antiparallel(self, constraint: Antiparallel) -> None:
        var_map = {Axis: [CVN.DIRECTION], Plane: [CVN.NORMAL]}
        func = partial(self._new_constraint_eq, eq=CEN.ANTIPARALLEL, var_map=var_map)
        self._add_equation(constraint, {frozenset({c}): func for c in var_map})

    @_add_constraint.register
    def _parallel(self, constraint: Parallel) -> None:
        var_map = {Axis: [CVN.DIRECTION], Plane: [CVN.NORMAL]}
        func = partial(self._new_constraint_eq, eq=CEN.PARALLEL, var_map=var_map)
        self._add_equation(constraint, {frozenset({c}): func for c in var_map})

    @_add_constraint.register
    def _unique(self, constraint: Unique) -> None:
        var_map = {Axis: [CVN.DIRECTION], Plane: [CVN.NORMAL]}
        func = partial(self._new_constraint_eq, eq=CEN.UNIQUE_VECTOR, var_map=var_map)
        self._add_equation(constraint, {frozenset({c}): func for c in var_map})

    @_add_constraint.register
    def _distance(self, constraint: Distance) -> None:
        var_map = {Plane: [CVN.REF_POINT, CVN.NORMAL]}
        combos = [
            ({Plane}, CEN.PLANE_PLANE_DISTANCE),
        ]
        # Add distance equation.
        eq_map = {frozenset(c): partial(self._new_constraint_eq, eq=e, var_map=var_map,
                                        constants={"distance": constraint.value})
                  for c, e in combos}
        self._add_equation(constraint, eq_map)
        if {type(g) for g in constraint.get_geometry()} == {Plane}:
            # Special Case: Planes must be parallel to have a meaningful distance between them.
            func = partial(self._new_constraint_eq,
                           eq=CEN.PARALLEL, var_map={Plane: [CVN.NORMAL]})
            self._add_equation(constraint, {frozenset({Plane}): func})

    @_add_constraint.register
    def _coincident(self, constraint: Coincident) -> None:
        var_map = {
            Axis: [CVN.REF_POINT, CVN.DIRECTION],
            Line: [CVN.REF_POINT, CVN.DIRECTION],
            Plane: [CVN.REF_POINT, CVN.NORMAL],
            Point: [CVN.LOCATION],
        }
        combos = [
            ({Axis, Point}, CEN.POINT_LINE_COINCIDENT),
            ({Line, Point}, CEN.POINT_LINE_COINCIDENT),
            ({Plane, Point}, CEN.POINT_PLANE_COINCIDENT),
            ({Axis}, CEN.LINE_LINE_COINCIDENT),
        ]
        eq_map = {frozenset(c): partial(self._new_constraint_eq, eq=e, var_map=var_map)
                  for c, e in combos}
        self._add_equation(constraint, eq_map)

    @_add_constraint.register
    def _fixed(self, constraint: Fixed) -> None:
        geo = constraint.get_geometry()[0] # Fixed must have only one geometry element
        vector_name_map = {
            Point: [CVN.LOCATION],
            Axis: [CVN.REF_POINT, CVN.DIRECTION],
            Plane: [CVN.REF_POINT, CVN.NORMAL],
        }
        try:
            vector_names = vector_name_map[type(geo)]
        except KeyError as exc:
            msg = f"Fixed relation for {geo} is not supported and/or may be invalid"
            raise NotImplementedError(msg) from exc
        # Fix all geometry variables and remove equations sourced from the geometry.
        for v in [self._get_var(geo, n) for n in vector_names]:
            v.fixed = True
        self._equations = [e for e in self._equations if e.element != geo]

    def _add_equation(self, constraint: AbstractConstraint,
                           eq_map: dict[GeoCombo,
                                        Callable[[AbstractConstraint], list[ConstraintEquation]]]
                           ) -> None:
        types = frozenset(type(g) for g in constraint.get_geometry())
        try:
            func = eq_map[types]
        except KeyError as exc:
            geo = constraint.get_geometry()
            msg = f"{constraint.type_name} geometry combo of {geo} is not supported or is invalid"
            raise NotImplementedError(msg) from exc
        self._equations.append(func(constraint))

    def _new_constraint_eq(self,
                           constraint: AbstractConstraint,
                           eq: CEN,
                           var_map: dict[Type[AbstractGeometry], list[CVN]],
                           constants: Optional[dict[str, np.float64]]=None,
                           ) -> ConstraintEquation:
        if constants is None:
            constants = {}
        params = []
        for geo in constraint.get_geometry():
            try:
                geo_vars = var_map[type(geo)]
            except KeyError as exc:
                msg = f"Got unsupported geometry type {geo} for constraint {constraint}"
                raise NotImplementedError(msg) from exc
            params.extend(self._get_var(geo, var) for var in geo_vars)
        return ConstraintEquation(constraint, eq, params, constants)

    @singledispatchmethod
    def _add_geometry_funcs(self, geometry: AbstractGeometry) -> None:
        """Adds a geometry's internal constraints to the function list."""
        if not isinstance(geometry, Point): # Point has no internal constraints
            msg = (f"Solving the internal geometry constraints of {geometry} has not"
                   " yet been implemented")
            raise NotImplementedError(msg)

    @_add_geometry_funcs.register
    def _axis(self, geometry: Axis) -> None:
        geo_vars = [v for v in self._variables if v.source == geometry.uid]
        func_param_map = {CEN.NON_ZERO: [CVN.DIRECTION],}
        for name, params in func_param_map.items():
            func = ConstraintEquation(geometry, name, [v for v in geo_vars if v.name in params])
            self._equations.append(func)

    @_add_geometry_funcs.register
    def _line(self, geometry: Line) -> None:
        geo_vars = [v for v in self._variables if v.source == geometry.uid]
        func_param_map = {
            CEN.LINE_REF_POINT: [CVN.DIRECTION, CVN.REF_POINT],
            CEN.UNIQUE_VECTOR: [CVN.DIRECTION],
        }
        for name, params in func_param_map.items():
            func = ConstraintEquation(geometry, name, [v for v in geo_vars if v.name in params])
            self._equations.append(func)

    @_add_geometry_funcs.register
    def _plane(self, geometry: Plane) -> None:
        geo_vars = [v for v in self._variables if v.source == geometry.uid]
        func_param_map = {CEN.NON_ZERO: [CVN.NORMAL],}
        for name, params in func_param_map.items():
            func = ConstraintEquation(geometry, name, [v for v in geo_vars if v.name in params])
            self._equations.append(func)

    @singledispatchmethod
    def _add_geometry_variables(self, geometry: AbstractGeometry) -> None:
        """Adds a geometry's internal variables to the variable list."""
        msg = (f"Solving the internal geometry constraints of {geometry} has not"
               " yet been implemented")
        raise NotImplementedError(msg)

    @_add_geometry_variables.register
    def _line_and_axis_vars(self, geometry: Axis | Line) -> None:
        values = {CVN.REF_POINT: geometry.reference_point.cartesian,
                  CVN.DIRECTION: geometry.direction}
        for name, vector in values.items():
            var = ConstraintVariable(geometry, name, np.array(vector), self)
            self._variables.append(var)

    @_add_geometry_variables.register
    def _point_vars(self, geometry: Point) -> None:
        var = ConstraintVariable(geometry, CVN.LOCATION, np.array(geometry.cartesian), self)
        self._variables.append(var)

    @_add_geometry_variables.register
    def _plane_vars(self, geometry: Plane) -> None:
        values = {CVN.NORMAL: geometry.normal,
                  CVN.REF_POINT: geometry.reference_point.cartesian}
        for name, vector in values.items():
            var = ConstraintVariable(geometry, name, np.array(vector), self)
            self._variables.append(var)

    @staticmethod
    def _var_data(var: ConstraintVariable) -> dict[str, str | SpaceVector | Real]:
        """Returns a dict of variable data from a ConstraintVariable for reporting."""
        if isinstance(var.initial, tuple):
            end = var.start + len(var.initial)
        else:
            end = var.start + 1
        return {
            "source": str(var.source),
            "name": var.name,
            "init": var.initial,
            "i": (var.start, end - 1)
        }

    def __str__(self) -> str:
        strings = []
        var_column_map = {
            "Source UID": "source",
            "Name": "name",
            "Initial Value": "init",
            "Indices": "i",
        }
        variable_data = [self._var_data(v) for v in self._variables]
        table = get_table_string(variable_data, var_column_map)
        strings.append("Solver Variables".center(max(map(len, table.splitlines()))))
        strings.append(table)
        func_strings = []
        for i, f in enumerate(self._equations):
            func_var_data = [self._var_data(v) for v in f.params]
            table = get_table_string(func_var_data, var_column_map)
            func_strings.append(f"{i} Name: {f.name} Source: {f.source}")
            func_strings.append(textwrap.indent(table, "    "))
        func_table = "\n".join(map(textwrap.indent, func_strings, repeat("  ")))
        strings.append("Solver Equations".center(max(map(len, func_table.splitlines()))))
        strings.append(func_table)
        init_vals = self.label_x(self.get_initial())
        strings.append("Initial Values".center(max(map(len, init_vals.splitlines()))))
        strings.append(init_vals)
        return "\n".join(strings)


def _update_location(geometry: Point, value: npt.NDArray) -> None:
    """Updates a Point's location."""
    geometry.cartesian = value

def _update_direction(geometry: Axis | Line,  value: npt.NDArray) -> None:
    """Updates a Line or Axis direction."""
    geometry.direction = value

def _update_normal(geometry: Plane, value: npt.NDArray) -> None:
    """Updates a Plane's normal vector."""
    geometry.normal = value

def _update_ref_point(geometry: Axis | Line | Plane, value: npt.NDArray) -> None:
    """Updates a Line or Axis reference point closest to the origin."""
    geometry.move_to_point(value)
