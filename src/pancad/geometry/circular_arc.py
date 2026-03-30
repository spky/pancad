"""A module providing a class to represent circular arcs in all CAD programs, 
graphics, and other geometry use cases.
"""
from __future__ import annotations

from dataclasses import dataclass
from sqlite3 import PrepareProtocol
from typing import TYPE_CHECKING

import numpy as np

from pancad.abstract import AbstractGeometry
from pancad.constants import ConstraintReference
from pancad.geometry.point import Point
from pancad.utils.geometry import (
    three_dimensional_only, two_dimensional_only, no_dimensional_mismatch
)
from pancad.utils.pancad_types import VectorLike
from pancad.utils.trigonometry import (
    get_unit_vector, to_1d_tuple, phi_of_cartesian, polar_to_cartesian,
)

if TYPE_CHECKING:
    from numbers import Real
    from typing import Self


@dataclass
class ArcParts:
    """A dataclass containing the geometric parts of a Circular Arc."""
    center: Point
    start: Point
    end: Point
    clockwise: bool
    normal: tuple[Real, Real, Real] = None

    @property
    def radius(self) -> Real:
        """The radius of the arc derived from the center and start."""
        return np.linalg.norm(self.start - self.center)

    @property
    def start_vector(self) -> tuple[Real, Real] | tuple[Real, Real, Real]:
        """The unit vector from the center to the start, derived from start."""
        return to_1d_tuple(get_unit_vector(self.start - self.center))

    @property
    def end_vector(self) -> tuple[Real, Real] | tuple[Real, Real, Real]:
        """The unit vector from the center to the end, derived from end."""
        return to_1d_tuple(get_unit_vector(self.end - self.center))

