"""A module providing a class to represent line segments in all CAD programs, 
graphics, and other geometry use cases.
"""
from __future__ import annotations

import math

import numpy as np

from PanCAD.utils import trigonometry as trig
from PanCAD.geometry.point import Point
from PanCAD.geometry.line import Line

class LineSegment:
    """A class representing a finite line in 2D and 3D space.
    """
    relative_tolerance = 1e-9
    absolute_tolerance = 1e-9
    
    def __init__(self, point_a: Point | tuple, point_b: Point | tuple,
                 uid: str = None):
        self.uid = uid
        
        if isinstance(point_a, tuple): point_a = Point(point_a)
        if isinstance(point_b, tuple): point_b = Point(point_b)
        
        self.update_points(point_a, point_b)
        
    # Getters #
    @property
    def direction(self) -> tuple:
        """The direction of the line segment, defined as the unit vector 
        pointing from point_a to point_b. The direction will not always be 
        the same sign as the LineSegment's Line direction since it 
        depends on point a and b's order"""
        vector_ab = np.array(self.point_b) - np.array(self.point_a)
        unit_vector_ab = trig.get_unit_vector(vector_ab)
        return trig.to_1D_tuple(unit_vector_ab)
    
    @property
    def direction_polar(self) -> tuple:
        return trig.cartesian_to_polar(self.direction)
    
    @property
    def direction_spherical(self) -> tuple:
        return trig.cartesian_to_spherical(self.direction)
    
    @property
    def length(self) -> float:
        return float(np.linalg.norm(self.get_vector_ab()))
    
    @property
    def point_a(self) -> Point:
        return self._point_a
    
    @property
    def point_b(self) -> Point:
        return self._point_b
    
    # Setters #
    @point_a.setter
    def point_a(self, pt: Point):
        self.update_points(pt, self.point_b)
    
    @point_b.setter
    def point_b(self, pt: Point):
        self.update_points(self.point_a, pt)
    
    # Public Methods #
    def copy(self) -> LineSegment:
        return self.__copy__()
    
    def get_length(self) -> float:
        return self.length
    
    def get_x_length(self) -> float:
        return abs(self.point_a.x - self.point_b.x)
    
    def get_y_length(self) -> float:
        return abs(self.point_a.y - self.point_b.y)
    
    def get_z_length(self) -> float:
        return abs(self.point_a.z - self.point_b.z)
    
    def get_line(self) -> Line:
        return Line.from_two_points(self.point_a, self.point_b)
    
    def get_vector_ab(self, numpy_vector: bool=True) -> tuple | np.ndarray:
        np_vector_ab = np.array(self.point_b) - np.array(self.point_a)
        if numpy_vector:
            return np_vector_ab
        else:
            return trig.to_1D_tuple(np_vector_ab)
    
    def is_collinear(self, other: LineSegment | Line) -> bool:
        other_line = LineSegment._get_comparison_line(other)
        return self.get_line().is_collinear(other_line)
    
    def is_coincident(self, other: Point) -> bool:
        return self.get_line().is_coincident(other)
    
    def is_coplanar(self, other: LineSegment | Line) -> bool:
        other_line = LineSegment._get_comparison_line(other)
        return self.get_line().is_coplanar(other_line)
    
    def is_parallel(self, other: LineSegment | Line) -> bool:
        other_line = LineSegment._get_comparison_line(other)
        return self.get_line().is_parallel(other_line)
    
    def is_perpendicular(self, other: LineSegment | Line) -> bool:
        other_line = LineSegment._get_comparison_line(other)
        return self.get_line().is_perpendicular(other)
    
    def is_skew(self, other: LineSegment | Line) -> bool:
        other_line = LineSegment._get_comparison_line(other)
        return self.get_line().is_skew(other)
    
    def set_length_from_a(self, value: float):
        if value != 0:
            new_vector_ab = np.array(self.direction) * value
            self.point_b.cartesian = (np.array(self.point_a.cartesian)
                                      + new_vector_ab)
        else:
            raise ValueError("Line Length cannot be set to 0")
    
    def set_length_from_b(self, value: float):
        new_vector_ab = np.array(self.direction) * value
        self.point_a.cartesian = np.array(self.point_b.cartesian) - new_vector_ab
    
    def set_x_length_from_a(self, value: float):
        self._update_axis_length(value, 0, True)
    
    def set_x_length_from_b(self, value: float):
        self._update_axis_length(value, 0, False)
    
    def set_y_length_from_a(self, value: float):
        self._update_axis_length(value, 1, True)
    
    def set_y_length_from_b(self, value: float):
        self._update_axis_length(value, 1, False)
    
    def set_z_length_from_a(self, value: float):
        self._update_axis_length(value, 2, True)
    
    def set_z_length_from_b(self, value: float):
        self._update_axis_length(value, 2, False)
    
    def update_points(self, point_a: Point, point_b: Point):
        if point_a == point_b:
            raise ValueError("""Line Segments cannot be defined with 2 of the 
                             same point""")
        elif len(point_a) == len(point_b):
            if hasattr(self, "_point_a"):
                # Update existing points
                self._point_a.cartesian = point_a.cartesian
                self._point_b.cartesian = point_b.cartesian
            else:
                # Initialize Points
                self._point_a = point_a
                self._point_b = point_b
        else:
            raise ValueError("""point_a and point_b must have the same number of
                              dimensions to initialize a line segment""")
    
    # Private Methods
    def _update_axis_length(self, value: float, axis: int, from_point_a: bool):
        new_vector_ab = self.get_vector_ab()
        new_vector_ab[axis] = value * math.copysign(1, self.direction[axis])
        if from_point_a:
            self.point_b.cartesian = (np.array(self.point_a.cartesian)
                                      + new_vector_ab)
        else:
            self.point_a.cartesian = (np.array(self.point_b.cartesian)
                                      - new_vector_ab)
    
    # Private Static Methods #
    def _get_comparison_line(other: Line | LineSegment) -> Line:
        if isinstance(other, Line):
            return other
        elif isinstance(other, LineSegment):
            return other.get_line()
        else:
            raise ValueError("other must be a Line or LineSegment")
    
    # Python Dunders #
    def __copy__(self) -> LineSegment:
        """Returns a copy of the LineSegment that has the same points and line, 
        but no assigned uid. Can be used with the python copy module"""
        return LineSegment(self.point_a, self.point_b)
    
    def __eq__(self, other: LineSegment) -> bool:
        """Rich comparison for LineSegment equality that allows for line
        segments to be directly compared with ==.
        
        :param other: The point to compare self to.
        :returns: Whether the line segments' points are equal, which implies the 
                  lines are also equal
        """
        if isinstance(other, LineSegment):
            return (
                self.point_a == other.point_a
                and self.point_b == other.point_b
            )
        else:
            return NotImplemented
    
    def __len__(self) -> int:
        """Returns the number of elements in the line segment's point_a, which is 
        equivalent to the line segment's number of dimnesions."""
        return len(self.point_a)
    
    def __repr__(self) -> str:
        """Returns the short string representation of the line"""
        return f"PanCAD_LineSegment{tuple(self.point_a)}{tuple(self.point_b)}"
    
    def __str__(self) -> str:
        """String function to output the line's description, closest 
        cartesian point to the origin, and unique cartesian direction 
        unit vector"""
        return (f"""PanCAD LineSegment with point_a {tuple(self.point_a)},
                point_b {tuple(self.point_b)} and a line in direction
                {self.get_line().direction}""")