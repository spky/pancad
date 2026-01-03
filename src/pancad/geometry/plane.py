"""A module providing a class to represent lines in all CAD programs, 
graphics, and other geometry use cases."""
from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

import numpy as np

from pancad.geometry import AbstractGeometry, Point
from pancad.geometry.constants import ConstraintReference
from pancad.utils import trigonometry as trig, comparison
from pancad.utils.pancad_types import VectorLike
from pancad.utils.geometry import three_dimensions_required

if TYPE_CHECKING:
    from numbers import Real

isclose = partial(comparison.isclose, nan_equal=False)
isclose0 = partial(comparison.isclose, value_b=0, nan_equal=False)

class Plane(AbstractGeometry):
    """A class representing planes in 3D space."""
    def __init__(self, point: Point | VectorLike=None, normal: VectorLike=None,
                 uid: str=None):
        self.uid = uid
        if isinstance(point, VectorLike):
            point = Point(point)
        if not isinstance(point, Point):
            type_ = type(point)
            raise TypeError(f"Expected Point/VectorLike point, got {type_}")
        self.normal = normal
        self._point_closest_to_origin = Plane._closest_to_origin(point,
                                                                 self.normal)
        super().__init__({ConstraintReference.CORE: self})

    # Getters #
    @property
    def normal(self) -> tuple:
        """The unit vector that describes the normal direction of the plane.
        
        :getter: Returns the normal vector of the plane.
        :setter: Takes a vector, finds its unit vector, and then sets that as 
            the direction of the plane.
        """
        return self._normal
    @normal.setter
    @three_dimensions_required
    def normal(self, vector: VectorLike):
        if not isinstance(vector, VectorLike):
            raise TypeError(f"Expected VectorLike, got {type(vector)}")
        self._normal = trig.to_1d_tuple(trig.get_unit_vector(vector))

    @property
    def normal_spherical(self) -> tuple:
        """The unit vector describing the normal direction of the plane in 
        spherical coordinates. Read-only.
        """
        return trig.cartesian_to_spherical(self.normal)

    @property
    def phi(self) -> Real:
        """The spherical azimuth of the plane's normal vector in radians. 
        Read-only.
        """
        return trig.phi_of_cartesian(self.normal)

    @property
    def reference_point(self) -> Point:
        """The closest point to the origin on the plane. Read-only.
        
        :getter: Returns a copy of the Point instance representing the point 
            closest to the origin on the plane.
        """
        return self._point_closest_to_origin.copy()

    @property
    def theta(self) -> Real:
        """The spherical inclination component of the plane's normal vector in 
        radians. Read-only.
        
        :getter: Returns the inclination angle of the plane's normal vector.
        """
        return trig.theta_of_cartesian(self.normal)

    # Public Methods #
    def copy(self) -> Plane:
        """Returns a copy of the plane that has the same closest to origin 
        point and normal vector, but with a different uid.
        """
        return Plane(self.reference_point, self.normal)

    def get_d(self) -> Real:
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
        if vertical:
            return vector.reshape(3, 1)
        return vector

    @three_dimensions_required
    def move_to_point(self, point: Point, normal: VectorLike = None) -> Plane:
        """Moves the plane to the point. Sets the normal vector at that point if 
        it is given. If no normal vector is given, the plane is moved to be 
        coincident with the point while maintaining the same normal 
        vector.
        
        :param point: A point the plane will be coincident to.
        :param normal: A new normal vector for the plane
        :returns: This plane so it can be fed into further functions
        """
        self.normal = normal
        self._point_closest_to_origin.update(
            Plane._closest_to_origin(point, normal)
        )
        return self

    def update(self, other: Plane) -> None:
        """Updates the plane to match the position and normal direction of 
        another plane.
        
        :param other: The plane to update to
        """
        self._point_closest_to_origin.update(other.reference_point)
        self.normal = other.normal

    # Class Methods #
    @classmethod
    @three_dimensions_required
    def from_point_and_angles(cls,
                              point: Point,
                              phi: Real,
                              theta: Real,
                              uid: str=None) -> Plane:
        """Return a Plane from a given point, phi, and theta.
        
        :param point: A point on the plane
        :param phi: The phi angle of the plane's normal vector in radians
        :param theta: The theta angle of the plane's normal vector in radians
        :returns: A Plane object that runs through the point with a normal vector 
            with the provided angles
        """
        return cls(point, trig.spherical_to_cartesian((1, phi, theta)), uid)

    # Static Methods #
    @staticmethod
    @three_dimensions_required
    def _closest_to_origin(point: Point, normal: tuple) -> Point:
        """Returns the point on the plane created by the point and normal vector 
        closest to the origin.
        
        :param point: A Point on the plane
        :param normal: A vector normal to the plane
        :returns: The point on the plane closest to the origin
        """
        x0, y0, z0 = tuple(point)
        a, b, c = tuple(normal)
        t = (a*x0 + b*y0 + c*z0)/(a**2 + b**2 + c**2)
        return Point(a*t, b*t, c*t)

    # Python Dunders #
    def __copy__(self) -> Plane:
        return self.copy()

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
        return NotImplemented

    def __len__(self) -> int:
        """Returns the number of elements in the plane's normal tuple, 
        which is equivalent to the plane's number of dimnesions. Should always be 
        3, but this is included for compatibility with other 2D objects."""
        return len(self.normal)

    def __repr__(self) -> str:
        """Returns the short string representation of the plane. Contains the 
        point closest to the origin and the unit vector normal to the plane.
        """
        strings = []
        for vector in [self.reference_point, self.normal]:
            vector_strings = []
            for component in vector:
                if isclose0(component):
                    vector_strings.append("0")
                else:
                    vector_strings.append(f"{component:g}")
            strings.append(",".join(vector_strings))
        point, normal = strings
        return f"<pancad_Plane({point})({normal})>"

    def __str__(self) -> str:
        return self.__repr__()