class CircularArc(AbstractGeometry):
    """A class representing a circular arc in 2D or 3D space.
    
    :param center: The center point of the arc.
    :param radius: The radius dimension of the arc.
    :param start: A vector pointing to the start of the arc.
    :param end: A vector pointing to the end of the arc.
    :param is_clockwise: Sets whether the arc travels clockwise from the start 
        point to the end point.
    :param normal: The vector normal to the start and end vectors that defines 
        which direction is clockwise. Required for 3D arcs.
    :param uid: The unique ID of the circle.
    """
    def __init__(self,
                 center: Point | VectorLike,
                 radius: Real,
                 start: VectorLike,
                 end: VectorLike,
                 is_clockwise: bool,
                 normal: VectorLike | None=None,
                 uid: str=None) -> None:
        # pylint: disable=too-many-positional-arguments, too-many-arguments
        # Ok here because packing it smaller would require arbitrary lists or
        # dicts. Arcs just need this many arguments.
        if isinstance(center, VectorLike):
            center = Point(center)
        if len(center) == 2 and normal is not None:
            raise ValueError("Normal must be none for 2D arcs")
        if any(dim != len(center) for dim in map(len, [start, end])):
            vectors = {"Center": tuple(center), "Start": start, "End": end}
            raise ValueError(f"Vectors not all the same length, got {vectors}")
        start = Point(center + radius * get_unit_vector(start))
        end = Point(center + radius * get_unit_vector(end))
        if normal:
            normal = get_unit_vector(normal)
        self._parts = ArcParts(center.copy(), start, end, is_clockwise, normal)
        self.uid = uid
        super().__init__(
            {
                ConstraintReference.CORE: self,
                ConstraintReference.CENTER: self._parts.center,
                ConstraintReference.START: self._parts.start,
                ConstraintReference.END: self._parts.end,
            }
        )

    @classmethod
    def from_angles(cls,
                    center: Point | VectorLike,
                    radius: Real,
                    start_angle: Real,
                    end_angle: Real,
                    is_clockwise: bool,
                    uid: str=None) -> None:
        """Initializes a 2D CircularArc using start and end angles instead of 
        vectors.
        
        :param center: The center point of the arc.
        :param radius: The radius dimension of the arc.
        :param start_angle: The angle from the horizontal axis to the line 
            between the center and the start of the arc in radians.
        :param end_angle: The angle from the horizontal axis to the line 
            between the center and the end of the arc in radians.
        :param is_clockwise: Sets whether the arc travels clockwise from the 
            start point to the end point.
        :param uid: The unique ID of the circle.
        :raises ValueError: Raised if the center point is 3D since 3D arcs
            cannot be defined by angles.
        """
        # pylint: disable=too-many-positional-arguments, too-many-arguments
        # Ok here because packing it smaller would require arbitrary lists or
        # dicts. Arcs just need this many arguments.
        if len(center) == 3:
            raise ValueError("3D CircularArcs cannot be initialized by angles")
        if isinstance(center, VectorLike):
            center = Point(center)
        start_vector = polar_to_cartesian((1, start_angle))
        end_vector = polar_to_cartesian((1, end_angle))
        return cls(center, radius, start_vector, end_vector, is_clockwise,
                   uid=uid)

    # Properties #
    @property
    def center(self) -> Point:
        """Center point of the arc.
        
        :getter: Returns the center point.
        :setter: Updates center to new point. Start and end get updated to match.
        """
        return self._parts.center
    @center.setter
    @no_dimensional_mismatch
    def center(self, point: Point | VectorLike) -> None:
        if isinstance(point, VectorLike):
            point = Point(point)
        # Store initial vectors before changing center
        start_vector = np.array(self.start_vector)
        end_vector = np.array(self.end_vector)
        self._parts.center.update(point)
        self._parts.start.update(Point(start_vector + point))
        self._parts.end.update(Point(end_vector + point))

    @property
    def is_clockwise(self) -> bool:
        """A boolean that sets whether the arc travels clockwise or 
        counterclockwise from its start point to its end point.
        """
        return self._parts.clockwise
    @is_clockwise.setter
    def is_clockwise(self, value: bool) -> None:
        self._parts.clockwise = value

    @property
    def diameter(self) -> Real:
        """Diameter of the arc.
        
        :getter: Returns the twice the arc's radius value.
        :setter: Updates the arc's radius value with half the provided value.
        :raises ValueError: Raised if provided a value less than 0.
        """
        return 2 * self.radius
    @diameter.setter
    def diameter(self, value: Real) -> None:
        self.radius = value / 2

    @property
    def end(self) -> Point:
        """The end point of the arc. Read-only."""
        return self._parts.end

    @property
    @two_dimensional_only
    def end_angle(self) -> Real:
        """The angle from the positive horizontal axis to the end_vector in 
        radians. Bounded -pi < angle <= pi.
        
        :getter: Returns the calculated angle of the end_vector relative to the 
            positive horizontal axis in radians.
        :setter: Sets the end_vector based on the value given in radians.
        :raises ValueError: Raised if accessed on a 3D arc.
        """
        return phi_of_cartesian(self.end_vector)
    @end_angle.setter
    @two_dimensional_only
    def end_angle(self, angle: Real) -> None:
        self.end_vector = polar_to_cartesian((1, angle))

    @property
    def end_vector(self) -> tuple[Real, Real] | tuple[Real, Real, Real]:
        """The unit vector pointing to the end of the arc from its center.
        
        :getter: Returns the vector.
        :setter: Sets the unit vector of the provided vector to the end vector 
            and updates the end point's position.
        """
        return self._parts.end_vector
    @end_vector.setter
    @no_dimensional_mismatch
    def end_vector(self, vector: VectorLike) -> None:
        self._parts.end.update(
            Point(self._parts.center + self.radius * get_unit_vector(vector))
        )

    @property
    @three_dimensional_only
    def normal_vector(self) -> tuple[Real] | None:
        """The unit vector defining the direction of clockwise for 3D arcs."""
        return self._parts.normal
    @normal_vector.setter
    @three_dimensional_only
    @no_dimensional_mismatch
    def normal_vector(self, vector: VectorLike | None) -> None:
        self._parts.normal = vector

    @property
    def radius(self) -> Real:
        """Radius of the arc.
        
        :raises ValueError: Raised if provided a value less than 0.
        """
        return self._parts.radius
    @radius.setter
    def radius(self, value: Real) -> None:
        if value < 0:
            raise ValueError(f"Radius cannot be < 0. Given: {value}")
        new_start = Point(self.center + value * np.array(self.start_vector))
        new_end = Point(self.center + value * np.array(self.end_vector))
        self._parts.start.update(new_start)
        self._parts.end.update(new_end)

    @property
    def start(self) -> Point:
        """The start point of the arc. Read-only."""
        return self._parts.start

    @property
    @two_dimensional_only
    def start_angle(self) -> Real:
        """The angle from the positive horizontal axis to the start_vector in 
        radians. Bounded -pi < angle <= pi.
        
        :raises ValueError: Raised if accessed on a 3D arc.
        """
        return phi_of_cartesian(self.start_vector)
    @start_angle.setter
    @two_dimensional_only
    def start_angle(self, angle: Real) -> None:
        self.start_vector = polar_to_cartesian((1, angle))

    @property
    def start_vector(self) -> tuple[Real]:
        """The unit vector pointing to the start of the arc from its center.
        
        :getter: Returns the vector.
        :setter: Sets the unit vector of the provided vector to the end vector 
            and updates the start point's position.
        """
        return self._parts.start_vector
    @start_vector.setter
    @no_dimensional_mismatch
    def start_vector(self, vector: VectorLike) -> None:
        new_start = Point(self.center + self.radius * get_unit_vector(vector))
        self._parts.start.update(new_start)

    # Public Methods #
    @no_dimensional_mismatch
    def update(self, other: CircularArc) -> Self:
        """Updates the center point, radius, start/end vectors and is_clockwise
        to match the other CircularArc.
        
        :param other: A CircularArc to update this CircularArc to.
        :returns: The updated CircularArc.
        """
        self.center = other.center
        self.radius = other.radius
        self.start_vector = other.start_vector
        self.end_vector = other.end_vector
        self.is_clockwise = other.is_clockwise
        if len(self) == 3:
            self.normal_vector = other.normal_vector
        return self

    def is_equal(self, other: CircularArc) -> bool:
        return all(
            [
                self.radius == other.radius,
                self.center.is_equal(other.center),
                np.allclose(self.start_vector, other.start_vector),
                np.allclose(self.end_vector, other.end_vector),
                self.is_clockwise == other.is_clockwise,
            ]
        )

    # Python Dunders
    def __conform__(self, protocol: PrepareProtocol) -> str:
        if protocol is PrepareProtocol:
            if len(self) == 3:
                raise NotImplementedError("3D CircularArcs not implemented yet")
            vectors = [self.center.cartesian, self.start_vector, self.end_vector]
            vector_strings = map(lambda v: ";".join(map(str, v)), vectors)
            return "|".join(
                [
                    *vector_strings,
                    str(int(self.is_clockwise)),
                    str(self.radius),
                ]
            )
        raise TypeError(f"Expected sqlite3.PrepareProtocol, got {protocol}")

    def __copy__(self) -> CircularArc:
        """Returns a copy of the arc with the same radius, center point, 
        start/end vectors, but with no assigned uid.
        """
        return CircularArc(self.center,
                           self.radius,
                           self.start_vector,
                           self.end_vector,
                           self.is_clockwise,
                           self.normal_vector)

    def __len__(self) -> int:
        """Returns whether the arc is 2D or 3D."""
        return len(self.center)

    def __repr__(self) -> str:
        center_str = str(self.center.cartesian).replace(" ","")
        start_str = str(self.start.cartesian).replace(" ","")
        end_str = str(self.end.cartesian).replace(" ","")
        return super().__repr__().format(
            details=f"{center_str}c{start_str}s{end_str}e{self.radius}r"
        )
