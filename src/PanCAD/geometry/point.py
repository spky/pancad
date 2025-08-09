"""A module providing a class to represent points in all CAD programs,  
graphics, and other geometry use cases.
"""
from __future__ import annotations

import math
from functools import partial, singledispatchmethod
from numbers import Real
from typing import overload, NoReturn, Self

import numpy as np

from PanCAD.geometry.abstract_geometry import AbstractGeometry
from PanCAD.utils import trigonometry as trig, comparison
from PanCAD.utils.pancad_types import VectorLike
from PanCAD.geometry.constants import ConstraintReference

isclose = partial(comparison.isclose, nan_equal=False)
isclose0 = partial(comparison.isclose, value_b=0, nan_equal=False)

class Point(AbstractGeometry):
    """A class representing points in 2D and 3D space. Point can return its 
    position in cartesian, spherical, or polar coordinates. Point's __init__ 
    function can only take cartesian coordinates, so either use one of its class 
    functions or initialize it with no arguments and modify one of its 
    coordinate system specific properties if another coordinate system is 
    desired. 
    
    :param cartesian: The cartesian coordinate (x, y, z) of the point. Treated 
        as x if given as a real.
    :param y: The cartesian y coordinate of the point. Can only be given if 
        cartesian is given as a real.
    :param z: The cartesian z coordinate of the point. Can only be given if 
        cartesian and y are given as reals.
    :param uid: The unique ID of the point for interoperable CAD identification.
    :param unit: The unit of the point's length values.
    """
    
    REFERENCES = (ConstraintReference.CORE,)
    """All relevant ConstraintReferences for Point."""
    
    @overload
    def __init__(self,
                 cartesian: tuple[Real],
                 *,
                 uid: str=None,
                 unit: str=None) -> None: ...
    
    @overload
    def __init__(self,
                 cartesian: np.ndarray,
                 *,
                 uid: str=None,
                 unit: str=None) -> None: ...
    
    @overload
    def __init__(self,
                 cartesian: Real,
                 y: Real,
                 *,
                 uid: str=None,
                 unit: str=None) -> None: ...
    
    @overload
    def __init__(self,
                 cartesian: Real,
                 y: Real,
                 z:Real,
                 *,
                 uid: str=None,
                 unit: str=None) -> None: ...
    
    @overload
    def __init__(self,
                 *,
                 uid: str=None,
                 unit: str=None) -> None: ...
    
    def __init__(self, cartesian=None, y=None, z=None, *, uid=None, unit=None):
        self.uid = uid
        # self._references = (ConstraintReference.CORE,)
        
        if all([isinstance(n, Real) for n in [cartesian, y, z]]):
            self.cartesian = (cartesian, y, z)
        elif (isinstance(cartesian, Real)
                 and isinstance(y, Real)
                 and z is None):
            self.cartesian = (cartesian, y)
        elif (isinstance(cartesian, (tuple, np.ndarray))
                 and (y is not None or z is not None)):
            raise ValueError(f"Cartesian {cartesian} can not be given as a"
                             + f" non-float/int if y and z are not None."
                             + f" y value: {y}, z value: {z}")
        elif isinstance(cartesian, tuple):
            self.cartesian = cartesian
        elif isinstance(cartesian, np.ndarray):
            # Converts numpy array to a tuple of floats
            if trig.is_geometry_vector(cartesian):
                cartesian = [
                    float(coordinate.squeeze()) for coordinate in cartesian
                ]
                self.cartesian = tuple(cartesian)
            else:
                raise ValueError("NumPy arrays must be 2 or 3 elements in a"
                                 + " single dimension to initialize a point")
        else:
            self.cartesian = (None, None, None)
        self.unit = unit if unit else None
    
    # Class Methods #
    @singledispatchmethod
    @classmethod
    def from_polar(cls, arg, uid: str=None, unit: str=None) -> NoReturn:
        """Initializes a point from polar coordinates.
        
        :param vector: A 2 long iterable of real numbers representing the radius 
            and azimuth angle. Azimuth must be radians.
        :param r: The radius of a polar coordinate.
        :param phi: The azimuth angle of a polar coordinate in radians.
        :param uid: Unique ID of the Point.
        :param unit: The unit of the point's length values.
        :returns: A new Point at the polar coordinate.
        """
        raise NotImplementedError(f"Unsupported 1st type {arg.__class__}")
    
    @from_polar.register
    @classmethod
    def _from_polar_vector(cls,
                           vector: VectorLike,
                           uid: str=None,
                           unit: str=None) -> Self:
        return cls(trig.polar_to_cartesian(vector), uid=uid, unit=unit)
    
    @from_polar.register
    @classmethod
    def _from_polar_r_phi(cls,
                          r: Real,
                          phi: Real,
                          uid: str=None,
                          unit: str=None) -> Self:
        return cls(trig.polar_to_cartesian((r, phi)), uid=uid, unit=unit)
    
    @singledispatchmethod
    @classmethod
    def from_spherical(cls, arg, *, uid: str=None, unit: str=None) -> NoReturn:
        """Initializes a point from spherical coordinates.
        
        :param vector: A 3 long iterable of reals representing the radius, 
            azimuth angle, and inclination angle. Azimuth and inclination must 
            be in radians.
        :param r: The radius of a spherical coordinate.
        :param phi: The azimuth angle in radians.
        :param theta: The inclination angle in radians.
        :param uid: Unique ID of the Point.
        :param unit: The unit of the point's length values.
        :returns: A new Point at the spherical coordinate.
        """
        raise NotImplementedError(f"Unsupported 1st type {arg.__class__}")
    
    @from_spherical.register
    @classmethod
    def _from_spherical_vector(cls,
                               vector: VectorLike,
                               *,
                               uid: str=None,
                               unit: str=None) -> Self:
        return cls(trig.spherical_to_cartesian(vector), uid=uid, unit=unit)
    
    @from_spherical.register
    @classmethod
    def _from_spherical_r_phi_theta(cls,
                                    r: Real,
                                    phi: Real,
                                    theta: Real,
                                    *,
                                    uid: str=None,
                                    unit: str=None) -> Self:
        return cls(trig.spherical_to_cartesian((r, phi, theta)),
                   uid=uid, unit=unit)
    
    # Getters #
    @property
    def uid(self) -> str:
        """The unique id of the point.
        
        :getter: Returns the unique id.
        :setter: Sets the unique id.
        """
        return self._uid
    
    # Cartesian Coordinates #
    @property
    def cartesian(self) -> tuple[Real]:
        """The cartesian coordinates (x, y) or(x, y, z) of the point.
        
        :getter: Returns the cartesian coordinate of the point as a 
                 tuple.
        :setter: Sets the cartesian coordinate of the point as a 
                 tuple. Checks that the tuple has 2 or 3 elements.
        """
        return self._cartesian
    
    @property
    def x(self) -> Real:
        """The cartesian x-coordinate of the point.
        
        :getter: Gets the x value of the cartesian tuple.
        :setter: Sets the x value of the cartesian tuple.
        """
        return self.cartesian[0]
    
    @property
    def y(self) -> Real:
        """The cartesian y-coordinate of the point.
        
        :getter: Gets the y value of the cartesian tuple.
        :setter: Sets the y value of the cartesian tuple.
        """
        return self.cartesian[1]
    
    @property
    def z(self) -> Real:
        """The cartesian z-coordinate of the point.
        
        :getter: Gets the z value of the cartesian tuple. Will error if the 
                 point is 2D.
        :setter: Sets the z value of the cartesian tuple. Will turn a 2D 
                 point into a 3D point if it was not already one.
        """
        return self.cartesian[2]
    
    # Polar/Spherical Coordinates
    @property
    def polar(self) -> tuple[Real]:
        """The polar coordinates of the point (r, phi). Azimuth angle is and 
        must be in radians.
        
        :getter: Returns the polar coordinates. Will raise a ValueError 
            if the point is 3D.
        :setter: Sets the polar coordinates. Will raise a ValueError if 
            the point is 3D.
        """
        return trig.cartesian_to_polar(self.cartesian)
    
    @property
    def spherical(self) -> tuple[Real]:
        """The spherical coordinates (r, phi, theta) of the point. Azimuth 
        and inclination angles are and must be in radians.
        
        :getter: Returns the spherical coordinates. Will raise a ValueError if 
            the point is 2D.
        :setter: Sets the spherical coordinates. Will raise a ValueError if the 
            point is 2D.
        """
        return trig.cartesian_to_spherical(self.cartesian)
    
    @property
    def r(self) -> Real:
        """The polar/spherical radial distance coordinate of the point.
        
        :getter: Returns the radial coordinate of the point.
        :setter: Sets the radial coordinate of the point.
        """
        return trig.r_of_cartesian(self.cartesian)
    
    @property
    def phi(self) -> Real:
        """The polar/spherical azimuth angle of the point in radians.
        
        :getter: Returns the azimuth angle of the point.
        :setter: Sets the azimuth angle of the point.
        """
        return trig.phi_of_cartesian(self.cartesian)
    
    @property
    def theta(self) -> Real:
        """The spherical inclination angle of the point in radians.
        
        :getter: Returns the inclination angle of the point.
        :setter: Sets the inclination angle of the point.
        """
        return trig.theta_of_cartesian(self.cartesian)
    
    # Setters #
    @cartesian.setter
    def cartesian(self, value: tuple[Real, Real, Real]) -> None:
        if len(value) == 2 or len(value) == 3:
            self._cartesian = value
        else:
            raise ValueError(f"Given cartesian {value} needs 2 or 3 elements")
    
    @uid.setter
    def uid(self, uid: str) -> None:
        self._uid = uid
    
    @x.setter
    def x(self, value: Real) -> None:
        if len(self) == 2:
            self.cartesian = (value, self.cartesian[1])
        else:
            self.cartesian = (value, self.cartesian[1], self.cartesian[2])
    
    @y.setter
    def y(self, value: Real) -> None:
        if len(self) == 2:
            self.cartesian = (self.cartesian[0], value)
        else:
            self.cartesian = (self.cartesian[0], value, self.cartesian[2])
    
    @z.setter
    def z(self, value: Real) -> None:
        self.cartesian = (self.cartesian[0], self.cartesian[1], value)
    
    @r.setter
    def r(self, value: Real) -> None:
        if value < 0:
            raise ValueError(f"r cannot be less than zero: {value}")
        elif math.isnan(value):
            raise ValueError(f"r cannot be NaN")
        
        if len(self) == 2: # Polar
            if value == 0:
                self.polar = (0, math.nan)
            elif not math.isnan(self.phi):
                self.polar = (value, self.phi)
            else:
                raise ValueError("Cannot set r to anything except zero if phi"
                                 + " is NaN, change phi or both simultaneously"
                                 + " using polar")
        else: # Spherical (or invalid)
            if value == 0:
                self.spherical = (value, math.nan, math.nan)
            elif not math.isnan(self.phi) and not math.isnan(self.theta):
                self.spherical = (value, self.phi, self.theta)
            else:
                raise ValueError("Cannot set r to anything except zero if phi"
                                 + " and theta are NaN, change phi/theta or all"
                                 + " 3 simultaneously using spherical")
    
    @polar.setter
    def polar(self, value: tuple[Real]) -> None:
        self.cartesian = trig.polar_to_cartesian(value)
    
    @phi.setter
    def phi(self, value: Real) -> None:
        if len(self) == 2: # Polar
            if self.r != 0 and math.isnan(value):
                raise ValueError("Cannot set phi to NaN if r is non-zero")
            elif self.r == 0 and not math.isnan(value):
                raise ValueError("phi can only be NaN if r is zero")
            else:
                self.polar = (self.r, value)
        else: 
            # Spherical (or invalid)
            if math.isnan(self.theta) and not math.isnan(value): # AKA r == 0
                raise ValueError("Phi can only be NaN if theta is NaN, change"
                                 + " theta or phi and theta simultaneously"
                                 + " using spherical")
            else:
                self.spherical = (self.r, value, self.theta)
    
    @spherical.setter
    def spherical(self, value: tuple[Real]) -> None:
        self.cartesian = trig.spherical_to_cartesian(value)
    
    @theta.setter
    def theta(self, value: Real) -> None:
        if (math.isnan(self.phi)
                and value != 0 and value != math.pi and not math.isnan(value)):
            raise ValueError("Cannot set theta to anything except NaN, 0, or pi"
                             " if phi = NaN, change phi or both simultaneously")
        else:
            self.spherical = (self.r, self.phi, value)
    
    # Public Methods #
    def copy(self) -> Point:
        """Returns a copy of the Point.
        
        :returns: A new Point at the same position as this point.
        """
        return self.__copy__()
    
    def get_reference(self, reference: ConstraintReference) -> Self:
        """Returns reference geometry for use in external modules like 
        constraints.
        
        :param reference: A ConstraintReference enumeration value. Points only 
            have a core reference, so any other value will cause an error.
        :returns: The Point itself or an error.
        """
        match reference:
            case ConstraintReference.CORE:
                return self
            case _:
                raise ValueError(f"{self.__class__}s do not have any"
                                 f" {reference.name} reference geometry")
    
    def get_all_references(self) -> tuple[ConstraintReference]:
        """Returns all ConstraintReferences applicable to Points.
        
        :returns: All ConstraintReferences applicable to Points.
        """
        return self.REFERENCES
    
    def phi_degrees(self) -> Real:
        """Returns the polar/spherical azimuth angle of the Point in degrees.
        
        :returns: The azimuth coordinate in degrees.
        """
        return math.degrees(self.phi)
    
    def theta_degrees(self) -> Real:
        """Returns the spherical inclination angle of the point in degrees.
        
        :returns: The inclination coordinate in degrees.
        """
        return math.degrees(self.theta)
    
    def set_phi_degrees(self, value: Real) -> Self:
        """Sets the polar/spherical azimuth coordinate of the point using a 
        value in degrees.
        
        :param value: The azimuth coordinate in degrees.
        :returns: A reference to the updated Point.
        """
        self.phi = math.radians(value)
        return self
    
    def set_theta_degrees(self, value: Real) -> Self:
        """Sets the spherical inclination coordinate of the point using a 
        value in degrees.
        
        :param value: The inclination coordinate in degrees.
        :returns: A reference to the updated Point.
        """
        self.theta = math.radians(value)
        return self
    
    def update(self, other: Point) -> Self:
        """Updates the point to match the position of another point.
        
        :param other: The point to update the calling Point's position to.
        :returns: A reference to the updated Point.
        """
        self.cartesian = other.cartesian
        return self
    
    def vector(self, vertical: bool=True) -> np.ndarray:
        """Returns a numpy vector of the point's cartesian.
        
        :param vertical: Sets whether the vector returns as a vertical or 
            horizontal vector. Defaults to True so that the function returns a 
            vertical vector.
        :returns: The cartesian position vector of the point.
        """
        array = np.array(self)
        if vertical:
            return array.reshape(len(self.cartesian), 1)
        else:
            return array
    
    # Python Dunders #
    def __add__(self, other) -> tuple[Real]:
        """Returns the addition of two point's cartesian position vectors as a 
        tuple.
        """
        if isinstance(other, (np.ndarray, tuple)):
            if len(self) == len(other):
                print(self)
                numpy_array = np.array(self) + np.array(other)
                return tuple(map(lambda x: x.item(), numpy_array))
            else:
                raise ValueError("Cannot add 2D points/arrays to/from 3D"
                                 " point/arrays")
        elif isinstance(other, Point):
            if len(self) == len(other):
                numpy_array = np.array(self) + np.array(other)
                return tuple(map(lambda x: x.item(), numpy_array))
            else:
                raise ValueError("Cannot add 2D points to/from 3D points")
        else:
            return NotImplemented
    
    def __sub__(self, other) -> tuple[Real]:
        """Returns the subtraction of two point's cartesian position vectors as
        a tuple"""
        if isinstance(other, Point):
            if len(self) == len(other):
                numpy_array = np.array(self) - np.array(other)
                return tuple(map(lambda x: x.item(), numpy_array))
            else:
                raise ValueError("Cannot subtract 2D points to/from 3D points")
        else:
            return NotImplemented
    
    def __copy__(self) -> Point:
        """Returns a copy of the point that has the same coordinates, but no 
        assigned uid. Can be used with the python copy module.
        """
        return Point(self.cartesian)
    
    def __getitem__(self, item: int) -> Real:
        """Returns the cartesian coordinates when subscripted. 0 returns x, 1 
        returns y, 2 returns z.
        """
        return self.cartesian[item]
    
    def __eq__(self, other: Point) -> bool:
        """Rich comparison for point equality that allows for points to be 
        directly compared with ==. Note: A point at (0,0) and a point at (0,0,0)
        will not be found equal since the first's z coordinate is not defined.
        
        :param other: The point to compare self to.
        :returns: Whether the cartesian tuples of the points are equal.
        """
        if isinstance(other, Point):
            if len(self) == len(other):
                return isclose(tuple(self), tuple(other))
            else:
                raise ValueError("Can only compare points with the same"
                                 " number of dimensions")
        else:
            return NotImplemented
    
    def __len__(self) -> int:
        """Returns the length of the cartesian tuple, indicating the point's 
        number of dimnesions.
        """
        return len(self.cartesian)
    
    def __iter__(self):
        """Iterator function to allow the point's cartesian position to be 
        output when the point is fed to a list or tuple like function.
        """
        self.dimension = 0
        return self
    
    def __next__(self) -> float:
        """Next function to allow the point's cartesian position to be 
        output when the point is fed to a list or tuple like function.
        """
        if self.dimension < len(self.cartesian):
            i = self.dimension
            self.dimension += 1
            return self.cartesian[i]
        else:
            raise StopIteration
    
    def __repr__(self) -> str:
        """Returns the short string representation of the point."""
        pt_strs = []
        for i in range(0, len(self.cartesian)):
            if isclose0(self.cartesian[i]):
                pt_strs.append("0")
            else:
                pt_strs.append("{:g}".format(self.cartesian[i]))
        point_str = ",".join(pt_strs)
        return f"<PanCADPoint'{self.uid}'({point_str})>"
    
    def __str__(self) -> str:
        pt_strs = []
        for i in range(0, len(self.cartesian)):
            if isclose0(self.cartesian[i]):
                pt_strs.append("0")
            else:
                pt_strs.append("{:g}".format(self.cartesian[i]))
        point_str = ",".join(pt_strs)
        return f"<PanCADPoint'{self.uid}'({point_str})>"
    
    # NumPy Dunders #
    def __array__(self, dtype=None, copy=None) -> np.ndarray:
        """Array function to allow the point to be fed into a numpy array 
        function and return a horizontal numpy array."""
        return np.array(list(self))