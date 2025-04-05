"""A module providing a class to represent points in all CAD programs, 
graphics, and other geometry use cases.
"""

import math

import numpy as np



class Point:
    
    def __init__(self, position: tuple[float, float, float] = (None, None, None), *,
                 uid: str = None, unit: str = None):
        
        self.uid = uid if uid else None
        self.position = position if position else (None, None, None)
        self.unit = unit if unit else None
    
    # Getters #
    @property
    def uid(self) -> str:
        """Returns the unique id of the point"""
        return self._uid
    
    # Cartesian Coordinates #
    @property
    def position(self) -> tuple[float, float] | tuple[float, float, float]:
        """Returns the cartesian coordinates of the point"""
        return self._position
    
    @property
    def x(self) -> float:
        """Returns the cartesian x-coordinate of the point"""
        return self.position[0]
    
    @property
    def y(self) -> float:
        """Returns the cartesian y-coordinate of the point"""
        return self.position[1]
    
    @property
    def z(self) -> float:
        """Returns the cartesian z-coordinate of the point. Will error if 
        the point is 2D."""
        return self.position[2]
    
    # Polar/Spherical Coordinates
    @property
    def polar(self) -> tuple[float, float]:
        """Returns the polar coordinate (r, phi) of the point. Azimuth angle 
        is in radians. Will error if the point is 3D."""
        if len(self.position) == 2:
            return (self.r, self.phi)
        else:
            raise ValueError("Point must be 2D to return a polar coordinate, "
                             + "use spherical() for 3D points")
    
    @property
    def spherical(self) -> tuple[float, float, float]:
        """Returns the polar coordinate (r, phi, theta) of the point. Azimuth 
        and inclination angles are in radians. Will error if the point is 
        2D."""
        return (self.r, self.phi, self.theta)
    
    @property
    def r(self) -> float:
        """Returns the polar/spherical radial coordinate of the point"""
        if len(self.position) == 2:
            return math.hypot(self.x, self.y)
        else:
            return math.hypot(self.x, self.y, self.z)
    
    @property
    def phi(self) -> float:
        """Returns the polar/spherical azimuth coordinate of the point in 
        radians"""
        if self.x == 0 and self.y == 0:
            return math.nan
        else:
            return math.atan2(self.y, self.x)
    
    @property
    def theta(self) -> float:
        """Returns the spherical inclination coordinate of the point in 
        radians"""
        if self.z == 0 and math.hypot(self.x, self.y) != 0:
            return math.pi/2
        elif self.x == 0 and self.y == 0 and self.z == 0:
            return math.nan
        elif self.z > 0:
            return math.atan(math.hypot(self.x, self.y)/self.z)
        elif self.z < 0:
            return math.pi + math.atan(math.hypot(self.x, self.y)/self.z)
        else:
            raise ValueError(f"Unhandled exception, position: {self.position}")
    
    # Setters #
    @position.setter
    def position(self, position: tuple[float, float, float]):
        if len(position) == 2 or len(position) == 3:
            self._position = position
        else:
            raise ValueError(f"Given position {position} needs 2 or 3 elements")
    
    @uid.setter
    def uid(self, uid: str) -> None:
        self._uid = uid
    
    @x.setter
    def x(self, value: float) -> None:
        if len(self.position) == 2:
            self.position = (value, self.position[1])
        else:
            self.position = (value, self.position[1], self.position[2])
    
    @y.setter
    def y(self, value: float) -> None:
        if len(self.position) == 2:
            self.position = (self.position[0], value)
        else:
            self.position = (self.position[0], value, self.position[2])
    
    @z.setter
    def z(self, value: float) -> None:
        self.position = (self.position[0], self.position[1], value)
    
    @r.setter
    def r(self, value: float) -> None:
        if len(self.position) == 2: # Polar
            if math.isnan(self.phi) and value != 0:
                raise ValueError("Cannot set r to anything except zero if phi"
                                 + " is nan, change r or both simultaneously")
            elif math.isnan(self.phi) and value == 0:
                self.position = (0, 0)
            else:
                self.position = (
                    value * math.cos(self.phi), value * math.sin(self.phi)
                )
        else: # Spherical (or invalid)
            self.position = (
                value * math.sin(self.theta) * math.cos(self.phi),
                value * math.sin(self.theta) * math.sin(self.phi),
                value * self.cos(self.theta)
            )
    
    @phi.setter
    def phi(self, value: float) -> None:
        if len(self.position) == 2: # Polar
            if math.isnan(value) or self.r == 0:
                self.position = (0, 0)
            else:
                self.position = (
                    self.r * math.cos(value), self.r * math.sin(value)
                )
        else: # Spherical (or invalid)
            if math.isnan(value) and self.z > 0:
                self.position = (0, 0, self.r)
            elif math.isnan(value) and self.z < 0:
                self.position = (0, 0, -self.r)
            elif self.r == 0:
                self.position = (0, 0, 0)
            else:
                self.position = (
                    self.r * math.sin(self.theta) * math.cos(value),
                    self.r * math.sin(self.theta) * math.sin(value),
                    self.r * self.cos(self.theta)
                )
    
    @theta.setter
    def theta(self, value: float) -> None:
        if self.r == 0 or (math.isnan(self.phi) and math.isnan(value)):
            self.position = (0, 0, 0)
        elif math.isnan(self.phi) and abs(value) == math.pi/2:
            self.position = (0, 0, self.r * math.cos(value))
        elif math.isnan(self.phi):
            raise ValueError("Cannot set theta to anything except +/-pi/2 if "
                             + "phi is nan, change phi or both simultaneously")
        else:
            self.position = (
                self.r * math.sin(value) * math.cos(self.phi),
                self.r * math.sin(value) * math.sin(self.phi),
                self.r * math.cos(value)
            )
    
    # Public Methods #
    def phi_degrees(self) -> float:
        """Returns the polar/spherical azimuth coordinate of the point in 
        degrees."""
        return math.degrees(self.phi)
    
    def theta_degrees(self) -> float:
        """Returns the spherical inclination coordinate of the point in 
        degrees."""
        return math.degrees(self.theta)
    
    def set_phi_degrees(self, value: float) -> None:
        """Sets the polar/spherical azimuth coordinate of the point using a 
        value in degrees."""
        self.phi = math.radians(value)
    
    def set_theta_degrees(self, value: float) -> None:
        """Sets the spherical inclindation coordinate of the point using a 
        value in degrees."""
        self.phi = math.radians(value)
    
    def vector(self, vertical = True) -> np.ndarray:
        """Returns a numpy vector of the point's position"""
        array = np.array(self) 
        if vertical:
            return array.reshape(len(self.position), 1)
        else:
            return array
    
    # Python Dunders #
    def __iter__(self):
        self.dimension = 0
        return self
    
    def __next__(self) -> float:
        if self.dimension < len(self.position):
            i = self.dimension
            self.dimension += 1
            return self.position[i]
        else:
            raise StopIteration
    
    def __str__(self) -> str:
        return f"PanCAD Point at position {self.position}"
    
    # NumPy Dunders #
    def __array__(self, dtype=None, copy=None) -> np.ndarray:
        return np.array(list(self))