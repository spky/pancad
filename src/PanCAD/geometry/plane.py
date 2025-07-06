"""A module providing a class to represent lines in all CAD programs, 
graphics, and other geometry use cases."""
from __future__ import annotations

from functools import partial
import math

import numpy as np

from PanCAD.geometry.abstract_geometry import AbstractGeometry
from PanCAD.geometry import Point
from PanCAD.utils import trigonometry as trig, comparison
from PanCAD.geometry.constants import ConstraintReference

isclose = partial(comparison.isclose, nan_equal=False)
isclose0 = partial(comparison.isclose, value_b=0, nan_equal=False)

class Plane(AbstractGeometry):
    
    def __init__(self, point: Point | tuple | np.ndarray = None,
                 normal_vector: list | tuple | np.ndarray = None,
                 uid: str = None):
        self.uid = uid
        self._references = (ConstraintReference.CORE,)
        
        if isinstance(point, (tuple, np.ndarray)):
            point = Point(point)
        
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
    def normal_spherical(self) -> tuple:
        """The unit vector describing the normal direction of the plane in 
        spherical coordinates
        
        :getter: Returns the normal vector of the plane as a spherical tuple
        :setter: None, read-only. Use a public method to change the direction
        """
        return trig.cartesian_to_spherical(self.normal)
    
    @property
    def phi(self) -> float:
        """The spherical azimuth component of the plane's normal vector in 
        radians.
        
        :getter: Returns the azimuth component of the plane's normal vector
        :setter: None, read-only. Use a public method to change the normal vector
        """
        return trig.phi_of_cartesian(self.normal)
    
    @property
    def reference_point(self) -> Point:
        """The closest point to the origin on the plane.
        
        :getter: Returns a copy of the Point instance representing the point 
            closest to the origin on the plane.
        :setter: None, read-only. Use a public method to change the plane position
        """
        return self._point_closest_to_origin.copy()
    
    @property
    def theta(self) -> float:
        """The spherical inclination component of the plane's normal vector in 
        radians.
        
        :getter: Returns the inclination angle of the plane's normal vector.
        :setter: None, read-only. Use a public method to change the normal vector
        """
        return trig.theta_of_cartesian(self.normal)
    
    @property
    def uid(self) -> str:
        """The unique id of the plane. Can also be interpreted as the name of 
        the plane
        
        :getter: Returns the unique id as a string.
        :setter: Sets the unique id.
        """
        return self._uid
    
    # Setters #
    @normal.setter
    def normal(self, vector: list | tuple | np.ndarray):
        if vector is not None:
            self._normal = trig.to_1D_tuple(trig.get_unit_vector(vector))
        else:
            self._normal = None
    
    @phi.setter
    def phi(self, value: float):
        raise NotImplementedError
    
    @theta.setter
    def theta(self, value: float):
        raise NotImplementedError
    
    @uid.setter
    def uid(self, uid: str) -> None:
        self._uid = uid
    
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
    
    def get_reference(self, reference: ConstraintReference
                      ) -> Plane:
        """Returns reference geometry for use in external modules like 
        constraints. Warning: Unlike some common PanCAD functions this one does 
        not return a copy of geometry, but the a reference to the internal 
        geometry object.
        
        :param reference: A ConstraintReference enumeration value. Planes only 
            have a core reference, so any other value will cause an error.
        :returns: The Line itself or an error.
        """
        match reference:
            case ConstraintReference.CORE:
                return self
            case _:
                raise ValueError(f"{self.__class__}s do not have any"
                                 f" {reference.name} reference geometry")
    
    def get_all_references(self) -> tuple[ConstraintReference]:
        return self._references
    
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
            self.normal = normal_vector
        self._point_closest_to_origin = Plane._closest_to_origin(point,
                                                                 normal_vector)
        return self
    
    def update(self, other: Plane) -> None:
        """Updates the plane to match the position and normal direction of 
        another plane.
        
        :param other: The plane to update to
        """
        self._point_closest_to_origin = other.reference_point
        self.normal = other.normal
    
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
        pt_strs, normal_strs = [], []
        for i in range(0, len(self.normal)):
            if isclose0(self._point_closest_to_origin[i]):
                pt_strs.append("0")
            else:
                pt_strs.append("{:g}".format(self._point_closest_to_origin[i]))
            if isclose0(self.normal[i]):
                normal_strs.append("0")
            else:
                normal_strs.append("{:g}".format(self.normal[i]))
        point_str = ",".join(pt_strs)
        normal_str = ",".join(normal_strs)
        return f"<PanCAD_Plane({point_str})({normal_str})>"
    
    def __str__(self) -> str:
        """String function to output the plane's description, closest 
        cartesian point to the origin, and cartesian normal unit vector
        """
        pt_strs, normal_strs = [], []
        for i in range(0, len(self.normal)):
            if isclose0(self._point_closest_to_origin[i]):
                pt_strs.append("0")
            else:
                pt_strs.append("{:g}".format(self._point_closest_to_origin[i]))
            if isclose0(self.normal[i]):
                normal_strs.append("0")
            else:
                normal_strs.append("{:g}".format(self.normal[i]))
        point_str = ", ".join(pt_strs)
        normal_str = ", ".join(normal_strs)
        return (f"PanCAD Plane with a point closest to the origin at"
                + f" ({point_str}) and with normal vector ({normal_str})")