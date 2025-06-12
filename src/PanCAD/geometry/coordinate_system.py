"""A module providing a class to represent coordinate systems in CAD programs, 
graphics, and other geometry use cases.
"""
from __future__ import annotations

from functools import partial, partialmethod
import math

import numpy as np

from PanCAD.geometry import Point, Line, Plane
from PanCAD.geometry.constants import PlaneName

from PanCAD.utils import comparison
from PanCAD.utils.trigonometry import (
    yaw_pitch_roll, rotation_2, to_1D_tuple
)

isclose = partial(comparison.isclose, nan_equal=False)
isclose0 = partial(comparison.isclose, value_b=0, nan_equal=False)

class CoordinateSystem:
    """A class representing coordinate systems in 2D and 3D space. Initial 
    rotation is defined by Tait-Bryan (zyx) yaw-pitch-roll angles.
    
    :param origin: A 2D or 3D Point defining the center of the coordinate system
    :param alpha: Angle to rotate about the z-axis, defaults to 0
    :param beta: Angle to rotate about the y-axis after alpha, defaults to 0. 
        Cannot be set for a 2D coordinate system
    :param gamma: Angle to rotate about the x-axis after beta, defaults to 0. 
        Cannot be set for a 2D coordinate system
    :param right_handed: Sets the coordinate system to right-handed if true, 
        left-handed if false
    :param uid: The unique ID of the coordinate system for interoperable CAD 
        identification
    """
    
    def __init__(self, origin: Point|tuple|np.ndarray,
                 alpha: float=0, beta: float=0, gamma: float=0, *,
                 right_handed: bool=True, uid: str=None):
        self.uid = uid
        
        if isinstance(origin, (tuple, np.ndarray)):
            origin = Point(origin)
        self.origin = origin
        
        if not right_handed:
            raise NotImplementedError("Left-Handed CoordinateSystems not"
                                      " yet implemented.")
        
        if len(self.origin) == 2:
            if beta != 0 or gamma != 0:
                raise ValueError("beta and/or gamma angles cannot be set for a"
                                 " 2D coordinate system")
            initial_axis_matrix = (
                (1, 0),
                (0, 1),
            )
            rotation_matrix = rotation_2(alpha)
        else:
            initial_axis_matrix = (
                (1, 0, 0),
                (0, 1, 0),
                (0, 0, 1),
            )
            rotation_matrix = yaw_pitch_roll(alpha, beta, gamma)
        self._set_axes(initial_axis_matrix)
        self._rotate_axes(rotation_matrix)
    
    # Getters #
    @property
    def uid(self) -> str:
        """The unique id of the coordinate system. Can also be interpreted as 
        the name of the coordinate system
        
        :getter: Returns the unique id as a string.
        :setter: Sets the unique id.
        """
        return self._uid
    
    @property
    def origin(self) -> Point:
        return self._origin.copy()
    
    @property
    def x_vector(self) -> tuple:
        return self._x_vector
    
    @property
    def y_vector(self) -> tuple:
        return self._y_vector
    
    @property
    def z_vector(self) -> tuple:
        return self._z_vector
    
    # Setters #
    @origin.setter
    def origin(self, point: Point|tuple|np.ndarray):
        self._origin = point
    
    @uid.setter
    def uid(self, uid: str) -> None:
        self._uid = uid
    
    # Public Methods #
    def get_axis_line_x(self) -> Line:
        return Line(self.origin, self.x_vector)
    
    def get_axis_line_y(self) -> Line:
        return Line(self.origin, self.y_vector)
    
    def get_axis_line_z(self) -> Line:
        return Line(self.origin, self.z_vector)
    
    def get_axis_vectors(self) -> tuple[tuple]:
        if len(self.origin) == 2:
            return (self.x_vector, self.y_vector)
        else:
            return (self.x_vector, self.y_vector, self.z_vector)
    
    def get_plane_by_name(self, name: str) -> Plane:
        match name:
            case PlaneName.XY:
                return self.get_xy_plane()
            case PlaneName.XZ:
                return self.get_xz_plane()
            case PlaneName.YZ:
                return self.get_yz_plane()
            case _:
                raise ValueError(f"{name} not recognized, must be one of"
                                 f" {list(PlaneName)}")
    
    def get_xy_plane(self) -> Plane:
        return Plane(self.origin, self.z_vector)
    
    def get_xz_plane(self) -> Plane:
        return Plane(self.origin, self.y_vector)
    
    def get_yz_plane(self) -> Plane:
        return Plane(self.origin, self.x_vector)
    
    def update(self, other: CoordinateSystem) -> None:
        self.origin = other.origin
        self._set_axes(other.get_axis_vectors())
    
    # Private Methods #
    def _rotate_axes(self, rotation_matrix: np.ndarray) -> None:
        """Applies the rotation matrix to all the coordinate system's axes
        """
        new_axis_matrix = [rotation_matrix @ axis
                           for axis in self.get_axis_vectors()]
        self._set_axes(new_axis_matrix)
    
    def _set_axes(self, axis_matrix: list|tuple|np.ndarray) -> None:
        """Used to set the axes all at once while ensuring they are tuples. 
        Assumes that the axes are still unit vectors, perpendicular, and 
        linearly independent (that's why this is private).
        """
        if len(self.origin) == len(axis_matrix) == 2:
            x, y = axis_matrix
            self._x_vector = to_1D_tuple(x)
            self._y_vector = to_1D_tuple(y)
        elif len(self.origin) == len(axis_matrix) == 3:
            x, y, z = axis_matrix
            self._x_vector = to_1D_tuple(x)
            self._y_vector = to_1D_tuple(y)
            self._z_vector = to_1D_tuple(z)
        else:
            raise ValueError("axis_matrix must be for the same number of"
                             " dimensions as the origin point")
    
    # Python Dunders #
    def __repr__(self) -> str:
        """Returns the short string representation of the coordinate system"""
        pt_strs, axis_strs = [], []
        for i in range(0, len(self.origin)):
            if isclose0(self.origin[i]):
                pt_strs.append("0")
            else:
                pt_strs.append("{:g}".format(self.origin[i]))
        axis_no = 0
        for axis in self.get_axis_vectors():
            
            component_strs = []
            for component in axis:
                if isclose0(component):
                    component_strs.append("0")
                else:
                    component_strs.append("{:g}".format(component))
            component_str = ",".join(component_strs)
            axis_name = chr(ord("x") + axis_no)
            axis_no += 1
            axis_strs.append(axis_name + "(" + component_str + ")")
        axis_str = "".join(axis_strs)
        point_str = ",".join(pt_strs)
        return f"<PanCAD_CoordinateSystem({point_str}){axis_str}>"
    
    def __len__(self) -> int:
        """Returns the number of dimensions of the coordinate system by returning 
        the number of dimensions of the origin point"""
        return len(self.origin)
    
    def __str__(self) -> str:
        """Returns the string representation of the coordinate system"""
        pt_strs, axis_strs = [], []
        for i in range(0, len(self.origin)):
            if isclose0(self.origin[i]):
                pt_strs.append("0")
            else:
                pt_strs.append("{:g}".format(self.origin[i]))
        axis_no = 0
        for axis in self.get_axis_vectors():
            
            component_strs = []
            for component in axis:
                if isclose0(component):
                    component_strs.append("0")
                else:
                    component_strs.append("{:g}".format(component))
            component_str = ", ".join(component_strs)
            axis_name = chr(ord("x") + axis_no)
            axis_no += 1
            axis_strs.append(f"{axis_name.upper()}-Axis ({component_str})")
        axis_str = " ".join(axis_strs)
        point_str = ", ".join(pt_strs)
        return f"PanCAD CoordinateSystem with origin ({point_str}) and axes {axis_str}"