"""A module providing secondary solving functions that perform operations on
pancad geometry. pancad geometry must not directly depend on these since doing
they would be cyclically dependent.
"""
from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING
import textwrap
from itertools import repeat
from functools import singledispatch, singledispatchmethod

import numpy as np
from scipy.optimize import root as find_root

from pancad.abstract import AbstractGeometry, AbstractConstraint
from pancad.constants import (ConstraintVariableName as CVN,
                              ConstraintEquationName as CEN)

from pancad.constraints.state_constraint import Coincident
from pancad.constraints.snapto import Fixed
from pancad.geometry.line_segment import LineSegment
from pancad.geometry.line import Axis
from pancad.geometry.point import Point
from pancad.utils.pancad_types import FitBox2D, SpaceVector
from pancad.utils.text_formatting import get_table_string

if TYPE_CHECKING:
    from numbers import Real
    from typing import Literal
    from uuid import UUID

    import numpy.typing as npt

    from pancad.abstract import AbstractGeometrySystem, PancadThing

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

################################################################################
# Constraint Residuals
################################################################################

def line_ref_point_res(eq: ConstraintEquation, x: npt.NDArray) -> npt.NDArray:
    """Returns the residual for how close an axis or line's reference point is to
    being the closest to origin point.
    """
    point, direction = [x[slice(*p.get_slicer())] for p in eq.params]
    return np.array([np.dot(direction, point)])

def unit_vector_res(eq: ConstraintEquation, x: npt.NDArray) -> npt.NDArray:
    """Returns the residual for how close a vector is to being a unit vector."""
    vector = x[slice(*eq.params[0].get_slicer())]
    return np.array([np.sum(np.array(vector)**2) - 1])

def point_line_coincident_res(eq: ConstraintEquation, x: npt.NDArray) -> npt.NDArray:
    """Returns the residual for how close a point is to being coincident on an
    axis or line.
    """
    ref_point, direction, point, t_param = [x[slice(*p.get_slicer())] for p in eq.params]
    t_param = t_param[0]
    return np.array(direction) * t_param + np.array(ref_point) - np.array(point)

def fixed_point_res(eq: ConstraintEquation, x: npt.NDArray) -> npt.NDArray:
    """Returns the residual for how close a fixed point is to its required location."""
    position_slice = slice(*eq.params[0].get_slicer())
    return np.array(x[position_slice]) - np.array(eq.x0[position_slice])

RESIDUAL_FUNCS = {
    CEN.UNIT_VECTOR: unit_vector_res,
    CEN.LINE_REF_POINT: line_ref_point_res,
    CEN.POINT_LINE_COINCIDENT: point_line_coincident_res,
    CEN.FIXED_POINT: fixed_point_res,
}

@dataclasses.dataclass
class ConstraintVariable:
    """A dataclass for tracking the names of variables used by constraint functions.

    :param source: The unique id of the source.
    :param name: The ConstraintVariableName that defines what part of the source
        element the variable is referring to.
    :param initial: The initial value of the variable.
    :param start: The start index for the variable.
    """
    source: str | UUID
    name: CVN
    initial: Real | SpaceVector
    start: int
    delim: str = dataclasses.field(repr=False)
    element: AbstractGeometry | AbstractConstraint

    @property
    def key(self) -> str:
        """The identifying unique key of the constraint variable."""
        return self.delim.join(map(str, [self.source, self.name]))

    def get_slicer(self) -> tuple[int, int]:
        """Returns first variable index and last index + 1 of the variable vector
        representing this value.
        """
        if isinstance(self.initial, tuple):
            return (self.start, self.start + len(self.initial))
        return (self.start, self.start + 1)

@dataclasses.dataclass
class ConstraintEquation:
    """A dataclass for tracking imposed and internal constraint equation function
    names and parameter names.
    """
    source: str
    name: CEN
    params: list[ConstraintVariable] = dataclasses.field(repr=False)
    delim: str = dataclasses.field(repr=False)
    x0: list[Real]

    @property
    def key(self) -> str:
        """The identifying unique key of the constraint function."""
        return self.delim.join(map(str, [self.source, self.name]))

    def calc(self, x: npt.NDArray) -> npt.NDArray:
        """Calculates the equation's residual for a given vector value."""
        return RESIDUAL_FUNCS[self.name](self, x)

