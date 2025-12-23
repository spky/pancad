"""A module providing a class to represent points in all CAD programs,  
graphics, and other geometry use cases.
"""
from __future__ import annotations

from collections.abc import Sequence
import math
from functools import partial
from numbers import Real
from sqlite3 import PrepareProtocol
from typing import Self, TYPE_CHECKING

import numpy as np

from pancad.geometry import AbstractGeometry
from pancad.geometry.constants import ConstraintReference
from pancad.utils import trigonometry as trig, comparison
from pancad.utils.trigonometry import is_geometry_vector

if TYPE_CHECKING:
    from uuid import UUID

isclose = partial(comparison.isclose, nan_equal=False)
isclose0 = partial(comparison.isclose, value_b=0, nan_equal=False)

class Point(AbstractGeometry):
    """A class representing points in 2D and 3D space. Point can return its 
    position in cartesian, spherical, or polar coordinates. Point's __init__ 
    function can only take cartesian coordinates, so either use one of its class 
    functions or initialize it with no arguments and modify one of its 
    coordinate system specific properties if another coordinate system is 
    desired. 
    
    :param components: Either the (x, y) or (x, y, z) as individual Real number 
        arguments or as a single vector.
    :param uid: The unique ID of the point for interoperable CAD identification.
    :param unit: The unit of the point's length values.
    """
    # pylint: disable=too-many-instance-attributes
    # Ok here since the intent of the Point class is to allow other functions to
    # immediately translate coordinates to other systems with minimal
    # boilerplate.
    REFERENCES = (ConstraintReference.CORE,)
    """All relevant ConstraintReferences for Point."""
    def __init__(self, *components: Real | Sequence[Real] | np.ndarray,
                 uid: str | UUID=None, unit: str=None):
        self._iter_index = 0 # Used for __iter__ counting
        self.uid = uid
        self.unit = unit
        self.cartesian = self._parse_components(*components)
    # Class Methods #
    @classmethod
    def from_polar(cls, *components: Real | Sequence[Real] | np.ndarray,
                   uid: str | UUID=None, unit: str=None):
        """Initializes a point from polar coordinates.
        
        :param components: The (Radius (r), Azimuth (phi)) individual Real 
            number arguments or as a single vector. Azimuth must be in radians.
        :param uid: The unique ID of the point for interoperable CAD 
            identification.
        :param unit: The unit of the Radius value.
        :raises ValueError: When provided a vector not 2 long.
        """
        vector = Point._parse_components(*components)
        if len(vector) != 2:
            raise ValueError(f"Expected a vector 2 long, got {vector}")
        return cls(trig.polar_to_cartesian(vector), uid=uid, unit=unit)
    @classmethod
    def from_spherical(cls, *components: Real | Sequence[Real] | np.ndarray,
                       uid: str | UUID=None, unit: str=None):
        """Initializes a point from spherical coordinates (Radius (r), Azimuth 
        (phi), Elevation (theta)). Azimuth and Elevation angles must be in 
        radians.
        :param components: The (Radius (r), Azimuth (phi), Elevation (theta)) 
            individual Real number arguments or as a single vector. Azimuth and 
            Elevation must be in radians.
        :param uid: The unique ID of the point for interoperable CAD 
            identification.
        :param unit: The unit of the Radius value.
        :raises ValueError: When provided a vector not 3 long.
        """
        vector = Point._parse_components(*components)
        if len(vector) != 3:
            raise ValueError(f"Expected a vector 3 long, got {vector}")
        return cls(trig.spherical_to_cartesian(vector), uid=uid, unit=unit)
    # Cartesian Coordinates #
    @property
    def cartesian(self) -> tuple[Real, Real] | tuple[Real, Real, Real]:
        """The cartesian coordinates (x, y) or(x, y, z) of the point.
        
        :raises ValueError: When provided a tuple not 2 or 3 long.
        """
        return self._cartesian
    @cartesian.setter
    def cartesian(self, value: Sequence[Real]) -> None:
        if len(value) not in [2, 3]:
            raise ValueError(f"Expected 2 or 3 long vector, given {len(value)}")
        self._cartesian = tuple(value)
    @property
    def x(self) -> Real:
        """The point's cartesian x-coordinate."""
        return self.cartesian[0]
    @x.setter
    def x(self, value: Real) -> None:
        if len(self) == 2:
            self.cartesian = (value, self.cartesian[1])
        else:
            self.cartesian = (value, self.cartesian[1], self.cartesian[2])
    @property
    def y(self) -> Real:
        """The point's cartesian y-coordinate."""
        return self.cartesian[1]
    @y.setter
    def y(self, value: Real) -> None:
        if len(self) == 2:
            self.cartesian = (self.cartesian[0], value)
        else:
            self.cartesian = (self.cartesian[0], value, self.cartesian[2])
    @property
    def z(self) -> Real:
        """The point's cartesian z-coordinate. Turns a 2D point 3D if set.
        
        :raises IndexError: When the getter is called on a 2D point.
        """
        return self.cartesian[2]
    @z.setter
    def z(self, value: Real) -> None:
        self.cartesian = (self.cartesian[0], self.cartesian[1], value)
    # Polar/Spherical Coordinates
    @property
    def polar(self) -> tuple[Real]:
        """The polar coordinates of the point (r, phi). Azimuth angle is and 
        must be in radians.
        
        :raises ValueError: When called if the point is 3D.
        """
        return trig.cartesian_to_polar(self.cartesian)
    @polar.setter
    def polar(self, value: tuple[Real]) -> None:
        self.cartesian = trig.polar_to_cartesian(value)
    @property
    def spherical(self) -> tuple[Real]:
        """The spherical coordinates (r, phi, theta) of the point. Azimuth 
        and inclination angles are and must be in radians.
        
        :raises ValueError: When called if the point is 2D.
        """
        return trig.cartesian_to_spherical(self.cartesian)
    @spherical.setter
    def spherical(self, value: tuple[Real]) -> None:
        self.cartesian = trig.spherical_to_cartesian(value)
    @property
    def r(self) -> Real:
        """The polar/spherical radial distance coordinate of the point.
        
        :raises ValueError: If r < 0, r is NaN, r == 0 and phi is NaN, or r != 0 
            and phi and theta are NaNs.
        """
        return trig.r_of_cartesian(self.cartesian)
    @r.setter
    def r(self, value: Real) -> None:
        if value < 0:
            raise ValueError("r cannot be less than zero")
        if math.isnan(value):
            raise ValueError("r cannot be NaN")
        if len(self) == 2: # Polar
            if value == 0:
                self.polar = (0, math.nan)
            elif not math.isnan(self.phi):
                self.polar = (value, self.phi)
            else:
                raise ValueError("r must be 0 if phi is NaN")
        else: # Spherical (or invalid)
            if value == 0:
                self.spherical = (value, math.nan, math.nan)
            elif not math.isnan(self.phi) and not math.isnan(self.theta):
                self.spherical = (value, self.phi, self.theta)
            else:
                raise ValueError("r must be 0 if phi and theta are NaN")
    @property
    def phi(self) -> Real:
        """The polar/spherical azimuth angle of the point in radians.
        
        :raises ValueError: If phi is NaN and r != 0, r == 0 and phi is not NaN, 
            or if phi is NaN and theta is not NaN.
        """
        return trig.phi_of_cartesian(self.cartesian)
    @phi.setter
    def phi(self, value: Real) -> None:
        if len(self) == 2: # Polar
            if self.r != 0 and math.isnan(value):
                raise ValueError("phi cannot be NaN if r is non-zero")
            if self.r == 0 and not math.isnan(value):
                raise ValueError("phi can only be NaN if r is zero")
            self.polar = (self.r, value)
        else:
            # Spherical (or invalid)
            if math.isnan(self.theta) and not math.isnan(value): # AKA r == 0
                raise ValueError("Phi can only be NaN if theta is also NaN")
            self.spherical = (self.r, value, self.theta)
    @property
    def theta(self) -> Real:
        """The spherical inclination angle of the point in radians.
        
        :raises ValueError: If phi is NaN and theta is not 0, pi or NaN.
        :raises IndexError: When the getter is called on a 2D point.
        """
        return trig.theta_of_cartesian(self.cartesian)
    @theta.setter
    def theta(self, value: Real) -> None:
        if math.isnan(self.phi) and value not in [0, math.pi, math.nan]:
            raise ValueError("theta must be NaN, 0, or pi if phi is NaN")
        self.spherical = (self.r, self.phi, value)
    # Public Methods #
    def copy(self) -> Point:
        """Returns a copy of the Point at the same position, different uid."""
        return Point(self.cartesian)
    def get_reference(self, reference: ConstraintReference) -> Self:
        """Returns reference geometry for use in external modules like 
        constraints.
        
        :param reference: A ConstraintReference enumeration value applicable to 
            Points. See :attr:`Point.REFERENCES`.
        :returns: The geometry corresponding to the reference.
        :raises ValueError: When provided an unrecognized ConstraintReference.
        """
        if reference == ConstraintReference.CORE:
            return self
        raise ValueError(f"Unrecognized ConstraintReference {reference}")
    def get_all_references(self) -> tuple[ConstraintReference]:
        """Returns all ConstraintReferences applicable to Points."""
        return self.REFERENCES
    def phi_degrees(self) -> Real:
        """Returns the polar/spherical azimuth angle of the Point in degrees."""
        return math.degrees(self.phi)
    def theta_degrees(self) -> Real:
        """Returns the spherical inclination angle of the point in degrees."""
        return math.degrees(self.theta)
    def set_phi_degrees(self, value: Real) -> Self:
        """Sets the polar/spherical azimuth coordinate of the point using a 
        value in degrees. Returns the updated point.
        """
        self.phi = math.radians(value)
        return self
    def set_theta_degrees(self, value: Real) -> Self:
        """Sets the spherical inclination coordinate of the point using a 
        value in degrees. Returns the updated point.
        """
        self.theta = math.radians(value)
        return self
    def update(self, other: Point) -> Self:
        """Updates the point to match the position of another point."""
        self.cartesian = other.cartesian
        return self
    def vector(self, vertical: bool=True) -> np.ndarray:
        """Returns a numpy vector of the point's cartesian.
        
        :param vertical: Sets whether to return a vertical vector. Defaults True.
        :returns: The cartesian position vector of the point.
        """
        array = np.array(self)
        if vertical:
            return array.reshape(len(self.cartesian), 1)
        return array
    # Private Methods
    @staticmethod
    def _parse_components(*components: Real | Sequence[Real] | np.ndarray
                          ) -> tuple[Real | Real | Real] | tuple[Real | Real]:
        """Returns vector component inputs as a tuple of Reals."""
        if len(components) not in [1, 2, 3]:
            raise ValueError("components must be 1 to 3 arguments")
        if len(components) == 1:
            vector = components[0]
            if isinstance(vector, np.ndarray):
                if not is_geometry_vector(vector):
                    raise ValueError("NumPy vectors must be 2 or 3 elements")
                return tuple(float(c.squeeze()) for c in vector)
            if isinstance(vector, Sequence):
                return tuple(vector)
            raise TypeError(f"Expected ndarray/Sequence, got {components}")
        if any(isinstance(c, Real) for c in components):
            return tuple(components)
        raise TypeError(f"Expected Real components, got {components}")
    # Python Dunders #
    def __add__(self, other) -> tuple[Real]:
        """Returns the addition of two point's cartesian position vectors."""
        if isinstance(other, (np.ndarray, tuple)):
            if len(self) == len(other):
                numpy_array = np.array(self) + np.array(other)
                return tuple(map(lambda x: x.item(), numpy_array))
            raise ValueError("Cannot add 2D elements to/from 3D elements")
        if isinstance(other, Point):
            if len(self) == len(other):
                numpy_array = np.array(self) + np.array(other)
                return tuple(map(lambda x: x.item(), numpy_array))
            raise ValueError("Cannot add 2D points to/from 3D points")
        return NotImplemented
    def __conform__(self, protocol: PrepareProtocol):
        """Conforms the point's values for storage in sqlite."""
        if protocol is PrepareProtocol:
            return ";".join(map(str, self.cartesian))
        raise TypeError(f"Expected sqlite3.PrepareProtocol, got {protocol}")
    def __sub__(self, other) -> tuple[Real]:
        """Returns the subtraction of two point's cartesian position vectors as
        a tuple"""
        if isinstance(other, Point):
            if len(self) == len(other):
                numpy_array = np.array(self) - np.array(other)
                return tuple(map(lambda x: x.item(), numpy_array))
            raise ValueError("Cannot subtract 2D points to/from 3D points")
        return NotImplemented
    def __copy__(self) -> Point:
        """Returns a copy of the point that has the same coordinates, but no 
        assigned uid. Can be used with the python copy module.
        """
        return self.copy()
    def __getitem__(self, item: int) -> Real:
        """Returns the cartesian coordinates when subscripted. 0 returns x, 1 
        returns y, 2 returns z.
        """
        return self.cartesian[item]
    def __eq__(self, other: Point) -> bool:
        """Rich comparison for point equality that allows for points to be 
        directly compared with ==.
        
        :param other: The point to compare self to.
        :returns: Whether the cartesian tuples of the points are equal.
        :raises ValueError: When comparing Points of differing dimensions.
        """
        if isinstance(other, Point):
            if len(self) == len(other):
                return isclose(tuple(self), tuple(other))
            raise ValueError("Points must be the same dimension")
        return NotImplemented
    def __len__(self) -> int:
        """Returns the dimension of the Point, 2 or 3."""
        return len(self.cartesian)
    def __iter__(self):
        """Iterator function to allow the point's cartesian position to be 
        output when the point is fed to a list or tuple like function.
        """
        self._iter_index = 0
        return self
    def __next__(self) -> float:
        """Next function to allow the point's cartesian position to be 
        output when the point is fed to a list or tuple like function.
        """
        if self._iter_index < len(self.cartesian):
            i = self._iter_index
            self._iter_index += 1
            return self.cartesian[i]
        raise StopIteration
    def __str__(self) -> str:
        pt_strs = []
        for component in self.cartesian:
            if isclose0(component):
                pt_strs.append("0")
            else:
                pt_strs.append(f"{component:g}")
        point_str = ",".join(pt_strs)
        prefix = super().__str__()
        return f"{prefix}({point_str})>"
    # NumPy Dunders #
    def __array__(self, dtype=None, copy=None) -> np.ndarray:
        """Array function to allow the point to be fed into a numpy array 
        function and return a horizontal numpy array.
        
        :raises ValueError: When copy is set to False. copy argument only 
            included for numpy compatibility.
        """
        array = np.array(list(self))
        if copy is not None and not copy:
            raise ValueError("pancad Point cannot return the original")
        if dtype:
            return array.astype(dtype)
        return array
