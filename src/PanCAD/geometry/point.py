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
    translation.
    
    :param cartesian: The cartesian coordinate (x, y, z) of the point.
    :param uid: The unique ID of the point for interoperable CAD 
                identitification.
    :param unit: The unit of the point's length values.
    """
    def __init__(self,
                 cartesian: tuple[float, float, float] | np.ndarray = (None, None, None),
                 *, uid: str = None, unit: str = None):
        """Constructor method"""
        self.uid = uid if uid else None
        
        if isinstance(cartesian, tuple):
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
        if len(self.cartesian) == 2:
            return (self.r, self.phi)
        elif len(self.cartesian) == 3:
            raise ValueError("Point must be 2D to return a polar coordinate, "
                             + "use spherical for 3D points")
        else:
            raise ValueError(f"Point cartesian {self.cartesian} is already"
                             + "invalid, must be 2D or 3D to operate")
    
    @property
    def spherical(self) -> tuple[float, float, float]:
        """The spherical coordinate (r, phi, theta) of the point. Azimuth 
        and inclination angles are in radians.
        
        :getter: Returns the spherical coordinate (r, phi, theta). Will error 
                 if the point is 2D.
        :setter: Sets the spherical coordinate (r, phi, theta). Will error if 
                 the point is 2D.
        """
        if len(self.cartesian) == 3:
            return (self.r, self.phi, self.theta)
        elif len(self.cartesian) == 2:
            raise ValueError("Point must be 3D to return a spherical coordinate,"
                             + " use polar for 2D points")
        else:
            raise ValueError(f"Point cartesian {self.cartesian} is already"
                             + "invalid, must be 2D or 3D to operate")
    
    @property
    def r(self) -> float:
        """The polar/spherical radial coordinate of the point.
        
        :getter: Returns the radial coordinate of the point.
        :setter: Sets the radial coordinate of the point. Checks the value 
                 for polar or spherical coordinate validity and will error if it 
                 is violated.
        """
        if len(self.cartesian) == 2:
            return math.hypot(self.x, self.y)
        elif len(self.cartesian) == 3:
            return math.hypot(self.x, self.y, self.z)
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
        if self.x == 0 and self.y == 0:
            return math.nan
        else:
            return math.atan2(self.y, self.x)
    
    @property
    def theta(self) -> float:
        """The spherical inclination coordinate of the point in 
        radians.
        
        :getter: Returns the inclination coordinate of the point.
        :setter: Sets the inclination coordinate of the point. Checks the value 
                 for polar or spherical coordinate validity and will error if 
                 it is violated.
        """
        if self.z == 0 and math.hypot(self.x, self.y) != 0:
            return math.pi/2
        elif self.x == 0 and self.y == 0 and self.z == 0:
            return math.nan
        elif self.z > 0:
            return math.atan(math.hypot(self.x, self.y)/self.z)
        elif self.z < 0:
            return math.pi + math.atan(math.hypot(self.x, self.y)/self.z)
        else:
            raise ValueError(f"Unhandled exception, cartesian: {self.cartesian}")
    
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
        if len(self.cartesian) == 2:
            self.cartesian = (value, self.cartesian[1])
        else:
            self.cartesian = (value, self.cartesian[1], self.cartesian[2])
    
    @y.setter
    def y(self, value: float) -> None:
        if len(self.cartesian) == 2:
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
        
        if len(self.cartesian) == 2: # Polar
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
        if len(value) == 2:
            r, phi = value
            if r == 0 and math.isnan(phi):
                self.cartesian = (0, 0)
            elif r < 0:
                raise ValueError(f"r cannot be less than zero: {r}")
            elif math.isnan(phi):
                raise ValueError("phi cannot be NaN if r is non-zero")
            else:
                self.cartesian = (r * math.cos(phi), r * math.sin(phi))
        else:
            raise ValueError("Point must be 2D to set a polar coordinate, "
                             + "use Point.spherical for 3D points")
    
    @phi.setter
    def phi(self, value: float) -> None:
        if len(self.cartesian) == 2: # Polar
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
        if len(value) == 3:
            r, phi, theta = value
            if r == 0 and math.isnan(phi) and math.isnan(theta):
                self.cartesian = (0, 0, 0)
            elif r > 0 and not math.isnan(phi) and (0 <= theta <= math.pi):
                self.cartesian = (
                    r * math.sin(theta) * math.cos(phi),
                    r * math.sin(theta) * math.sin(phi),
                    r * math.cos(theta)
                )
            elif r > 0 and math.isnan(phi) and theta == 0:
                self.cartesian = (0, 0, r)
            elif r > 0 and math.isnan(phi) and theta == math.pi:
                self.cartesian = (0, 0, -r)
            elif r < 0:
                raise ValueError(f"r cannot be less than zero: {r}")
            elif not math.isnan(theta) and (not 0 <= theta <= math.pi):
                raise ValueError(f"theta must be between 0 and pi, value: {theta}")
            elif math.isnan(phi) and math.isnan(theta):
                raise ValueError(f"r value {r} cannot be non-zero if phi and "
                                 + "theta are NaN.")
            elif math.isnan(theta):
                raise ValueError("Theta cannot be NaN if r is non-zero")
            elif math.isnan(phi) and (theta != 0 or theta != math.pi):
                raise ValueError("If phi is NaN, theta must be pi/2")
                
        elif len(value) == 2:
            raise ValueError("Point must be 3D to set a spherical coordinate, "
                             + "use Point.polar for 2D points")
        else:
            raise ValueError(f"Invalid tuple length {len(value)}, must be 3 to"
                             + "set as a spherical coordinate")
    
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
    def __eq__(self, other: Point) -> bool:
        """Rich comparison for point equality that allows for points to be 
        directly compared with ==.
        
        :param other: The point to compare self to.
        :returns: Whether the tuples of the points are equal.
        """
        if isinstance(other, Point):
            return tuple(self) == tuple(other)
        else:
            return NotImplemented
    
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
    
    def __str__(self) -> str:
        """String function to output the point's description and cartesian 
        position when the point is fed to the str() function"""
        return f"PanCAD Point at cartesian {self.cartesian}"
    
    # NumPy Dunders #
    def __array__(self, dtype=None, copy=None) -> np.ndarray:
        """Array function to allow the point to be fed into a numpy array 
        function and return a horizontal numpy array."""
        return np.array(list(self))