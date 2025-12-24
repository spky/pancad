"""A module providing a class to represent line segments in all CAD programs, 
graphics, and other geometry use cases.
"""
from __future__ import annotations

from math import copysign
from functools import partial
from numbers import Real
from sqlite3 import PrepareProtocol
from typing import TYPE_CHECKING

import numpy as np

from pancad.geometry import AbstractGeometry, Point, Line
from pancad.geometry.constants import ConstraintReference
from pancad.utils import comparison, trigonometry as trig
from pancad.utils.geometry import parse_vector
from pancad.utils.pancad_types import VectorLike

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Self

isclose0 = partial(comparison.isclose, value_b=0, nan_equal=False)

class LineSegment(AbstractGeometry):
    """A class representing finite lines in 2D and 3D space.
    
    :param start: The start point of the line segment.
    :param end: The end point of the line segment.
    :param uid: The unique id of the line segment.
    """
    REFERENCES = (ConstraintReference.CORE,
                  ConstraintReference.START,
                  ConstraintReference.END)
    """All relevant ConstraintReferences for LineSegments."""
    def __init__(self,
                 start: Point | VectorLike,
                 end: Point | VectorLike,
                 uid: str=None) -> None:
        if isinstance(start, VectorLike):
            start = Point(start)
        if isinstance(end, VectorLike):
            end = Point(end)
        if any(not isinstance(point, Point) for point in [start, end]):
            types = [type(point) for point in [start, end]]
            raise TypeError(f"Expected Point or VectorLike, got {types}")
        self._start = start
        self._end = end
        self.update_points(start, end)
        self.uid = uid
    # Class Methods #
    @classmethod
    def from_point_length_angle(cls,
                                start: Point,
                                *components: Real | Sequence[Real] | np.ndarray,
                                uid=None):
        """Returns a LineSegment defined by a point and a length, azimuth angle 
        phi, and inclination angle theta relative to the point.
        
        :param point: A Point, or iterable with 2 or 3 dimensions.
        :param components: The length (r), azimuth angle (phi), and (for 3D 
            only) the inclination angle (theta) of the vector from the start 
            point to the end point. A polar/spherical vector. Angles must be in 
            radians.
        :returns: A line segment with its start at point, and end at the point's 
            position plus the polar/spherical vector.
        :raises TypeError:  When provided a single component that is not Sequence 
            or when 2 or more non-Real arguments.
        :raises ValueError: When provided too many components or a start point 
            and components with differing dimensions.
        """
        vector = parse_vector(*components)
        if len(vector) == 2:
            cartesian = trig.polar_to_cartesian(vector)
        else:
            cartesian = trig.spherical_to_cartesian(vector)
        if len(start) != len(cartesian):
            raise ValueError("start and vector must be the same dimension,"
                             f" got: {len(start)} and {len(cartesian)}")
        return cls(start, np.array(start) + cartesian, uid)
    # Getters #
    @property
    def direction(self) -> tuple[Real]:
        """The direction of the line segment defined as the unit vector pointing 
        from start to end with cartesian components.
        
        The direction will not always be the same sign as the LineSegment's Line
        direction since it depends on point a and b's order and Line's does not.
        
        :getter: Returns the direction of the line segment.
        :setter: Read-only.
        """
        vector_ab = np.array(self.end) - np.array(self.start)
        unit_vector_ab = trig.get_unit_vector(vector_ab)
        return trig.to_1d_tuple(unit_vector_ab)
    @property
    def direction_polar(self) -> tuple[Real]:
        """The direction of the line segment defined as the unit vector pointing 
        from start to end with polar components.
        
        :getter: Returns the direction of the line segment as (r, phi). Phi is 
            the azimuth angle in radians.
        :setter: Read-only.
        """
        return trig.cartesian_to_polar(self.direction)
    @property
    def direction_spherical(self) -> tuple[Real]:
        """The direction of the line segment defined as the unit vector pointing 
        from start to end with spherical components.
        
        :getter: Returns the direction of the line segment as (r, phi, theta). 
            Phi is the azimuth angle in radians. Theta is the inclination angle 
            in radians.
        :setter: Read-only.
        """
        return trig.cartesian_to_spherical(self.direction)
    @property
    def length(self) -> float:
        """The length of the line segment. Defined as the distance between 
        points a and b.
        
        :getter: Returns the length of the line segment.
        :setter: Read-only.
        """
        return float(np.linalg.norm(self.get_vector_ab()))
    @property
    def phi(self) -> Real:
        """The azimuth angle of the vector from point a to point b.
        
        :getter: Returns the azimuth angle in radians.
        :setter: Read-only.
        """
        return trig.phi_of_cartesian(self.direction)
    @property
    def start(self) -> Point:
        """The start Point of the line segment.
        
        :getter: Returns the start point of the line segment.
        :setter: Updates point a to match the location of a new Point.
        """
        return self._start
    @property
    def end(self) -> Point:
        """The end Point of the line segment.
        
        :getter: Returns the end point of the line segment.
        :setter: Updates point b to match the location of a new Point.
        """
        return self._end
    @property
    def theta(self) -> Real:
        """The inclination angle of the vector from point a to point b.
        
        :getter: Returns the inclination angle in radians.
        :setter: Read-only.
        """
        return trig.theta_of_cartesian(self.direction)
    # Setters #
    @start.setter
    def start(self, pt: Point) -> None:
        self.update_points(pt, self.end)
    @end.setter
    def end(self, pt: Point) -> None:
        self.update_points(self.start, pt)
    # Public Methods #
    def copy(self) -> LineSegment:
        """Returns a copy of the LineSegment.
        
        :returns: A new LineSegment with new start and end points at the same 
            position as this LineSegment, but with no uids assigned.
        """
        return LineSegment(self.start.copy(), self.end.copy())
    def get_fit_box(self) -> tuple[Point, Point]:
        """Returns the corner points of the smallest axis-aligned box that fits 
        the line segment.
        
        :returns: A tuple of the minimum and maximum points of the fit box.
        """
        min_coordinates = (min(self.start.x, self.end.x),
                           min(self.start.y, self.end.y))
        max_coordinates = (max(self.start.x, self.end.x),
                           max(self.start.y, self.end.y))
        if len(self) == 3:
            min_coordinates += (min(self.start.z, self.end.z),)
            max_coordinates += (max(self.start.z, self.end.z),)
        return (Point(min_coordinates), Point(max_coordinates))
    def get_length(self) -> float:
        """Returns the length of the LineSegment."""
        return self.length
    def get_reference(self,
                      reference: ConstraintReference) -> LineSegment | Point:
        """Returns reference geometry for use in external modules like 
        constraints.
        
        :param reference: A ConstraintReference enumeration value applicable to 
            LineSegments. See :attr:`LineSegment.REFERENCES`.
        :returns: The geometry corresponding to the reference.
        """
        match reference:
            case ConstraintReference.CORE:
                return self
            case ConstraintReference.START:
                return self._start
            case ConstraintReference.END:
                return self._end
            case _:
                raise ValueError(f"{self.__class__}s do not have any"
                                 f" {reference.name} reference geometry")
    def get_all_references(self) -> tuple[ConstraintReference]:
        """Returns all ConstraintReferences applicable to LineSegments. See 
        :attr:`LineSegment.REFERENCES`.
        """
        return self.REFERENCES
    def get_x_length(self) -> Real:
        """Returns the distance along the x axis from point a to point b."""
        return abs(self.start.x - self.end.x)
    def get_y_length(self) -> Real:
        """Returns the distance along the y axis from point a to point b."""
        return abs(self.start.y - self.end.y)
    def get_z_length(self) -> Real:
        """Returns the distance along the z axis from point a to point b."""
        return abs(self.start.z - self.end.z)
    def get_line(self) -> Line:
        """Returns the infinite Line coincident with points a and b."""
        return Line.from_two_points(self.start, self.end)
    def get_vector_ab(self, numpy_vector: bool=True) -> np.ndarray | tuple:
        """Returns the non-unit-vector from point a to point b.
        
        :param numpy_vector: Whether to return a numpy array or tuple. Defaults 
            to True.
        :returns: A numpy array if numpy_vector is True, otherwise returns a 
            tuple.
        """
        np_vector_ab = np.array(self.end) - np.array(self.start)
        if numpy_vector:
            return np_vector_ab
        return trig.to_1d_tuple(np_vector_ab)
    def set_length_from_a(self, value: Real) -> Self:
        """Sets the length of the line segment relative to point a by keeping 
        point a in the same location and moving point b along the current 
        line direction. Raises a ValueError if the value is 0.
        
        :param value: The new LineSegment length from a.
        :returns: The updated LineSegment.
        """
        if value != 0:
            new_vector_ab = np.array(self.direction) * value
            self.end.cartesian = (np.array(self.start.cartesian)
                                      + new_vector_ab)
            return self
        raise ValueError("Line Length cannot be set to 0")
    def set_length_from_b(self, value: Real) -> Self:
        """Sets the length of the line segment relative to point b by keeping 
        point b in the same location and moving point a along the current 
        line direction to meet the new length. Raises a ValueError if the value 
        is 0.
        
        :param value: The new LineSegment length from b.
        :returns: The updated LineSegment.
        """
        if value != 0:
            new_vector_ab = np.array(self.direction) * value
            self.start.cartesian = (np.array(self.end.cartesian)
                                      - new_vector_ab)
            return self
        raise ValueError("Line Length cannot be set to 0")
    def set_x_length_from_a(self, value: Real) -> Self:
        """Same as :meth:`set_length_from_a`, but only along the x axis and does 
        not raise a ValueError if set to 0.
        """
        return self._update_axis_length(value, 0, True)
    def set_x_length_from_b(self, value: Real) -> Self:
        """Same as :meth:`set_length_from_b`, but only along the x axis and does 
        not raise a ValueError if set to 0.
        """
        return self._update_axis_length(value, 0, False)
    def set_y_length_from_a(self, value: Real) -> Self:
        """Same as :meth:`set_x_length_from_a`, but only along the y axis."""
        return self._update_axis_length(value, 1, True)
    def set_y_length_from_b(self, value: Real) -> Self:
        """Same as :meth:`set_x_length_from_b`, but only along the y axis."""
        return self._update_axis_length(value, 1, False)
    def set_z_length_from_a(self, value: Real) -> Self:
        """Same as :meth:`set_x_length_from_a`, but only along the z axis."""
        return self._update_axis_length(value, 2, True)
    def set_z_length_from_b(self, value: Real) -> Self:
        """Same as :meth:`set_x_length_from_b`, but only along the z axis."""
        return self._update_axis_length(value, 2, False)
    def update(self, other: LineSegment) -> Self:
        """Updates the points of the line segment to match the points of another 
        line segment.
        
        :param other: The line segment to update to.
        :returns: The updated LineSegment.
        """
        return self.update_points(other.start, other.end)
    def update_points(self, start: Point, end: Point) -> Self:
        """Updates (or initializes if not available) the points of the line 
        segment. Raises ValueErrors if the points are the same or if the points 
        do not share the same number of dimensions.
        
        :param start: The Point to update the start point to.
        :param end: The Point to update the end point to.
        :returns: The updated LineSegment.
        """
        if start == end:
            raise ValueError("points are at the same position")
        if len(start) != len(end):
            raise ValueError("points must be the same dimension")
        self._start.cartesian = start.cartesian
        self._end.cartesian = end.cartesian
        return self
    def _update_axis_length(self,
                            value: Real,
                            axis: int,
                            from_start: bool) -> Self:
        """Updates the distance between the points along the specified axis.
        
        :param value: The new distance along the axis.
        :param axis: 0 for x, 1 for y, and 2 for z.
        :param from_start: Whether to update the length from point a or b.
        :returns: The updated LineSegment.
        """
        new_vector_ab = self.get_vector_ab()
        new_vector_ab[axis] = value * copysign(1, self.direction[axis])
        if from_start:
            self.end.cartesian = (np.array(self.start.cartesian)
                                      + new_vector_ab)
        else:
            self.start.cartesian = (np.array(self.end.cartesian)
                                      - new_vector_ab)
        return self
    # Python Dunders #
    def __conform__(self, protocol: PrepareProtocol) -> str:
        if protocol is PrepareProtocol:
            return ";".join(map(str, [*self.start, *self.end]))
        raise TypeError(f"Expected sqlite3.PrepareProtocol, got {protocol}")
    def __copy__(self) -> LineSegment:
        """Returns a copy of the LineSegment that has the same points and line, 
        but no assigned uid.
        """
        return self.copy()
    def __eq__(self, other: LineSegment) -> bool:
        """Rich comparison for LineSegment equality that allows for line
        segments to be directly compared with ==.
        
        :param other: The point to compare self to.
        :returns: Whether the line segments' points are equal, which implies the 
                  lines are also equal.
        """
        if isinstance(other, LineSegment):
            return (
                self.start == other.start
                and self.end == other.end
            )
        return NotImplemented
    def __len__(self) -> int:
        """Returns the number of elements in the line segment's start, which 
        is equivalent to the line segment's number of dimnesions.
        """
        return len(self.start)
    def __str__(self) -> str:
        pt_a_strs, pt_b_strs = [], []
        for i in range(0, len(self)):
            if isclose0(self.start[i]):
                pt_a_strs.append("0")
            else:
                pt_a_strs.append(f"{self.start[i]:g}")
            if isclose0(self.end[i]):
                pt_b_strs.append("0")
            else:
                pt_b_strs.append(f"{self.end[i]:g}")
        pt_a_str = ",".join(pt_a_strs)
        pt_b_str = ",".join(pt_b_strs)
        prefix = super().__str__()
        return f"{prefix}({pt_a_str})({pt_b_str})>"
