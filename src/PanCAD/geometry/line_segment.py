"""A module providing a class to represent line segments in all CAD programs, 
graphics, and other geometry use cases.
"""
from __future__ import annotations

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
        vector_ab = np.array(self.point_b) - np.array(self.point_a)
        return float(np.linalg.norm(vector_ab))
    
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
    
    def set_length_from_a(self, value: float):
        pass
    
    def set_length_from_b(self, value: float):
        pass
    
    def get_line(self) -> Line:
        return self._line
    
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
    
    def update_points(self, point_a: Point, point_b: Point):
        if point_a == point_b:
            raise ValueError("""Line Segments cannot be defined with 2 of the 
                             same point""")
        elif len(point_a) == len(point_b):
            self._point_a = point_a
            self._point_b = point_b
            self._line = Line.from_two_points(self.point_a, self.point_b)
        else:
            raise ValueError("""point_a and point_b must have the same number of
                              dimensions to initialize a line segment""")
    
    # Static Methods #
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