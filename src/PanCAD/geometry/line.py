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
    
    def __init__(self, point:Point = None, direction:tuple | np.ndarray = None,
                 uid:str = None):
        self.uid = uid
        self.direction = direction
        
        if point is not None:
            self._point_closest_to_origin = Line.closest_to_origin(
                point, self.direction
            )
        else:
            self._point_closest_to_origin = None
    
    # Getters #
    @property
    def direction(self) -> tuple:
        """The unique direction of the line. Independent of line definition 
        method.
        
        :getter: Returns the direction of the line as a tuple
        :setter: Takes a vector, finds its unique direction unit vector, and 
                 sets that as the direction of the line.
        """
        return self._direction
    
    @property
    def uid(self) -> str:
        """The unique id of the line. Can also be interpreted as the name of 
        the line
        
        :getter: Returns the unique id as a string.
        :setter: Sets the unique id.
        """
        return self._uid
    
    # Setters #
    @direction.setter
    def direction(self, vector: list | tuple | np.ndarray):
        if vector is not None:
            vector = trig.to_1D_np(vector)
            self._direction = Line.unique_direction(vector)
        else:
            self._direction = None
    
    @uid.setter
    def uid(self, uid: str) -> None:
        self._uid = uid
    
    # Class Methods #
    @classmethod
    def from_two_points(cls, a:Point, b:Point, uid:str = None) -> Line:
        """Returns a Line instance defined by points a and b. Point order 
        does not matter since lines are infinite. If direction matters, use 
        LineSegment.
        
        :param a: A PanCAD Point
        :param b: A PanCAD Point that is not the same as point a
        """
        if not isinstance(a, Point) or not isinstance(b, Point):
            raise ValueError(f"Points a and b must be PanCAD points."
                             + f"Classes - a: {a.__class__}, b:{b.__class__}")
        if a != b:
            a_vector, b_vector = np.array(a), np.array(b)
            ab_vector = b_vector - a_vector
            return cls(a_vector, ab_vector, uid)
        else:
            raise ValueError(f"A line cannot be defined by 2 points at the same"
                             f" location. Point a: {tuple(a)}, Point b:"
                             f" {tuple(b)}")
    
    @classmethod
    def from_slope_and_intercept(cls, slope: float, intercept: float,
                                 uid: str = None) -> Line:
        pass
    
    @classmethod
    def from_parametric(cls, x_intercept: float, x_slope: float,
                        y_intercept: float, y_slope: float,
                        z_intercept: float = None, z_slope: float = None) -> Line:
        pass
    
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
    def __eq__(self, other: Line) -> bool:
        """Rich comparison for line equality that allows for lines to be 
        directly compared with ==.
        
        :param other: The point to compare self to.
        :returns: Whether the tuples of the points are equal.
        """
        self_origin_pt = self._point_closest_to_origin
        other_origin_pt = other._point_closest_to_origin
        if isinstance(other, Line):
            return (tuple(self_origin_pt) == tuple(other_origin_pt)
                    and self.direction == other.direction)
        else:
            return NotImplemented
    
    def __str__(self) -> str:
        """String function to output the line's description, closest 
        cartesian point to the origin, and unique cartesian direction 
        unit vector"""
        closest_point = tuple(self._point_closest_to_origin)
        
        return (f"PanCAD Line with a point closest to the origin at"
                + f" {closest_point} and in the direction {self.direction}")