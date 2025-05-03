"""A module providing a class to represent lines in all CAD programs, 
graphics, and other geometry use cases."""
from __future__ import annotations

import math

import numpy as np

from PanCAD.geometry import Point
from PanCAD.utils import trigonometry as trig

class Plane:
    
    relative_tolerance = 1e-9
    absolute_tolerance = 1e-9
    
    def __init__(self, point: Point = None,
                 normal_vector: list | tuple | np.ndarray = None,
                 uid: str = None):
        self.uid = uid
        
        if isinstance(point, Point):
            self.normal = normal_vector
            self._point_closest_to_origin = (
                Plane._closest_to_origin(point, self.normal)
            )
        else:
            self._point_closest_to_origin = None
    
    # Getters #
    @property
    def normal(self) -> tuple:
        """The unit vector that describes the normal direction of the plane.
        
        :getter: Returns the normal vector of the plane as a tuple
        :setter: Takes a vector, finds its unit vector, and then set that as the 
        direction of the plane
        """
        return self._normal
    
    @property
    def reference_point(self) -> Point:
        """The closest point to the origin on the plane.
        
        :getter: Returns the Point instance representing the point closest to 
                 the origin on the plane.
        :setter: There is no setter, reference_point is read-only
        """
        return self._point_closest_to_origin
    
    # Setters #
    @normal.setter
    def normal(self, vector: list | tuple | np.ndarray):
        if vector is not None:
            self._normal = trig.to_1D_tuple(trig.get_unit_vector(vector))
        else:
            self._normal = None
    
    # Public Methods #
    def get_d(self) -> float:
        """Returns the Plane's Point-Normal form constant d (equation of form 
        ax + by + cz + d = 0)
        """
        a, b, c = self.normal
        x0, y0, z0 = tuple(self.reference_point)
        return -(a*x0 + b*y0 + c*z0)
    
    # Private Methods
    def _isclose(self, value_a: float, value_b: float) -> bool:
        """Returns whether value_a is close to value_b using the Plane's class 
        variables.
        
        :param value_a: A value to compare
        :param value_b: Another value to compare
        :returns: True if value_a == value_b within the relative and absolute 
                  tolerance class variables
        """
        return math.isclose(value_a, value_b,
                            rel_tol=self.relative_tolerance,
                            abs_tol=self.absolute_tolerance)
    
    def _isclose_tuple(self, value_a: tuple, value_b: tuple) -> bool:
        """Returns whether the components of value_a are close to the 
        corresponding components of value_b using the Plane's class variables.
        
        :param value_a: A tuple to compare
        :param value_b: Another tuple to compare
        :returns: True if value_a's components == value_b's components within 
                  the Plane's relative and absolute tolerance class variables
        """
        return trig.isclose_tuple(value_a, value_b,
                                  rel_tol=self.relative_tolerance,
                                  abs_tol=self.absolute_tolerance)
    
    # Static Methods #
    @staticmethod
    def _closest_to_origin(point: Point, vector: tuple) -> Point:
        """Returns the point on the plane created by the point and normal vector 
        closest to the origin.
        
        :param point: a Point on the plane
        :param vector: a vector normal to the plane
        :returns: The point on the plane closest to the origin
        """
        if len(point) == 2:
            point_vector = (point.x, point.y, 0)
        else:
            point_vector = tuple(point)
        
        if len(vector) == 2:
            normal_vector = (vector[0], vector[1], 0)
        else:
            normal_vector = trig.to_1D_tuple(vector)
        
        x0, y0, z0 = point_vector
        a, b, c = normal_vector
        t = (a*x0 + b*y0 + c*z0)/(a**2 + b**2 + c**2)
        
        return Point(a*t, b*t, c*t)
    
    # Python Dunders #
    def __copy__(self) -> Line:
        """Returns a copy of the plane that has the same closest to origin 
        point and normal vector, but no assigned uid. Can be used with the python 
        copy module"""
        return Plane(self.reference_point, self.normal)
    
    def __eq__(self, other: Plane) -> bool:
        """Rich comparison for plane equality that allows for planes to be 
        directly compared with ==.
        
        :param other: The plane to compare self to.
        :returns: Whether the tuples of the planes' reference_points and 
                  normal vectors are equal
        """
        if isinstance(other, Plane):
            return (
                self._isclose_tuple(tuple(self.reference_point),
                                    tuple(other.reference_point))
                and self._isclose_tuple(self.normal, other.normal)
            )
        else:
            return NotImplemented
    
    def __len__(self) -> int:
        """Returns the number of elements in the plane's normal tuple, 
        which is equivalent to the plane's number of dimnesions. Should always be 
        3, but this is included for compatibility with other 2D objects."""
        return len(self.normal)
    
    def __repr__(self) -> str:
        """Returns the short string representation of the plane"""
        return f"PanCAD_Plane{tuple(self._point_closest_to_origin)},{self.normal}"
    
    def __str__(self) -> str:
        """String function to output the plane's description, closest 
        cartesian point to the origin, and cartesian normal unit vector
        """
        closest_point = tuple(self._point_closest_to_origin)
        return (f"PanCAD Plane with a point closest to the origin at"
                + f" {closest_point} and with normal vector {self.normal}")