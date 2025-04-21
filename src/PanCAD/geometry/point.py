"""A module providing a class to represent points in all CAD programs,  
graphics, and other geometry use cases.
"""
from __future__ import annotations

import math

import numpy as np

from PanCAD.utils import trigonometry as trig

class Point:
    """A class representing points in 2D and 3D space. Point can freely 
    translate its position between coordinate systems for easy position 
    translation. Point's __init__ function can only take cartesian coordinates, 
    so either use one of its class functions or initialize it with no 
    arguments and modify one of its coordinate system specific properties if 
    another coordinate system is desired.
    
    :param cartesian: The cartesian coordinate (x, y, z) of the point. If a
                      float or int is given instead, y needs to also be 
                      initialized.
    :param y: The cartesian y coordinate of the point. Can only be given if 
              cartesian is given as a float or int.
    :param z: The cartesian z coordinate of the point. Can only be given if 
              cartesian and y are given as floats or ints.
    :param uid: The unique ID of the point for interoperable CAD 
                identification.
    :param unit: The unit of the point's length values.
    """
    
    relative_tolerance = 1e-9
    absolute_tolerance = 1e-9
    
    
    def __init__(self, cartesian: (tuple[float, float, float]
                                   | np.ndarray | float) = None,
                 y: float = None, z: float = None,
                 *, uid: str = None, unit: str = None):
        """Constructor method"""
        self.uid = uid
        
        if (
               isinstance(cartesian, (int, float))
               and isinstance(y, (int, float))
               and isinstance(z, (int, float))
            ):
            self.cartesian = (cartesian, y, z)
        elif (
                 isinstance(cartesian, (int, float))
                 and isinstance(y, (int, float))
                 and z is None):
            self.cartesian = (cartesian, y)
        elif (
                 isinstance(cartesian, (tuple, np.ndarray))
                 and (y is not None or z is not None)
              ):
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
    
    # Getters #
    @property
    def uid(self) -> str:
        """The unique id of the point.
        
        :getter: Returns the unique id as a string.
        :setter: Sets the unique id.
        """
        return self._uid
    
    # Cartesian Coordinates #
    @property
    def cartesian(self) -> tuple[float, float] | tuple[float, float, float]:
        """The cartesian coordinates (x, y) or(x, y, z) of the point.
        
        :getter: Returns the cartesian coordinate of the point as a 
                 tuple.
        :setter: Sets the cartesian coordinate of the point as a 
                 tuple. Checks that the tuple has 2 or 3 elements.
        """
        return self._cartesian
    
    @property
    def x(self) -> float:
        """The cartesian x-coordinate of the point.
        
        :getter: Gets the x value of the cartesian tuple.
        :setter: Sets the x value of the cartesian tuple.
        """
        return self.cartesian[0]
    
    @property
    def y(self) -> float:
        """The cartesian y-coordinate of the point.
        
        :getter: Gets the y value of the cartesian tuple.
        :setter: Sets the y value of the cartesian tuple.
        """
        return self.cartesian[1]
    
    @property
    def z(self) -> float:
        """The cartesian z-coordinate of the point.
        
        :getter: Gets the z value of the cartesian tuple. Will error if the 
                 point is 2D.
        :setter: Sets the z value of the cartesian tuple. Will turn a 2D 
                 point into a 3D point if it was not already one.
        """
        return self.cartesian[2]
    
    # Polar/Spherical Coordinates
    @property
    def polar(self) -> tuple[float, float]:
        """The polar coordinate of the point. Azimuth angle is in radians.
        
        :getter: Returns the polar coordinate (r, phi). Will error if the 
                 point is 3D.
        :setter: Sets the polar coordinate (r, phi). Will error if the point 
                 is 3D.
        """
        return trig.cartesian_to_polar(self.cartesian)
    
    @property
    def spherical(self) -> tuple[float, float, float]:
        """The spherical coordinate (r, phi, theta) of the point. Azimuth 
        and inclination angles are in radians.
        
        :getter: Returns the spherical coordinate (r, phi, theta). Will error 
                 if the point is 2D.
        :setter: Sets the spherical coordinate (r, phi, theta). Will error if 
                 the point is 2D.
        """
        return trig.cartesian_to_spherical(self.cartesian)
    
    @property
    def r(self) -> float:
        """The polar/spherical radial coordinate of the point.
        
        :getter: Returns the radial coordinate of the point.
        :setter: Sets the radial coordinate of the point. Checks the value 
                 for polar or spherical coordinate validity and will error if it 
                 is violated.
        """
        if len(self) == 2 or len(self) == 3:
            return trig.r_of_cartesian(self.cartesian)
        else:
            raise ValueError(f"Point cartesian {self.cartesian} is already"
                             + "invalid, must be 2D or 3D to function")
    
    @property
    def phi(self) -> float:
        """The polar/spherical azimuth coordinate of the point in 
        radians.
        
        :getter: Returns the azimuth coordinate of the point.
        :setter: Sets the azimuth coordinate of the point. Checks the value 
                 for polar or spherical coordinate validity and will error if 
                 it is violated.
        """
        return trig.phi_of_cartesian(self.cartesian)
    
    @property
    def theta(self) -> float:
        """The spherical inclination coordinate of the point in 
        radians.
        
        :getter: Returns the inclination coordinate of the point.
        :setter: Sets the inclination coordinate of the point. Checks the value 
                 for polar or spherical coordinate validity and will error if 
                 it is violated.
        """
        return trig.theta_of_cartesian(self.cartesian)
    
    # Setters #
    @cartesian.setter
    def cartesian(self, value: tuple[float, float, float]):
        if len(value) == 2 or len(value) == 3:
            self._cartesian = value
        else:
            raise ValueError(f"Given cartesian {cartesian} needs 2 or 3 elements")
    
    @uid.setter
    def uid(self, uid: str) -> None:
        self._uid = uid
    
    @x.setter
    def x(self, value: float) -> None:
        if len(self) == 2:
            self.cartesian = (value, self.cartesian[1])
        else:
            self.cartesian = (value, self.cartesian[1], self.cartesian[2])
    
    @y.setter
    def y(self, value: float) -> None:
        if len(self) == 2:
            self.cartesian = (self.cartesian[0], value)
        else:
            self.cartesian = (self.cartesian[0], value, self.cartesian[2])
    
    @z.setter
    def z(self, value: float) -> None:
        self.cartesian = (self.cartesian[0], self.cartesian[1], value)
    
    @r.setter
    def r(self, value: float) -> None:
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
    def polar(self, value: tuple[float, float]) -> None:
        self.cartesian = trig.polar_to_cartesian(value)
    
    @phi.setter
    def phi(self, value: float) -> None:
        if len(self) == 2: # Polar
            if self.r != 0 and math.isnan(value):
                raise ValueError("Cannot set phi to NaN if r is non-zero")
            elif self.r == 0 and not math.isnan(value):
                raise ValueError("phi can only be NaN if r is zero")
            else:
                self.polar = (self.r, value)
        else: # Spherical (or invalid)
            if math.isnan(self.theta) and not math.isnan(value): # AKA r == 0
                raise ValueError("Phi can only be NaN if theta is NaN, change"
                                 + " theta or phi and theta simultaneously"
                                 + " using spherical")
            else:
                self.spherical = (self.r, value, self.theta)
    
    @spherical.setter
    def spherical(self, value: tuple[float, float, float]) -> None:
        self.cartesian = trig.spherical_to_cartesian(value)
    
    @theta.setter
    def theta(self, value: float) -> None:
        if math.isnan(self.phi) and value != 0 and value != math.pi and not math.isnan(value):
            raise ValueError("Cannot set theta to anything except NaN, 0, or pi if "
                             + "phi is NaN, change phi or both simultaneously")
        else:
            self.spherical = (self.r, self.phi, value)
    
    # Public Methods #
    def phi_degrees(self) -> float:
        """Returns the polar/spherical azimuth coordinate of the point in 
        degrees.
        
        :returns: The azimuth coordinate in degrees.
        """
        return math.degrees(self.phi)
    
    def theta_degrees(self) -> float:
        """Returns the spherical inclination coordinate of the point in 
        degrees.
        
        :returns: The inclination coordinate in degrees.
        """
        return math.degrees(self.theta)
    
    def set_phi_degrees(self, value: float) -> None:
        """Sets the polar/spherical azimuth coordinate of the point using a 
        value in degrees.
        
        :param value: The azimuth coordinate in degrees.
        """
        self.phi = math.radians(value)
    
    def set_theta_degrees(self, value: float) -> None:
        """Sets the spherical inclindation coordinate of the point using a 
        value in degrees.
        
        :param value: The inclination coordinate in degrees.
        """
        self.phi = math.radians(value)
    
    def vector(self, vertical = True) -> np.ndarray:
        """Returns a numpy vector of the point's cartesian.
        
        :param vertical: Sets whether the vector returns as a vertical or 
                         horizontal vector. Defaults to returning as a 
                         vertical vector.
        :returns: The cartesian position vector of the point.
        """
        array = np.array(self)
        if vertical:
            return array.reshape(len(self.cartesian), 1)
        else:
            return array
    
    # Python Dunders #
    def __copy__(self) -> Point:
        """Returns a copy of the point that has the same coordinates, but no 
        assigned uid. Can be used with the python copy module"""
        return Point(self.cartesian)
    
    def __getitem__(self, item: int):
        """Returns the cartesian coordinates when subscripted. 0 returns x, 1 
        returns y, 2 returns z"""
        return self.cartesian[item]
    
    def __eq__(self, other: Point) -> bool:
        """Rich comparison for point equality that allows for points to be 
        directly compared with ==. Note: A point at (0,0) and a point at (0,0,0) 
        will not be found equal since the first's z coordinate is not defined.
        
        :param other: The point to compare self to.
        :returns: Whether the tuples of the points are equal.
        """
        if isinstance(other, Point):
            return trig.isclose_tuple(tuple(self), tuple(other),
                                      self.relative_tolerance,
                                      self.absolute_tolerance)
        else:
            return NotImplemented
    
    def __len__(self) -> int:
        """Returns the length of the cartesian tuple, which is equivalent to the 
        point's number of dimnesions."""
        return len(self.cartesian)
    
    def __iter__(self):
        """Iterator function to allow the point's cartesian position to be 
        output when the point is fed to a list or tuple like function."""
        self.dimension = 0
        return self
    
    def __next__(self) -> float:
        """Next function to allow the point's cartesian position to be 
        output when the point is fed to a list or tuple like function."""
        if self.dimension < len(self.cartesian):
            i = self.dimension
            self.dimension += 1
            return self.cartesian[i]
        else:
            raise StopIteration
    
    def __repr__(self) -> str:
        return f"PanCAD_Point{self.cartesian}"
    
    def __str__(self) -> str:
        """String function to output the point's description and cartesian 
        position when the point is fed to the str() function"""
        return f"PanCAD Point at cartesian {self.cartesian}"
    
    # NumPy Dunders #
    def __array__(self, dtype=None, copy=None) -> np.ndarray:
        """Array function to allow the point to be fed into a numpy array 
        function and return a horizontal numpy array."""
        return np.array(list(self))