"""A module providing a class to represent line segments in all CAD programs, 
graphics, and other geometry use cases.
"""
from __future__ import annotations

from math import copysign
from functools import partial
from numbers import Real
from typing import TYPE_CHECKING, overload

import numpy as np

from PanCAD.geometry import AbstractGeometry, Point, Line
from PanCAD.geometry.constants import ConstraintReference
from PanCAD.utils import comparison, trigonometry as trig
from PanCAD.utils.pancad_types import VectorLike

if TYPE_CHECKING:
    from typing import Self

isclose0 = partial(comparison.isclose, value_b=0, nan_equal=False)

class LineSegment(AbstractGeometry):
    """A class representing finite lines in 2D and 3D space.
    
    :param point_a: The start point of the line segment.
    :param point_b: The end point of the line segment.
    :param uid: The unique id of the line segment.
    """
    
    REFERENCES = (ConstraintReference.CORE,
                  ConstraintReference.START,
                  ConstraintReference.END)
    """All relevant ConstraintReferences for LineSegments."""
    
    def __init__(self,
                 point_a: Point | VectorLike,
                 point_b: Point | VectorLike,
                 uid: str=None) -> None:
        if isinstance(point_a, VectorLike):
            point_a = Point(point_a)
        if isinstance(point_b, VectorLike):
            point_b = Point(point_b)
        
        self.update_points(point_a, point_b)
        self.uid = uid
    
    # Class Methods #
    @overload
    @classmethod
    def from_point_length_angle(cls,
                                point: Point | VectorLike,
                                length: VectorLike,
                                *,
                                uid: str=None) -> Self: ...
    
    @overload
    @classmethod
    def from_point_length_angle(cls,
                                point: Point | VectorLike,
                                length: Real,
                                phi: Real,
                                *,
                                uid: str=None) -> Self: ...
    
    @overload
    @classmethod
    def from_point_length_angle(cls,
                                point: Point | VectorLike,
                                length: Real,
                                phi: Real,
                                theta: Real,
                                *,
                                uid: str=None) -> Self: ...
    
    @classmethod
    def from_point_length_angle(cls, point, length, phi=None, theta=None,
                                *, uid=None):
        """Returns a LineSegment defined by a point and a length, azimuth angle 
        phi, and inclination angle theta relative to the point.
        
        :point: A Point, or iterable with 2 or 3 dimensions.
        :length: The length of the line segment, or a polar/spherical (r, phi, 
            theta) vector iterable.
        :phi: The azimuth angle of the line segment relative to the point in 
            radians.
        :theta: The inclination angle of the line segment relative to the point 
            in radians. If None or not given the LineSegment will be 2D.
        :returns: A line segment with its start at point, and end at the point's 
            position plus the polar/spherical vector.
        """
        length_number_input = isinstance(length, Real)
        if length_number_input and phi is not None and theta is None:
            vector_ab = trig.polar_to_cartesian((length, phi))
        elif length_number_input and phi is not None and theta is not None:
            vector_ab = trig.spherical_to_cartesian((length, phi, theta))
        elif isinstance(length, VectorLike) and phi is None:
            if len(length) == 2:
                vector_ab = trig.polar_to_cartesian(length)
            elif len(length) == 3:
                vector_ab = trig.spherical_to_cartesian(length)
            else:
                raise ValueError(f"Spherical/Polar Vector must have 2 or 3"
                                 f" elements, given {length}")
        elif (isinstance(length, VectorLike)
                and (phi is not None or theta is not None)):
            raise ValueError("phi/theta must not be given or None if a "
                             "polar/spherical vector was provided. Given"
                             f" Vector: {length}, phi: {phi}, theta: {theta}")
        elif length_number_input and phi is None:
            raise ValueError("If length is a number, phi must not be None")
        else:
            raise ValueError(f"Unhandled type combo given {point.__class__},"
                             f" {length.__class__}, {phi.__class__},"
                             f" {theta.__class__}")
        
        if len(point) == len(vector_ab):
            return cls(point, np.array(point) + vector_ab, uid)
        else:
            raise ValueError("Point and vector must have the same number of"
                             " dimensions")
    
    # Getters #
    @property
    def direction(self) -> tuple[Real]:
        """The direction of the line segment defined as the unit vector pointing 
        from point_a to point_b with cartesian components.
        
        The direction will not always be the same sign as the LineSegment's Line
        direction since it depends on point a and b's order and Line's does not.
        
        :getter: Returns the direction of the line segment.
        :setter: Read-only.
        """
        vector_ab = np.array(self.point_b) - np.array(self.point_a)
        unit_vector_ab = trig.get_unit_vector(vector_ab)
        return trig.to_1D_tuple(unit_vector_ab)
    
    @property
    def direction_polar(self) -> tuple[Real]:
        """The direction of the line segment defined as the unit vector pointing 
        from point_a to point_b with polar components.
        
        :getter: Returns the direction of the line segment as (r, phi). Phi is 
            the azimuth angle in radians.
        :setter: Read-only.
        """
        return trig.cartesian_to_polar(self.direction)
    
    @property
    def direction_spherical(self) -> tuple[Real]:
        """The direction of the line segment defined as the unit vector pointing 
        from point_a to point_b with spherical components.
        
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
    def point_a(self) -> Point:
        """The start Point of the line segment.
        
        :getter: Returns the start point of the line segment.
        :setter: Updates point a to match the location of a new Point.
        """
        return self._point_a
    
    @property
    def point_b(self) -> Point:
        """The end Point of the line segment.
        
        :getter: Returns the end point of the line segment.
        :setter: Updates point b to match the location of a new Point.
        """
        return self._point_b
    
    @property
    def theta(self) -> Real:
        """The inclination angle of the vector from point a to point b.
        
        :getter: Returns the inclination angle in radians.
        :setter: Read-only.
        """
        return trig.theta_of_cartesian(self.direction)
    
    # Setters #
    @point_a.setter
    def point_a(self, pt: Point) -> None:
        self.update_points(pt, self.point_b)
    
    @point_b.setter
    def point_b(self, pt: Point) -> None:
        self.update_points(self.point_a, pt)
    
    # Public Methods #
    def copy(self) -> LineSegment:
        """Returns a copy of the LineSegment.
        
        :returns: A new LineSegment with new start and end points at the same 
            position as this LineSegment, but with no uids assigned.
        """
        return self.__copy__()
    
    def get_fit_box(self) -> tuple[Point, Point]:
        """Returns the corner points of the smallest axis-aligned box that fits 
        the line segment.
        
        :returns: A tuple of the minimum and maximum points of the fit box.
        """
        min_coordinates = (min(self.point_a.x, self.point_b.x),
                           min(self.point_a.y, self.point_b.y))
        max_coordinates = (max(self.point_a.x, self.point_b.x),
                           max(self.point_a.y, self.point_b.y))
        if len(self) == 3:
            min_coordinates += (min(self.point_a.z, self.point_b.z),)
            max_coordinates += (max(self.point_a.z, self.point_b.z),)
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
                return self._point_a
            case ConstraintReference.END:
                return self._point_b
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
        return abs(self.point_a.x - self.point_b.x)
    
    def get_y_length(self) -> Real:
        """Returns the distance along the y axis from point a to point b."""
        return abs(self.point_a.y - self.point_b.y)
    
    def get_z_length(self) -> Real:
        """Returns the distance along the z axis from point a to point b."""
        return abs(self.point_a.z - self.point_b.z)
    
    def get_line(self) -> Line:
        """Returns the infinite Line coincident with points a and b."""
        return Line.from_two_points(self.point_a, self.point_b)
    
    def get_vector_ab(self, numpy_vector: bool=True) -> np.ndarray | tuple:
        """Returns the non-unit-vector from point a to point b.
        
        :param numpy_vector: Whether to return a numpy array or tuple. Defaults 
            to True.
        :returns: A numpy array if numpy_vector is True, otherwise returns a 
            tuple.
        """
        np_vector_ab = np.array(self.point_b) - np.array(self.point_a)
        if numpy_vector:
            return np_vector_ab
        else:
            return trig.to_1D_tuple(np_vector_ab)
    
    def set_length_from_a(self, value: Real) -> Self:
        """Sets the length of the line segment relative to point a by keeping 
        point a in the same location and moving point b along the current 
        line direction. Raises a ValueError if the value is 0.
        
        :param value: The new LineSegment length from a.
        :returns: The updated LineSegment.
        """
        if value != 0:
            new_vector_ab = np.array(self.direction) * value
            self.point_b.cartesian = (np.array(self.point_a.cartesian)
                                      + new_vector_ab)
            return self
        else:
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
            self.point_a.cartesian = (np.array(self.point_b.cartesian)
                                      - new_vector_ab)
            return self
        else:
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
        return self.update_points(other.point_a, other.point_b)
    
    def update_points(self, point_a: Point, point_b: Point) -> Self:
        """Updates (or initializes if not available) the points of the line 
        segment. Raises ValueErrors if the points are the same or if the points 
        do not share the same number of dimensions.
        
        :param point_a: The Point to update the start point to.
        :param point_b: The Point to update the end point to.
        :returns: The updated LineSegment.
        """
        if point_a == point_b:
            raise ValueError("Line Segments cannot be defined with 2 of the"
                             " same point""")
        elif len(point_a) == len(point_b):
            if hasattr(self, "_point_a"):
                # Update existing points
                self._point_a.cartesian = point_a.cartesian
                self._point_b.cartesian = point_b.cartesian
            else:
                # Initialize Points
                self._point_a = point_a
                self._point_b = point_b
            return self
        else:
            raise ValueError("point_a and point_b must have the same number of"
                             " dimensions to initialize a line segment")
    
    def _update_axis_length(self,
                            value: Real,
                            axis: int,
                            from_point_a: bool) -> Self:
        """Updates the distance between the points along the specified axis.
        
        :param value: The new distance along the axis.
        :param axis: 0 for x, 1 for y, and 2 for z.
        :param from_point_a: Whether to update the length from point a or b.
        :returns: The updated LineSegment.
        """
        new_vector_ab = self.get_vector_ab()
        new_vector_ab[axis] = value * copysign(1, self.direction[axis])
        if from_point_a:
            self.point_b.cartesian = (np.array(self.point_a.cartesian)
                                      + new_vector_ab)
        else:
            self.point_a.cartesian = (np.array(self.point_b.cartesian)
                                      - new_vector_ab)
        return self
    
    # Python Dunders #
    def __copy__(self) -> LineSegment:
        """Returns a copy of the LineSegment that has the same points and line, 
        but no assigned uid.
        """
        return LineSegment(self.point_a.copy(), self.point_b.copy())
    
    def __eq__(self, other: LineSegment) -> bool:
        """Rich comparison for LineSegment equality that allows for line
        segments to be directly compared with ==.
        
        :param other: The point to compare self to.
        :returns: Whether the line segments' points are equal, which implies the 
                  lines are also equal.
        """
        if isinstance(other, LineSegment):
            return (
                self.point_a == other.point_a
                and self.point_b == other.point_b
            )
        else:
            return NotImplemented
    
    def __len__(self) -> int:
        """Returns the number of elements in the line segment's point_a, which 
        is equivalent to the line segment's number of dimnesions.
        """
        return len(self.point_a)
    
    def __str__(self) -> str:
        pt_a_strs, pt_b_strs = [], []
        for i in range(0, len(self)):
            if isclose0(self.point_a[i]):
                pt_a_strs.append("0")
            else:
                pt_a_strs.append("{:g}".format(self.point_a[i]))
            if isclose0(self.point_b[i]):
                pt_b_strs.append("0")
            else:
                pt_b_strs.append("{:g}".format(self.point_b[i]))
        pt_a_str = ",".join(pt_a_strs)
        pt_b_str = ",".join(pt_b_strs)
        
        prefix = super().__str__()
        return f"{prefix}({pt_a_str})({pt_b_str})>"