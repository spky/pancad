"""A module providing a class to represent coordinate systems in CAD programs, 
graphics, and other geometry use cases.
"""
from __future__ import annotations

from functools import partial, partialmethod
import math

import numpy as np

from PanCAD.geometry import Point, Line, Plane
from PanCAD.geometry.constants import ConstraintReference

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
    UID_SEPARATOR = "_"
    XLINE_UID = "xline"
    YLINE_UID = "yline"
    ZLINE_UID = "zline"
    ORIGIN_UID = "origin"
    
    def __init__(self, origin: Point|tuple|np.ndarray=None,
                 alpha: float=0, beta: float=0, gamma: float=0, *,
                 right_handed: bool=True, uid: str=None):
        
        if origin is None:
            origin = (0, 0, 0)
        
        if isinstance(origin, (tuple, np.ndarray)):
            origin = Point(origin)
        
        if not right_handed:
            raise NotImplementedError("Left-Handed CoordinateSystems not"
                                      " yet implemented.")
        
        # Initialize reference geometry and then translate/rotate into place
        if len(origin) == 2:
            self._origin = Point(0, 0)
            self.origin = origin
            if beta != 0 or gamma != 0:
                raise ValueError("beta and/or gamma angles cannot be set for a"
                                 " 2D coordinate system")
            self._x_axis_line = Line(self.origin, (1, 0))
            self._y_axis_line = Line(self.origin, (0, 1))
            initial_axis_matrix = (
                self._x_axis_line.direction, self._y_axis_line.direction,
            )
            rotation_matrix = rotation_2(alpha)
        else:
            self._origin = Point(0, 0, 0)
            self.origin = origin
            self._x_axis_line = Line(self.origin, (1, 0, 0))
            self._y_axis_line = Line(self.origin, (0, 1, 0))
            self._z_axis_line = Line(self.origin, (0, 0, 1))
            self._xy_plane = Plane(self.origin, self._z_axis_line.direction)
            self._xz_plane = Plane(self.origin, self._y_axis_line.direction)
            self._yz_plane = Plane(self.origin, self._x_axis_line.direction)
            
            initial_axis_matrix = (
                self._x_axis_line.direction, self._y_axis_line.direction,
                self._z_axis_line.direction,
            )
            rotation_matrix = yaw_pitch_roll(alpha, beta, gamma)
        self._set_axes(initial_axis_matrix)
        self._rotate_axes(rotation_matrix)
        self.uid = uid
    
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
        return self._origin
    
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
        if isinstance(point, Point):
            self._origin.update(point)
        else:
            self._origin.cartesian = point
    
    @uid.setter
    def uid(self, uid: str) -> None:
        if uid is None:
            self._x_axis_line.uid = self.XLINE_UID
            self._y_axis_line.uid = self.YLINE_UID
            self._origin.uid = self.ORIGIN_UID
        else:
            self._x_axis_line.uid = self.UID_SEPARATOR.join([uid,
                                                             self.XLINE_UID])
            self._y_axis_line.uid = self.UID_SEPARATOR.join([uid,
                                                             self.YLINE_UID])
            self._origin.uid = self.UID_SEPARATOR.join([uid, self.ORIGIN_UID])
            
        if len(self.origin) == 3 and uid is None:
            self._z_axis_line.uid = self.ZLINE_UID
        elif len(self.origin) == 3:
            self._z_axis_line.uid = self.UID_SEPARATOR.join([uid,
                                                             self.ZLINE_UID])
        
        self._uid = uid
    
    # Public Methods #
    def get_axis_line_x(self) -> Line:
        return self._x_axis_line
    
    def get_axis_line_y(self) -> Line:
        return self._y_axis_line
    
    def get_axis_line_z(self) -> Line:
        return self._z_axis_line
    
    def get_axis_vectors(self) -> tuple[tuple]:
        if len(self.origin) == 2:
            return (self.x_vector, self.y_vector)
        else:
            return (self.x_vector, self.y_vector, self.z_vector)
    
    def get_reference(self,
                      reference: ConstraintReference) -> Point | Line | Plane:
        if len(self.origin) == 2:
            match reference:
                case ConstraintReference.ORIGIN:
                    return self.origin
                case ConstraintReference.X:
                    return self.get_axis_line_x()
                case ConstraintReference.Y:
                    return self.get_axis_line_y()
                case _:
                    raise ValueError(f"2D {self.__class__}s do not have any"
                                     f" {reference.name} reference geometry")
        else:
            match reference:
                case ConstraintReference.ORIGIN:
                    return self.origin
                case ConstraintReference.X:
                    return self.get_axis_line_x()
                case ConstraintReference.Y:
                    return self.get_axis_line_y()
                case ConstraintReference.Z:
                    return self.get_axis_line_z()
                case ConstraintReference.XY:
                    return self.get_xy_plane()
                case ConstraintReference.XZ:
                    return self.get_xz_plane()
                case ConstraintReference.YZ:
                    return self.get_yz_plane()
                case _:
                    raise ValueError(f"3D {self.__class__}s do not have any"
                                     f" {reference.name} reference geometry")
    
    def get_xy_plane(self) -> Plane:
        return self._xy_plane
    
    def get_xz_plane(self) -> Plane:
        return self._xz_plane
    
    def get_yz_plane(self) -> Plane:
        return self._yz_plane
    
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
        self._update_axis_lines_and_planes()
    
    def _update_axis_lines_and_planes(self):
        self._x_axis_line.update(Line(self.origin, self._x_vector))
        self._y_axis_line.update(Line(self.origin, self._y_vector))
        if len(self.origin) == 3:
            self._z_axis_line.update(Line(self.origin, self._z_vector))
            
            self._xy_plane.update(Plane(self.origin, self._z_vector))
            self._xz_plane.update(Plane(self.origin, self._y_vector))
            self._yz_plane.update(Plane(self.origin, self._x_vector))
    
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
        return f"<PanCADCoordSys'{self.uid}'({point_str}){axis_str}>"
    
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