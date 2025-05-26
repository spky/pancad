"""A module providing a class to represent lines in all CAD programs,  
graphics, and other geometry use cases. Not to be confused with line 
segments, which is part of a line that is the shortest distance between two 
points.
"""
from __future__ import annotations
from functools import partial

import math

import numpy as np

from PanCAD.geometry import Point
from PanCAD.utils import trigonometry as trig
from PanCAD.utils import comparison

isclose = partial(comparison.isclose, nan_equal=False)
isclose0 = partial(comparison.isclose, value_b=0, nan_equal=False)

class Line:
    """A class representing infinite lines in 2D and 3D space. A Line 
    instance can be uniquely identified and compared for equality/inequality 
    with other lines by using its direction and reference_point. The 
    direction is explained below. The reference_point is the point on the 
    line closest to the origin.
    
    :param point: A point on the line.
    :param direction: A vector in the direction of the line. Vector can be 
                      positive or negative, it will not impact the result.
    :param uid: The unique ID of the line for interoperable CAD 
                identification.
    """
    
    def __init__(self, point: Point=None, direction:tuple | np.ndarray = None,
                 uid:str = None):
        self.uid = uid
        self.direction = direction
        
        if isinstance(point, Point):
            self._point_closest_to_origin = Line.closest_to_origin(
                point, self.direction
            )
        elif isinstance(point, tuple):
            raise ValueError("point cannot be a tuple for Line's init function."
                             "Use Line.from_two_points instead")
        else:
            self._point_closest_to_origin = None
    
    # Getters #
    @property
    def direction(self) -> tuple:
        """The unique direction of the line represented as a vector with 
        cartesian components. Independent of line definition method.
        
        :getter: Returns the direction of the line as a tuple
        :setter: Takes a vector, finds its unique direction unit vector, and 
                 sets that as the direction of the line.
        """
        return self._direction
    
    @property
    def direction_polar(self) -> tuple:
        return trig.cartesian_to_polar(self.direction)
    
    @property
    def direction_spherical(self) -> tuple:
        return trig.cartesian_to_spherical(self.direction)
    
    @property
    def phi(self) -> float:
        """The polar/spherical azimuth component of the line's direction in 
        radians.
        
        :getter: Returns the azimuth component of the line's direction.
        :setter: None, read-only. Use a public method to change the direction
        """
        return trig.phi_of_cartesian(self.direction)
    
    @property
    def reference_point(self) -> Point:
        """The closest point to the origin of the line.
        
        :getter: Returns the Point instance representing the point closest to 
                 the origin on the line.
        :setter: None, read-only. Use a public method to change the line position
        """
        return self._point_closest_to_origin
    
    @property
    def slope(self) -> float:
        """The slope of the line (m in y = mx + b), only available if the 
        line is 2D.
        
        :getter: Returns the slope of the line.
        :setter: Sets the slope of the line while keeping the y intercept (b 
                 in y = mx + b) the same.
        """
        if len(self) == 2:
            if self.direction[0] == 0:
                return math.nan
            else:
                return self.direction[1]/self.direction[0]
        else:
            raise ValueError("slope is not defined for a 3D line")
    
    @property
    def theta(self) -> float:
        """The spherical inclination component of the line's direction in 
        radians.
        
        :getter: Returns the inclination angle of the line's direction
        :setter: None, read-only. Use a public method to change the direction
        """
        return trig.theta_of_cartesian(self.direction)
    
    @property
    def uid(self) -> str:
        """The unique id of the line. Can also be interpreted as the name of 
        the line
        
        :getter: Returns the unique id as a string.
        :setter: Sets the unique id.
        """
        return self._uid
    
    @property
    def x_intercept(self) -> float:
        """The x-intercept of the line (x when y = 0 in y = mx + b), only 
        available if the line is 2D.
        
        :getter: Returns the x-intercept of the line
        :setter: Sets the x-intercept of the line while keeping the slope (m 
                 in y = mx + b) the same.
        """
        if len(self) == 2:
            if self.direction[0] == 1:
                return math.nan
            elif self.direction[0] == 0:
                return self.reference_point.x
            else:
                return (self.slope*self.reference_point.x
                        - self.reference_point.y)/self.slope
        else:
            raise ValueError("x-intercept is not defined for a 3D line")
    
    @property
    def y_intercept(self) -> float:
        """The y-intercept of the line (b in y = mx + b), only available if 
        the line is 2D.
        
        :getter: Returns the y-intercept of the line
        :setter: Sets the y-intercept of the line while keeping the slope (m 
                 in y = mx + b) the same.
        """
        if len(self) == 2:
            if self.direction[0] == 0:
                return math.nan
            else:
                return (self.reference_point.y
                        - self.slope*self.reference_point.x)
        else:
            raise ValueError("y-intercept is not defined for a 3D line")
    
    # Setters #
    @direction.setter
    def direction(self, vector: list | tuple | np.ndarray):
        if vector is not None:
            vector = trig.to_1D_np(vector)
            self._direction = Line._unique_direction(vector)
        else:
            self._direction = None
    
    @direction_polar.setter
    def direction_polar(self, vector: list | tuple | np.ndarray):
        self.direction = trig.polar_to_cartesian(vector)
    
    @direction_spherical.setter
    def direction_spherical(self, vector: list | tuple | np.ndarray):
        self.direction = trig.spherical_to_cartesian(vector)
    
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
    def copy(self) -> Line:
        return self.__copy__()
    
    def get_parametric_point(self, t: float) -> Point:
        """Returns the point at parameter t where a, b, and c are defined by 
        the unique unit vector direction of the line and initialized at the 
        point closest to the origin.
        
        :param t: The value of the line parameter
        :returns: The point on the line corresponding to the parameter's value
        """
        return Point(
            np.array(self.reference_point) + trig.to_1D_np(self.direction)*t
        )
    
    def get_parametric_constants(self) -> tuple[float]:
        """Returns a tuple containing parameters (x0, y0, z0, a, b, c) for the 
        line. The reference point is used for the initial position and the 
        line's direction vector is used for a, b, and c.
        """
        return (*tuple(self.reference_point), *self.direction)
    
    def move_to_point(self, point: Point,
                      phi: float=None, theta: float=None) -> Line:
        """Moves the line to go through a point and changes the line's 
        direction's phi (polar azimuth angle) and/or theta (polar elevation 
        angle) around that point. If phi or theta are set to None then they 
        stay constant unless 
        
        :param point: A point the user wants to be on the line
        :param phi: The line's new phi around the point in radians
        :param theta: The line's new theta around the point in radians
        :returns: The line with an updated reference_point that goes through the 
                  point
        """
        if phi is not None or theta is not None:
            direction_end_pt = Point(self.direction)
            if phi is not None and theta is not None and len(self) == 3:
                direction_end_pt.spherical = (1, phi, theta)
            elif theta is not None and len(self) == 2:
                raise ValueError("Theta can only be set on 3D Lines")
            elif phi is not None and theta is None:
                direction_end_pt.phi = phi
            elif phi is None and theta is not None:
                direction_end_pt.theta = theta
            self.direction = tuple(direction_end_pt)
        
        self._point_closest_to_origin = self.closest_to_origin(
            point, self.direction
        )
        return self
    
    # Class Methods #
    @classmethod
    def from_two_points(cls, a:Point | tuple, b:Point | tuple,
                        uid:str = None) -> Line:
        """Returns a Line instance defined by points a and b. Point order 
        does not matter since lines are infinite. If direction matters, use 
        LineSegment.
        
        :param a: A PanCAD Point on the line
        :param b: A PanCAD Point on the line that is not the same as point a
        """
        if isinstance(a, tuple) and len(a) in (2, 3): a = Point(a)
        if isinstance(b, tuple) and len(b) in (2, 3): b = Point(b)
        
        if not isinstance(a, Point) or not isinstance(b, Point):
            raise ValueError(f"Points a and b must be tuples or PanCAD Points."
                             + f" Classes - a: {a.__class__}, b:{b.__class__}")
        
        if a != b:
            a_vector, b_vector = np.array(a), np.array(b)
            ab_vector = b_vector - a_vector
            return cls(Point(a_vector), ab_vector, uid)
        else:
            raise ValueError(f"A line cannot be defined by 2 points at the same"
                             f" location. Point a: {tuple(a)}, Point b:"
                             f" {tuple(b)}")
    
    @classmethod
    def from_slope_and_y_intercept(cls, slope: float, intercept: float,
                                   uid: str = None) -> Line:
        """Returns a 2D line described by y = mx + b, where m is the slope 
        and b is the y intercept."""
        if slope == 0: # Horizontal
            point_a = Point((0, intercept))
            point_b = Point((1, intercept))
        else:
            point_a = Point((0, intercept))
            point_b = Point((1, slope + intercept))
        
        return Line.from_two_points(point_a, point_b)
    
    @classmethod
    def from_parametric(cls, x_intercept: float, x_slope: float,
                        y_intercept: float, y_slope: float,
                        z_intercept: float = None, z_slope: float = None) -> Line:
        raise NotImplementedError
    
    @classmethod
    def from_point_and_angle(cls, point: Point | tuple | np.ndarray, phi: float,
                             theta: float = None, uid: str = None) -> Line:
        """Return a line from a given point and phi or phi and theta.
        
        :param point: A point on the line
        :param phi: The phi angle of the line around the point
        :param theta: The theta angle of the line around the point, if 3D
        :returns: A Line object that runs through the point in a direction 
            with the provided angles
        """
        if isinstance(point, (tuple, np.ndarray)): point = Point(point)
        if len(point) == 2 and theta is None:
            direction_end_pt = Point(1, 0)
            direction_end_pt.phi = phi
        elif len(point) == 3 and theta is not None:
            direction_end_pt = Point(1, 0, 0)
            direction_end_pt.spherical = (1, phi, theta)
        elif len(point) == 3 and theta is None:
            raise ValueError("If a 3D point is given, theta must also be given")
        elif len(point) == 2 and theta is not None:
            raise ValueError("Theta can only be specified for 3D points")
        
        direction = tuple(direction_end_pt)
        return cls(point, direction, uid)
    
    @classmethod
    def from_x_intercept(cls, x_intercept: float, uid: str = None) -> Line:
        """Returns a 2D vertical line the passes through the x intercept"""
        return cls(Point(x_intercept, 0), (0, 1), uid)
    
    @classmethod
    def from_y_intercept(cls, y_intercept: float, uid: str = None) -> Line:
        """Returns a 2D horizontal line the passes through the y intercept"""
        return cls(Point(0, y_intercept), (1, 0), uid)
    
    # Static Methods #
    @staticmethod
    def closest_to_origin(point: Point, vector: list | tuple | np.ndarray) -> Point:
        """Returns the point on the line created by the point and vector 
        closest to the origin.
        
        :param point: a Point on the line
        :param vector: a vector in the direction of the line
        :returns: The point on the line created by the given point and vector 
            closest to the origin
        """
        point_vector = np.array(point)
        vector = trig.to_1D_np(vector)
        unit_vector = trig.get_unit_vector(vector)
        dot_product = np.dot(point_vector, unit_vector)
        
        if dot_product == 0:
            point_closest_to_origin = Point(point_vector)
        elif abs(dot_product) == np.linalg.norm(point_vector):
            if len(point) == 2:
                point_closest_to_origin = Point((0,0))
            else:
                point_closest_to_origin = Point((0,0,0))
        elif (np.linalg.norm(point_vector + unit_vector)
              < np.linalg.norm(point_vector + unit_vector)):
            point_closest_to_origin = Point(
                point_vector + dot_product * unit_vector
            )
        else:
            point_closest_to_origin = Point(
                point_vector - dot_product * unit_vector
            )
        
        return point_closest_to_origin
    
    @staticmethod
    def _unique_direction(vector:np.ndarray) -> np.ndarray:
        """Returns a unit vector that can uniquely identify the direction of 
        the given vector. Does so flipping the unit vector if necessary to 
        ensure there can only ever be one vector for every direction.
        
        :param vector: A 1D vector of cartesian coordinates as a numpy array
        :returns: The unique unit vector to represent the vector's direction.
        """
        unit_vector = trig.get_unit_vector(vector)
        if len(unit_vector) == 3:
            x, y, z = unit_vector
            if x < 0 and isclose0(y) and isclose0(z):
                unit_vector = -unit_vector
            elif y < 0 and isclose0(z):
                unit_vector = -unit_vector
            elif z < 0:
                unit_vector = -unit_vector
        elif len(unit_vector) == 2:
            x, y = unit_vector
            if x < 0 and isclose0(y):
                unit_vector = -unit_vector
            elif not isclose0(y) and y < 0:
                unit_vector = -unit_vector
        
        # Add 0 to ensure negative zero representations are eliminated
        return trig.to_1D_tuple(unit_vector + 0)
    
    # Python Dunders #
    def __copy__(self) -> Line:
        """Returns a copy of the line that has the same closest to origin 
        point and direction, but no assigned uid. Can be used with the python 
        copy module"""
        return Line(self.reference_point, self.direction)
    
    def __eq__(self, other: Line) -> bool:
        """Rich comparison for line equality that allows for lines to be 
        directly compared with ==.
        
        :param other: The line to compare self to.
        :returns: Whether the tuples of the lines' reference_points and 
                  directions are equal
        """
        if isinstance(other, Line):
            return (
                isclose(tuple(self._point_closest_to_origin),
                        tuple(other._point_closest_to_origin))
                and isclose(self.direction, other.direction)
            )
        else:
            return NotImplemented
    
    def __len__(self) -> int:
        """Returns the number of elements in the line's direction tuple, 
        which is equivalent to the line's number of dimnesions."""
        return len(self.direction)
    
    def __repr__(self) -> str:
        """Returns the short string representation of the line"""
        return f"PanCAD_Line{tuple(self._point_closest_to_origin)},{self.direction}"
    
    def __str__(self) -> str:
        """String function to output the line's description, closest 
        cartesian point to the origin, and unique cartesian direction 
        unit vector"""
        closest_point = tuple(self._point_closest_to_origin)
        return (f"PanCAD Line with a point closest to the origin at"
                + f" {closest_point} and in the direction {self.direction}")