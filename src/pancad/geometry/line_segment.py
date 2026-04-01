"""A module providing a class to represent line segments in all CAD programs,
graphics, and other geometry use cases.
"""
from __future__ import annotations

from math import copysign
from numbers import Real
from sqlite3 import PrepareProtocol
from typing import TYPE_CHECKING

import numpy as np

from pancad.abstract import AbstractGeometry
from pancad.constants import ConstraintReference
from pancad.geometry.point import Point
from pancad.geometry.line import Line
from pancad.utils import trigonometry as trig
from pancad.utils.geometry import parse_vector
from pancad.utils.pancad_types import VectorLike

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Self


class LineSegment(AbstractGeometry):
    """A class representing finite lines in 2D and 3D space.

    :param start: The start point of the line segment.
    :param end: The end point of the line segment.
    :param uid: The unique id of the line segment.
    """
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
        for child in [self._start, self._end]:
            child.parent = self
        self.update_points(start, end)
        self.uid = uid
        super().__init__(
            {
                ConstraintReference.CORE: self,
                ConstraintReference.START: self.start,
                ConstraintReference.END: self.end,
            }
        )

    # Class Methods
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

    # Properties
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
    def start(self) -> Point:
        """The start Point of the line segment.

        :getter: Returns the start point of the line segment.
        :setter: Updates point a to match the location of a new Point.
        """
        return self._start

    @start.setter
    def start(self, pt: Point) -> None:
        self.update_points(pt, self.end)

    @property
    def end(self) -> Point:
        """The end Point of the line segment.

        :getter: Returns the end point of the line segment.
        :setter: Updates point b to match the location of a new Point.
        """
        return self._end

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

    def is_equal(self, other: LineSegment) -> bool:
        return self.start.is_equal(other.start) and self.end.is_equal(other.end)

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

    def get_line(self) -> Line:
        """Returns the infinite Line coincident with points a and b."""
        return Line.from_two_points(self.start, self.end)

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

    # Python Dunders
    def __conform__(self, protocol: PrepareProtocol) -> str:
        if protocol is PrepareProtocol:
            return ";".join(map(str, [*self.start, *self.end]))
        raise TypeError(f"Expected sqlite3.PrepareProtocol, got {protocol}")

    def __copy__(self) -> LineSegment:
        """Returns a copy of the LineSegment that has the same points and line,
        but no assigned uid.
        """
        return self.copy()

    def __len__(self) -> int:
        """Returns the number of elements in the line segment's start, which
        is equivalent to the line segment's number of dimnesions.
        """
        return len(self.start)

    def __repr__(self) -> str:
        pt_a_strs, pt_b_strs = [], []
        for i in range(0, len(self)):
            if np.isclose(self.start[i], 0):
                pt_a_strs.append("0")
            else:
                pt_a_strs.append(f"{self.start[i]:g}")
            if np.isclose(self.end[i], 0):
                pt_b_strs.append("0")
            else:
                pt_b_strs.append(f"{self.end[i]:g}")
        start_str = ",".join(pt_a_strs)
        end_str = ",".join(pt_b_strs)
        return super().__repr__().format(
            details=f"({start_str})({end_str})"
        )
