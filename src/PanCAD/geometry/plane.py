"""A module providing a class to represent lines in all CAD programs, 
graphics, and other geometry use cases."""
from __future__ import annotations

from functools import partial
import math

import numpy as np

from PanCAD.geometry import Point
from PanCAD.utils import trigonometry as trig
from PanCAD.utils import comparison

isclose = partial(comparison.isclose, nan_equal=False)

class Plane:
    
    def __init__(self, point: Point = None,
                 normal_vector: list | tuple | np.ndarray = None,
                 uid: str = None):
        self.uid = uid
        point = Point(point) if isinstance(point, tuple) else point
        if isinstance(point, Point):
            self.move_to_point(point, normal_vector)
        elif point is None:
            self._point_closest_to_origin = None
        else:
            raise ValueError(f"1st arg must be tuple/Point, not {point.__class__}")
    
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
        return self._point_closest_to_origin.copy()
    
    # Public Methods #
    def get_d(self) -> float:
        """Returns the Plane's Point-Normal form constant d (equation of form 
        ax + by + cz + d = 0)
        """
        a, b, c = self.normal
        x0, y0, z0 = tuple(self.reference_point)
        return -(a*x0 + b*y0 + c*z0)
    
    def get_normal_vector(self, vertical: bool=True) -> np.ndarray:
        """Returns the normal vector of the plane as a numpy vector
        
        :param vertical: If True, the vector will be 3x1, otherwise 1x3
        :returns: A numpy vector of the normal vector
        """
        vector = np.array(self.normal)
        return vector.reshape(3, 1) if vertical else vector
    
    def move_to_point(self, point: Point,
                      normal_vector: list | tuple | np.ndarray = None) -> Plane:
        """Moves the plane to the point. Sets the normal vector at that point if 
        it is given. If no normal vector is given, the plane is moved to be 
        coincident with the point while maintaining the same normal 
        vector.
        
        :param point: A point the plane will be coincident to.
        :param normal_vector: A new normal vector for the plane
        :returns: This plane so it can be fed into further functions
        """
        if normal_vector is None:
            normal_vector = self.normal
        else:
            self._normal = trig.to_1D_tuple(trig.get_unit_vector(normal_vector))
        self._point_closest_to_origin = Plane._closest_to_origin(point,
                                                                 normal_vector)
        return self
    
    # Class Methods #
    @classmethod
    def from_point_and_angles(cls, point: Point, phi: float, theta: float,
                              uid: str=None) -> Plane:
        """Return a Plane from a given point, phi, and theta.
        
        :param point: A point on the plane
        :param phi: The phi angle of the plane's normal vector in radians
        :param theta: The theta angle of the plane's normal vector in radians
        :returns: A Plane object that runs through the point with a normal vector 
            with the provided angles
        """
        if len(point) == 2:
            raise ValueError("Planes can only be initialized by 2D points")
        else:
            return cls(point, trig.spherical_to_cartesian((1, phi, theta)), uid)
    
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
                isclose(tuple(self.reference_point),
                        tuple(other.reference_point))
                and isclose(self.normal, other.normal)
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