class SystemSolver:
    """A class that solves a geometry system's internal and imposed constraints
    and updates its geometry to meet them.
    """
    _delim = "_"
    _func_map = {
        CEN.UNIT_VECTOR: unit_vector_res,
        CEN.LINE_REF_POINT: line_ref_point_res,
        CEN.POINT_LINE_COINCIDENT: point_line_coincident_res,
        CEN.FIXED_POINT: fixed_point_res,
    }

    def __init__(self, system: AbstractGeometrySystem) -> None:
        self._system = system
        self._functions = []
        self._variables = []
        self._x0 = []
        for c in self._system.constraints:
            for geo in c.get_parents():
                # Make sure the geometry variables/constraints have been added
                if not any(v.source == geo.uid for v in self._variables):
                    self._add_geometry_variables(geo)
                    self._add_geometry_funcs(geo)
            self._add_constraint(c)

    def fun(self, x: npt.NDArray) -> npt.NDArray:
        """Returns the residuals of the system for a given vector value."""
        result = np.concatenate([f.calc(x) for f in self._functions])
        return result

    def solve(self, method: str="lm", **kwargs) -> npt.NDArray:
        """Returns the roots of the system's functions as a 1D numpy array.

        :param method: The type of solver that should be used. Defaults to
            Levenberg-Marquardt (lm). See scipy.optimize.root for other options.
        """
        return find_root(self.fun, self._x0, method=method, **kwargs)

    def label_x(self, x: npt.NDArray) -> str:
        """Returns a string table with each vector variable value labeled and indexed."""
        column_map = {
            "#": "#",
            "Value": "value",
            "Name": "name",
            "Source": "source",
            "Element": "element",
        }
        data = []
        index = 0
        i = 0
        for var in self._variables:
            for i, value in enumerate(x[slice(*var.get_slicer())], index):
                data.append(
                    {
                        "#": i,
                        "value": value,
                        "name": var.name,
                        "source": var.source,
                        "element": var.element,
                    }
                )
            index = i + 1
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
            "Source": "source"
        }
        data = []
        start = 0
        i = 0
        for f in self._functions:
            try:
                end = start + len(f.calc(self._x0))
            except TypeError:
                end = start + 1
            for i, value in enumerate(results[slice(start, end)], start):
                data.append(
                    {
                        "#": i,
                        "sub": i - start,
                        "value": value,
                        "name": f.name,
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
    def _coincident(self, constraint: Coincident) -> None:
        geo_types = {type(g) for g in constraint.get_geometry()}
        # Add coincident constraint equation based on geometry combo.
        if geo_types == {Axis, Point}:
            # # Point and Axis
            axis = next(g for g in constraint.get_geometry() if isinstance(g, Axis))
            point = next(g for g in constraint.get_geometry() if isinstance(g, Point))
            t_param = ConstraintVariable(constraint.uid, CVN.PARAMETER, 0,
                                         len(self._x0), self._delim,
                                         constraint)
            self._variables.append(t_param)
            self._x0.append(t_param.initial)
            params = [
                self._get_var(axis, CVN.REF_POINT),
                self._get_var(axis, CVN.DIRECTION),
                self._get_var(point, CVN.LOCATION),
                t_param,
            ]
            func = ConstraintEquation(constraint.uid, CEN.POINT_LINE_COINCIDENT,
                                      params, self._delim, self._x0)
        elif geo_types == {Point}:
            # Both are points
            raise NotImplementedError("Point to point not completed yet")
        else:
            msg = (f"Coincident combo {constraint.get_parents()} is not"
                   " supported and/or may be invalid")
            raise NotImplementedError(msg)
        self._functions.append(func)

    @_add_constraint.register
    def _fixed(self, constraint: Fixed) -> None:
        geo = constraint.get_geometry()[0]
        if isinstance(geo, Point):
            params = [self._get_var(geo, CVN.LOCATION)]
            func = ConstraintEquation(constraint.uid, CEN.FIXED_POINT,
                                      params, self._delim, self._x0)
        else:
            msg = f"Fixed relation for {geo} is not supported and/or may be invalid"
            raise NotImplementedError(msg)
        self._functions.append(func)

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
        func_param_map = {
            CEN.LINE_REF_POINT: [CVN.DIRECTION, CVN.REF_POINT],
            CEN.UNIT_VECTOR: [CVN.DIRECTION]
        }
        for name, params in func_param_map.items():
            func = ConstraintEquation(geometry.uid,
                                      name,
                                      [v for v in geo_vars if v.name in params],
                                      self._delim,
                                      self._x0)
            self._functions.append(func)

    @singledispatchmethod
    def _add_geometry_variables(self, geometry: AbstractGeometry) -> None:
        """Adds a geometry's internal variables to the variable list."""
        msg = (f"Solving the internal geometry constraints of {geometry} has not"
               " yet been implemented")
        raise NotImplementedError(msg)

    @_add_geometry_variables.register
    def _axis_vars(self, geometry: Axis) -> None:
        values = {
            CVN.REF_POINT: geometry.reference_point.cartesian,
            CVN.DIRECTION: geometry.direction,
        }
        for name, vector in values.items():
            variable = ConstraintVariable(geometry.uid, name, vector,
                                          len(self._x0), self._delim, geometry)
            self._x0.extend(variable.initial)
            self._variables.append(variable)

    @_add_geometry_variables.register
    def _point_vars(self, geometry: Point) -> None:
        variable = ConstraintVariable(geometry.uid, CVN.LOCATION, geometry.cartesian,
                                      len(self._x0), self._delim, geometry)
        self._x0.extend(variable.initial)
        self._variables.append(variable)

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
        for i, f in enumerate(self._functions):
            func_var_data = [self._var_data(v) for v in f.params]
            table = get_table_string(func_var_data, var_column_map)
            func_strings.append(f"{i} Name: {f.name} Source: {f.source}")
            func_strings.append(textwrap.indent(table, "    "))
        func_table = "\n".join(map(textwrap.indent, func_strings, repeat("  ")))
        strings.append("Solver Equations".center(max(map(len, func_table.splitlines()))))
        strings.append(func_table)
        init_vals = self.label_x(self._x0)
        strings.append("Initial Values".center(max(map(len, init_vals.splitlines()))))
        strings.append(init_vals)
        return "\n".join(strings)
