"""A module providing a class to represent lines in all CAD programs,  
graphics, and other geometry use cases. Not to be confused with line 
segments, which is part of a line that is the shortest distance between two 
points.
"""
from __future__ import annotations

import math

import numpy as np

from PanCAD.geometry.point import Point
from PanCAD.utils import trigonometry as trig

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
    
    relative_tolerance = 1e-9
    absolute_tolerance = 1e-9
    
    def __init__(self, point:Point = None, direction:tuple | np.ndarray = None,
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
        :setter: Sets the azimuth component of the line while keeping theta 
                 the same. Checks the value for polar or spherical vector 
                 validity and will error if it is violated.
        """
        return trig.phi_of_cartesian(self.direction)
    
    @property
    def reference_point(self) -> Point:
        """The closest point to the origin of the line.
        
        :getter: Returns the Point instance representing the point.
        :setter: Sets the closest point to the origin of the line while 
                 keeping the direction the same.
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
        
        :getter: Returns the inclination coordinate of the point.
        :setter: Sets the inclination component of the line's direction. 
                 Checks the value for polar or spherical vector validity and 
                 will error if it is violated.
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
            self._direction = Line.unique_direction(vector)
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
    
    def get_angle_between(self, other_line: Line,
                          supplement: bool=False, signed: bool=False) -> float:
        """Returns the value of the angle between this line and the 
        other line.
        
        :param other_line: A line to find the angle of relative to this line
        :param supplement: If False, the angle's magnitude is the angle 
            clockwise of this line and counterclockwise of the other line 
            (which is equal to the angle counterclockwise of this line and 
            clockwise of the other line). If True, the angle's magnitude will 
            be the supplement of the False angle which is the angle of 
            the other two quadrants. Note: If the lines are parallel, this 
            will cause the function to return pi
        :param signed: If False, the absolute value of the angle will be 
            returned. If True and the line is 2D, angle will be negative the 
            angle between this line's direction and the other line's 
            direction is clockwise
        :returns: The value of the angle between the lines in radians. If the 
            lines are skew, returns None.
        """
        if self.is_parallel(other_line):
            if supplement:
                return math.pi
            else:
                return 0
        elif self.is_skew(other_line):
            return None
        
        dot_angle = math.acos(np.dot(self.direction, other_line.direction))
        if supplement:
            angle_magnitude = math.pi - dot_angle
        else:
            angle_magnitude = dot_angle
        
        if len(self) == 3 and signed:
            raise NotImplementedError("""Signed angles between 3D lines will
                                      require a not yet made implementation 
                                      of planes""")
        elif len(self) == 2 and signed:
            direction_90_ccw = (-self.direction[1], self.direction[0])
            is_clockwise = np.dot(direction_90_ccw, other_line.direction) < 0
            if is_clockwise ^ supplement:
                return -angle_magnitude
            else:
                return angle_magnitude
        else:
            return angle_magnitude
        
    
    def get_intersection(self, other_line: Line) -> Point | None:
        """Returns the intersection of this line with another line as a Point 
        if it exists.
        
        :param other_line: Another line to compare to this line and find the 
            intersection point, if it exists.
        :returns: The intersection point if it exists, otherwise None
        """
        if self.is_parallel(other_line) or self.is_skew(other_line):
            return None
        
        pt1_to_pt2 = (self.reference_point.vector() 
                      - other_line.reference_point.vector())
        matrix_a = np.column_stack(
            (np.array(other_line.direction), -np.array(self.direction))
        )
        
        non_zero_rows = []
        for c1, c2 in zip(self.direction, other_line.direction):
            non_zero_rows.append(not (self._isclose(c1, 0)
                                      and self._isclose(c2, 0)))
        
        if len(self) == 2:
            pass
        elif non_zero_rows[0] and non_zero_rows[1] and not non_zero_rows[2]:
            matrix_a = np.delete(matrix_a, (2), axis=0)
            pt1_to_pt2 = np.delete(pt1_to_pt2, (2), axis=0)
        elif non_zero_rows[0] and not non_zero_rows[1] and non_zero_rows[2]:
            matrix_a = np.delete(matrix_a, (1), axis=0)
            pt1_to_pt2 = np.delete(pt1_to_pt2, (1), axis=0)
        elif all(non_zero_rows):
            matrix_a_yz = np.delete(matrix_a, (0), axis=0)
            if self._isclose(np.det(matrix_a_yz), 0):
                return None
            matrix_a = np.delete(matrix_a, (2), axis=0)
        else:
            matrix_a = np.delete(matrix_a, (0), axis=0)
            pt1_to_pt2 = np.delete(pt1_to_pt2, (0), axis=0)
        
        if self._isclose(np.linalg.det(matrix_a), 0):
            return None
        else:
            t = np.linalg.inv(matrix_a) @ pt1_to_pt2
            return self.get_parametric_point(t[1])
    
    def get_parametric_point(self, t: float) -> Point:
        """Returns the point at parameter t where a, b, and c are defined by 
        the unique unit vector direction of the line and initialized at the 
        point closest to the origin.
        
        :param t: The value of the line parameter
        """
        return Point(
            np.array(self.reference_point) + trig.to_1D_np(self.direction)*t
        )
    
    def is_collinear(self, other_line: Line) -> bool:
        """Returns whether the line is collinear to another line
        
        :param other_line: A line that can be checked for collinearity
        :returns: True if collinear, False otherwise
        """
        other_line = Line._get_comparison_line(other_line)
        return self == other_line
    
    def is_coincident(self, point: Point) -> bool:
        """Returns whether the given point is on the line.
        
        :param point: A Point to check the location of
        :returns: True if the point is on the line, false otherwise
        """
        if self.reference_point == point:
            # Cover the edge cases where point is the zero vector or if the 
            # point is the reference_point
            return True
        
        point_vector = np.array(point)
        reference_vector = np.array(self.reference_point)
        direction_vector = np.array(self.direction)
        
        ref_pt_to_pt = (np.dot(point_vector, direction_vector)
                        * direction_vector)
        
        check_point_tuple = trig.to_1D_tuple(ref_pt_to_pt + reference_vector)
        
        if self._isclose_tuple(check_point_tuple, tuple(point)):
            return True
        else:
            return False
    
    def is_coplanar(self, other_line: Line) -> bool:
        """Returns whether the other line can lie on the same plane as this 
        line. Effectively whether the line is intersecting or parallel.
        
        :param other_line: A line to check for coplanarity with this line
        :returns: True if the other line is coplanar, otherwise False
        """
        other_line = Line._get_comparison_line(other_line)
        return self.is_parallel(other_line) or not self.is_skew(other_line)
    
    def is_parallel(self, other_line: Line) -> bool:
        """Returns whether the line is parallel to another line"""
        other_line = Line._get_comparison_line(other_line)
        return self._isclose_tuple(self.direction, other_line.direction)
    
    def is_perpendicular(self, other_line: Line) -> bool:
        """Returns whether the line is intersects and is oriented 90 degrees 
        to the other line.
        
        :param other_line: A line to check for perpendicularity with this line
        :returns: True if the other line is perpendicular to this line, 
                  otherwise False
        """
        other_line = Line._get_comparison_line(other_line)
        if self.is_skew(other_line):
            return False
        else:
            dot_product = np.dot(self.direction, other_line.direction)
            return self._isclose(dot_product, 0)
    
    def is_skew(self, other_line: Line) -> bool:
        """Returns whether the line is skew to another line"""
        other_line = Line._get_comparison_line(other_line)
        if self.is_parallel(other_line):
            return False
        elif len(self) != len(other_line):
            raise ValueError("Both lines must have the same number of dimensions")
        elif len(self) == 2:
            return False
        
        pt1_to_pt2 = (np.array(self.reference_point)
                      - np.array(other_line.reference_point))
        cross_product = np.cross(self.direction, other_line.direction)
        
        if self._isclose(np.dot(pt1_to_pt2, cross_product), 0):
            return False
        else:
            return True
    
    def move_to_point(self, point: Point) -> Line:
        """Moves the line's reference_point while keeping the direction constant 
        to make the line go through a new point.
        
        :param point: A point the user wants to be on the line
        :returns: The line with an updated reference_point that goes through the 
                  point
        """
        self._point_closest_to_origin = self.closest_to_origin(
            point, self.direction
        )
        return self
    
    # Private Methods
    def _isclose(self, value_a: float, value_b: float) -> bool:
        """Returns whether value_a is close to value_b using the Line's class 
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
        corresponding components of value_b using the Line's class variables.
        
        :param value_a: A tuple to compare
        :param value_b: Another tuple to compare
        :returns: True if value_a's components == value_b's components within 
                  the Line's relative and absolute tolerance class variables
        """
        return trig.isclose_tuple(value_a, value_b,
                                  rel_tol=self.relative_tolerance,
                                  abs_tol=self.absolute_tolerance)
    
    # Class Methods #
    @classmethod
    def from_two_points(cls, a:Point, b:Point, uid:str = None) -> Line:
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
    def from_x_intercept(cls, x_intercept: float, uid:str = None) -> Line:
        """Returns a 2D vertical line the passes through the x intercept"""
        return cls(Point(x_intercept, 0), (0, 1), uid)
    
    @classmethod
    def from_y_intercept(cls, y_intercept: float, uid:str = None) -> Line:
        """Returns a 2D horizontal line the passes through the y intercept"""
        return cls(Point(0, y_intercept), (1, 0), uid)
    
    # Static Methods #
    @staticmethod
    def closest_to_origin(point:Point, vector: list | tuple | np.ndarray):
        """Returns the point on the line created by the point and vector 
        closest to the origin.
        
        :param point: a Point on the line
        :param vector: a vector in the direction of the line
        """
        point_vector = np.array(point)
        vector = trig.to_1D_np(vector)
        unit_vector = trig.get_unit_vector(vector)
        dot_product = np.dot(point_vector, unit_vector)
        
        if dot_product == 0:
            point_closest_to_origin = Point(point_vector)
        elif abs(dot_product) == np.linalg.norm(point_vector):
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
    def _get_comparison_line(other) -> Line:
        """Returns a PanCAD Line object from another object to use in 
        comparisons. Used to handle cases like a LineSegment checking 
        whether it is parallel to an infinite Line since LineSegments have 
        Lines. Is not used for the __eq__ dunder since that is only to be 
        used for checking Line to Line equality.
        
        :param other: Another object that is either another Line object, or a 
                      has a "get_line" function that can return one
        """
        if isinstance(other, Line):
            return other
        elif hasattr(other, "get_line"):
            return other.get_line()
    
    @staticmethod
    def unique_direction(vector:np.ndarray) -> np.ndarray:
        """Returns a unit vector that can uniquely identify the direction of 
        the given vector. Does so flipping the unit vector if necessary to 
        ensure there can only ever be one vector for every direction.
        
        :param vector: A 1D vector of cartesian coordinates as a numpy array
        :returns: The unique unit vector to represent the vector's direction.
        """
        unit_vector = trig.get_unit_vector(vector)
        if len(unit_vector) == 3:
            if unit_vector[0] < 0 and unit_vector[1] == 0 and unit_vector[2] == 0:
                unit_vector = -unit_vector
            elif unit_vector[1] < 0 and unit_vector[2] == 0:
                unit_vector = -unit_vector
            elif unit_vector[2] < 0:
                unit_vector = -unit_vector
        elif len(unit_vector) == 2:
            if unit_vector[0] < 0 and unit_vector[1] == 0:
                unit_vector = -unit_vector
            elif unit_vector[1] < 0:
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
        self_origin_pt = self._point_closest_to_origin
        other_origin_pt = other._point_closest_to_origin
        if isinstance(other, Line):
            return (
                self._isclose_tuple(tuple(self_origin_pt), tuple(other_origin_pt))
                and self._isclose_tuple(self.direction, other.direction)
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