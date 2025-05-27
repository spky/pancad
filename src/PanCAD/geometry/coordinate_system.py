"""A module providing a class to represent coordinate systems in CAD programs, 
graphics, and other geometry use cases.
"""
from __future__ import annotations

from functools import partial
import math

import numpy as np

from PanCAD.geometry import Point, Line, Plane
from PanCAD.utils import comparison
from PanCAD.utils.trigonometry import (
    rotation_x, rotation_y, rotation_z, rotation_2
)

isclose = partial(comparison.isclose, nan_equal=False)
isclose0 = partial(comparison.isclose, value_b=0, nan_equal=False)

class CoordinateSystem:
    
    def __init__(self, origin_point: Point|tuple|np.ndarray,
                 alpha: float=None, beta: float=None, gamma: float=None, *,
                 right_handed: bool=True, uid: str=None, unit: str=None):
        self.uid = uid
        
        if isinstance(origin_point, (tuple, np.ndarray)):
            origin_point = Point(origin_point)
        self.origin = origin_point
        
        if not right_handed:
            raise NotImplementedError("Left-Handed CoordinateSystems not"
                                      " yet implemented.")
        
        if len(self.origin) == 2:
            if beta is not None or gamma is not None:
                raise ValueError("beta and/or gamma angles cannot be set for a"
                                 " 2D coordinate system")
            self._x_vector = (1, 0)
            self._y_vector = (0, 1)
            if alpha is not None:
                self._x_vector = rotation_2(alpha) @ self._x_vector
                self._y_vector = rotation_2(alpha) @ self._y_vector
        else:
            rotation = np.identity(3)
            if alpha is not None:
                rotation = rotation @ rotation_z(alpha)
            if beta is not None:
                rotation = rotation @ rotation_y(beta)
            if gamma is not None:
                rotation = rotation @ rotation_x(gamma)
            self._x_vector = rotation @ (1, 0, 0)
            self._y_vector = rotation @ (0, 1, 0)
            self._z_vector = rotation @ (0, 0, 1)
        
        
        # Alpha, Beta, and Gamma are Tait-Bryan angles, which is a rotation 
        # around z, y, and x respectively
    
    
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
    def axis_vectors(self) -> tuple(tuple):
        if len(self.origin) == 2:
            return (self.x_vector, self.y_vector)
        else:
            return (self.x_vector, self.y_vector, self.z_vector)
    
    @property
    def x_vector(self) -> tuple:
        return self._x_vector
    
    @property
    def y_vector(self) -> tuple:
        return self._y_vector
    
    @property
    def z_vector(self) -> tuple:
        return self._z_vector
    
    @origin.setter
    def origin(self, point: Point|tuple|np.ndarray):
        self._origin = point
    
    @uid.setter
    def uid(self, uid: str) -> None:
        self._uid = uid
    
    # Public Methods #
    def get_axis_line_x(self) -> Line:
        return Line(self.origin_point, self.x_vector)
    
    def get_axis_line_y(self) -> Line:
        return Line(self.origin_point, self.y_vector)
    
    def get_axis_line_z(self) -> Line:
        return Line(self.origin_point, self.z_vector)
    
    # Python Dunders #
    def __repr__(self) -> str:
        """Returns the short string representation of the point"""
        pt_strs, axis_strs = [], []
        for i in range(0, len(self.origin)):
            if isclose0(self.origin[i]):
                pt_strs.append("0")
            else:
                pt_strs.append("{:g}".format(self.origin[i]))
        axis_no = 0
        for axis in self.axis_vectors:
            
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