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
from pancad.utils.trigonometry import (
    get_unit_vector, to_1d_tuple, phi_of_cartesian, polar_to_cartesian,
)

if TYPE_CHECKING:
    from numbers import Real
    from typing import Self, Literal

    from pancad.utils.pancad_types import SpaceVector, Space3DVector


@dataclass
class ArcParts:
    """A dataclass containing the geometric parts of a Circular Arc."""
    center: Point
    start: Point
    end: Point
    clockwise: bool
    normal: Space3DVector = None

    def __post_init__(self) -> None:
        """Verifies arc part validity."""
        if len(self.center) == 3:
            raise NotImplementedError("3D Arcs not yet implemented, see issue #143")
        if len(self.center) == 2 and self.normal is not None:
            raise ValueError(f"Normal must be None for 2D arcs, got {self.normal}")
        if any(dim != len(self.center) for dim in map(len, [self.start, self.end])):
            vectors = {"Center": tuple(self.center), "Start": self.start, "End": self.end}
            raise ValueError(f"Dimensional mismatch during arc init. Got: {vectors}")

    @property
    def radius(self) -> Real:
        """The radius of the arc derived from the center and start."""
        return np.linalg.norm(self.start - self.center)

    @radius.setter
    def radius(self, value: Real) -> None:
        if value < 0:
            raise ValueError(f"Radius cannot be < 0. Got: {value}")
        for name, point in {"start": self.start, "end": self.end}.items():
            new = Point(self.center + value * np.array(self.get_vector(name)))
            point.update(new)

    def get_vector(self, name: Literal["start", "end"]) -> SpaceVector:
        """Returns the unit vector from the center to the specified point."""
        try:
            point = {"start": self.start, "end": self.end}[name]
        except KeyError as exc:
            msg = f"Unexpected name option, must be 'start' or 'end'. Got: {name}"
            raise TypeError(msg) from exc
        return to_1d_tuple(get_unit_vector(point - self.center))

    def update_center(self, new: Point) -> Self:
        """Updates the arc's center point while keeping the start and end points
        in their same relative locations.
        """
        # Store initial vectors before changing center
        start_vector = np.array(self.get_vector("start"))
        end_vector = np.array(self.get_vector("end"))
        self.center.update(new)
        self.update_with_vector("start", start_vector)
        self.update_with_vector("end", end_vector)

    def update_with_angle(self, name: Literal["start", "end"], angle: Real) -> Self:
        """Updates the start or end points of the arc using a new angle from the
        positive horizontal axis.
        """
        new_vector = polar_to_cartesian((1, angle))
        self.update_with_vector(name, new_vector)
        return self

    def update_with_vector(self, name: Literal["start", "end"], vector: SpaceVector) -> Self:
        """Updates the start or end points of the arc using a new vector."""
        new = self.center + self.radius * get_unit_vector(vector)
        point_map = {"start": self.start, "end": self.end}
        try:
            point_map[name].update(Point(new))
        except KeyError as exc:
            msg = f"Unexpected name option, must be 'start' or 'end'. Got: {name}"
            raise TypeError(msg) from exc
        return self

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

    :raises ValueError: When normal is not None for a 2D arc or if the
        dimensions of center, start, and end do not all match.
    """
    def __init__(self,
                 center: Point | SpaceVector,
                 radius: Real,
                 start: SpaceVector,
                 end: SpaceVector,
                 is_clockwise: bool,
                 normal: SpaceVector | None=None,
                 uid: str=None) -> None:
        # pylint: disable=too-many-positional-arguments, too-many-arguments
        # Ok here because packing it smaller would require arbitrary lists or
        # dicts. Arcs just need this many arguments.
        if not isinstance(center, Point):
            center = Point(center)
        start = Point(center + radius * get_unit_vector(start))
        end = Point(center + radius * get_unit_vector(end))
        if normal is not None:
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
                    center: Point | SpaceVector,
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
    def center(self, point: Point | SpaceVector) -> None:
        if not isinstance(point, Point):
            point = Point(point)
        self._parts.update_center(point)

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
        return 2 * self._parts.radius

    @diameter.setter
    def diameter(self, value: Real) -> None:
        self._parts.radius = value / 2

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
        :raises ValueError: Raised when accessed on a 3D arc.
        """
        return phi_of_cartesian(self._parts.get_vector("end"))

    @end_angle.setter
    @two_dimensional_only
    def end_angle(self, angle: Real) -> None:
        self._parts.update_with_angle("end", angle)

    @property
    def end_vector(self) -> SpaceVector:
        """The unit vector pointing to the end of the arc from its center.

        :getter: Returns the vector.
        :setter: Sets the unit vector of the provided vector to the end vector
            and updates the end point's position.
        """
        return self._parts.get_vector("end")

    @end_vector.setter
    @no_dimensional_mismatch
    def end_vector(self, vector: SpaceVector) -> None:
        self._parts.update_with_vector("end", vector)

    @property
    @three_dimensional_only
    def normal_vector(self) -> tuple[Real] | None:
        """The unit vector defining the direction of clockwise for 3D arcs."""
        return self._parts.normal

    @normal_vector.setter
    @three_dimensional_only
    @no_dimensional_mismatch
    def normal_vector(self, vector: SpaceVector | None) -> None:
        self._parts.normal = vector

    @property
    def radius(self) -> Real:
        """Radius of the arc.

        :raises ValueError: Raised if provided a value less than 0.
        """
        return self._parts.radius

    @radius.setter
    def radius(self, value: Real) -> None:
        self._parts.radius = value

    @property
    def start(self) -> Point:
        """The start point of the arc. Read-only."""
        return self._parts.start

    @property
    @two_dimensional_only
    def start_angle(self) -> Real:
        """The angle from the positive horizontal axis to the start_vector in
        radians. Bounded -pi < angle <= pi.

        :raises ValueError: Raised when accessed on a 3D arc.
        """
        return phi_of_cartesian(self._parts.get_vector("start"))

    @start_angle.setter
    @two_dimensional_only
    def start_angle(self, angle: Real) -> None:
        self._parts.update_with_angle("start", angle)

    @property
    def start_vector(self) -> SpaceVector:
        """The unit vector pointing to the start of the arc from its center.

        :getter: Returns the vector.
        :setter: Sets the unit vector of the provided vector to the end vector
            and updates the start point's position.
        """
        return self._parts.get_vector("start")

    @start_vector.setter
    @no_dimensional_mismatch
    def start_vector(self, vector: SpaceVector) -> None:
        self._parts.update_with_vector("start", vector)

    # Public Methods #
    @no_dimensional_mismatch
    def update(self, other: CircularArc) -> Self:
        """Updates the center point, radius, start/end vectors and is_clockwise
        to match the other CircularArc.

        :param other: A CircularArc to update this CircularArc to.
        :returns: The updated CircularArc.
        """
        self._parts.update_center(other.center)
        self._parts.radius = other.radius
        self._parts.update_with_vector("start", other.start_vector)
        self._parts.update_with_vector("end", other.end_vector)
        self._parts.clockwise = other.is_clockwise
        if len(self) == 3:
            self._parts.normal = other.normal_vector
        return self

    def is_equal(self, other: CircularArc) -> bool:
        return all(
            [
                self._parts.radius == other.radius,
                self._parts.center.is_equal(other.center),
                np.allclose(self._parts.get_vector("start"), other.start_vector),
                np.allclose(self._parts.get_vector("end"), other.end_vector),
                self._parts.clockwise == other.is_clockwise,
            ]
        )

    # Python Dunders
    def __conform__(self, protocol: PrepareProtocol) -> str:
        if protocol is PrepareProtocol:
            if len(self) == 3:
                raise NotImplementedError("3D CircularArcs not implemented yet")
            vectors = [
                self._parts.center.cartesian,
                self._parts.get_vector("start"),
                self._parts.get_vector("end"),
            ]
            vector_strings = map(lambda v: ";".join(map(str, v)), vectors)
            return "|".join(
                [
                    *vector_strings,
                    str(int(self._parts.clockwise)),
                    str(self._parts.radius),
                ]
            )
        raise TypeError(f"Expected sqlite3.PrepareProtocol, got {protocol}")

    def __copy__(self) -> CircularArc:
        """Returns a copy of the arc with the same radius, center point,
        start/end vectors, but with no assigned uid.
        """
        return CircularArc(self._parts.center,
                           self._parts.radius,
                           self._parts.get_vector("start"),
                           self._parts.get_vector("end"),
                           self._parts.clockwise,
                           self._parts.normal)

    def __len__(self) -> int:
        """Returns whether the arc is 2D or 3D."""
        return len(self.center)

    def __repr__(self) -> str:
        center_str = str(self._parts.center.cartesian).replace(" ","")
        start_str = str(self._parts.start.cartesian).replace(" ","")
        end_str = str(self._parts.end.cartesian).replace(" ","")
        return super().__repr__().format(
            details=f"{center_str}c{start_str}s{end_str}e{self._parts.radius}r"
        )
