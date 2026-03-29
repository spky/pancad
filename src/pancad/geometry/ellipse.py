"""A module providing a class to represent ellipses in all CAD programs, 
graphics, and other geometry use cases.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from math import atan2, cos, sin, sqrt
from numbers import Real
from typing import overload, Self

import numpy as np

from pancad.abstract import AbstractGeometry
from pancad.geometry.point import Point
from pancad.geometry.line import Line
from pancad.constants import ConstraintReference
from pancad.utils.geometry import two_dimensional_only, no_dimensional_mismatch
from pancad.utils.pancad_types import VectorLike
from pancad.utils.trigonometry import angle_mod, rotation_2



def updates_reference_points(func):
    """A wrapper to update the EllipseParts reference points after a change to 
    the other parts.
    """
    def wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        for direction, distance_map in self.parts.component_map.items():
            for reference, distance in distance_map.items():
                self.parts.reference_points[reference].update(
                    Point(self.parts.center + distance * np.array(direction))
                )
        return result
    return wrapper


@dataclass
class EllipseParts:
    """A dataclass containing the geometric parts of an Ellipse."""
    center: Point
    major_semidiameter: Real
    minor_semidiameter: Real
    major_axis: Line
    minor_axis: Line
    reference_points: dict[ConstraintReference, Point] = field(init=False)

    @property
    def linear_eccentricity(self) -> Real:
        """Returns the linear eccentricity value of the Ellipse."""
        return sqrt(self.major_semidiameter**2 - self.minor_semidiameter**2)

    @property
    def component_map(self) -> dict[tuple, dict[ConstraintReference, Real]]:
        """Maps the reference point's direction and constraint reference to a 
        distance from the center.
        """
        return {
            self.major_axis.direction: {
                ConstraintReference.X_MAX: self.major_semidiameter,
                ConstraintReference.X_MIN: -self.major_semidiameter,
                ConstraintReference.FOCAL_PLUS: self.linear_eccentricity,
                ConstraintReference.FOCAL_MINUS: -self.linear_eccentricity,
            },
            self.minor_axis.direction: {
                ConstraintReference.Y_MAX: self.minor_semidiameter,
                ConstraintReference.Y_MIN: -self.minor_semidiameter,
            },
        }

    def __post_init__(self):
        self.reference_points = {}
        for direction, distance_map in self.component_map.items():
            for reference, distance in distance_map.items():
                self.reference_points[reference] = (
                    Point(self.center + distance * np.array(direction))
                )

class Ellipse(AbstractGeometry):
    """A class representing an ellipse in 2D or 3D space.
    
    :param center: The center point of the ellipse.
    :param semi_major_axis: The length of the ellipse's **initial** longest 
        semidiameter. This length will continue to represent the same axis 
        orientation even if the user changes the value to be shorter than the 
        semi-minor axis since the alternative would be semantically correct but 
        very confusing to modify. The lengths will not be compared by pancad 
        since this could be read from an already defined ellipse that has 
        already switched the values.
    :param semi_minor_axis: The length of the ellipse's **initial** shortest 
        semidiameter. Same caveats as the semi_major_axis regarding changes.
    :param major_direction: The direction of the Ellipse's major axis.
    :param minor_direction: The direction of the Ellipse's minor axis.
    :param uid: The unique ID of the ellipse. Defaults to None.
    :raises ValueError: When minor_direction is provided for a 2D ellipse or not 
        provided for a 3D ellipse.
    """

    @overload
    def __init__(self,
                 center: Point | VectorLike,
                 semi_major_axis: Real,
                 semi_minor_axis: Real,
                 major_direction: VectorLike,
                 uid: str | None=None) -> None: ...

    @overload
    def __init__(self,
                 center: Point | VectorLike,
                 semi_major_axis: Real,
                 semi_minor_axis: Real,
                 major_direction: VectorLike,
                 minor_direction: VectorLike,
                 uid: str | None=None) -> None: ...

    def __init__(self, center, semi_major_axis, semi_minor_axis,
                 major_direction, minor_direction=None, uid=None):
        if isinstance(center, VectorLike):
            center = Point(center)
        if len(center) == 2 and minor_direction is not None:
            raise ValueError("minor_direction cannot be provided in 2D case")
        if len(center) == 3 and minor_direction is None:
            raise ValueError("minor_direction must be given for 3D ellipses.")
        major_axis = Line(center, major_direction)
        if not minor_direction:
            minor_direction = major_direction @ np.array([[0, 1], [-1, 0]])
        minor_axis = Line(center, minor_direction)
        self.parts = EllipseParts(center, semi_major_axis, semi_minor_axis,
                                  major_axis, minor_axis)
        self.uid = uid
        references = {
            ConstraintReference.CORE: self,
            ConstraintReference.CENTER : self.parts.center,
            ConstraintReference.X: self.parts.major_axis,
            ConstraintReference.Y: self.parts.minor_axis,
        }
        for reference, point in self.parts.reference_points.items():
            references[reference] = point
        super().__init__(references)

    # Class Methods
    @classmethod
    def from_angle(cls,
                   center: Point | VectorLike,
                   semi_major_axis: Real,
                   semi_minor_axis: Real,
                   rotation_angle: Real,
                   uid: str | None=None) -> Self:
        """Returns a 2D ellipse using a rotation angle instead of a direction 
        vector.
        
        :param center: The center point of the ellipse.
        :param semi_major_axis: The length of the ellipse's **initial** longest 
            semidiameter. This length will continue to represent the same axis 
            even if the user changes the length to be shorter than the 
            semi-minor axis since the alternative would be semantically correct 
            but very confusing for users to modify. The lengths will not be 
            compared by pancad since this could be read from an already defined 
            ellipse that has already switched the values.
        :param semi_minor_axis: The length of the ellipse's **initial**
            shortest semidiameter. Same caveats as the semi_major_axis
            regarding changes.
        :param rotation_angle: The angle from the positive horizontal axis to 
            the Ellipse's major axis in radians.
        """
        major_direction = Point.from_polar(1, rotation_angle).cartesian
        return cls(center,
                   semi_major_axis,
                   semi_minor_axis,
                   major_direction,
                   uid=uid)

    # Properties
    @property
    def center(self) -> Point:
        """Center point of the ellipse.
        
        :getter: Returns the point.
        :setter: Moves the center point, major axis line, and minor axis line to 
            the new location without rotating the lines.
        :raises ValueError: When the given point's number of dimensions does not 
            match the Ellipse's current number of dimensions.
        """
        return self.parts.center
    @center.setter
    @no_dimensional_mismatch
    @updates_reference_points
    def center(self, point: Point | VectorLike) -> None:
        if isinstance(point, VectorLike):
            point = Point(point)
        self.parts.center.update(point)
        for axis in [self.parts.major_axis, self.parts.minor_axis]:
            axis.move_to_point(point)

    @property
    def focal_point_minus(self) -> Point:
        """Focal point in the negative direction of the Ellipse major axis."""
        return self.parts.reference_points[ConstraintReference.FOCAL_MINUS]

    @property
    def focal_point_plus(self) -> Point:
        """Focal point in the positive direction of the Ellipse major axis."""
        return self.parts.reference_points[ConstraintReference.FOCAL_PLUS]

    @property
    @two_dimensional_only
    def major_axis_angle(self) -> Real:
        """The angle from the positive horizontal axis of a 2D ellipse to its 
        major axis line.
        
        :getter: Returns the angle in radians.
        :setter: Updates the major and minor axes of the Ellipse so that the 
            major axis has the new angle in radians while keeping the center in 
            the same location.
        :raises ValueError: When the Ellipse not 2D.
        """
        return self.major_axis_line.phi

    @major_axis_angle.setter
    @two_dimensional_only
    @updates_reference_points
    def major_axis_angle(self, angle: Real) -> None:
        self.parts.major_axis.move_to_point(self.center, angle)
        minor_direction = (self.parts.major_axis.direction
                           @ np.array([[0, 1], [-1, 0]]))
        self.parts.minor_axis.update(Line(self.center, minor_direction))

    @property
    def major_axis_line(self) -> Line:
        """The line representing the major axis of the ellipse."""
        return self.parts.major_axis

    @property
    def major_axis_direction(self) -> tuple[Real]:
        """The direction vector of the major axis of the ellipse.
        
        :getter: Returns the vector of the major axis direction.
        :setter: Updates the major and minor axes so that the major axis matches 
            the new direction while keeping the ellipse center in the same 
            location.
        """
        return self.major_axis_line.direction

    @major_axis_direction.setter
    @updates_reference_points
    def major_axis_direction(self, direction: VectorLike) -> None:
        self.parts.major_axis.update(Line(self.center, direction))
        minor_direction = direction @ np.array([[0, 1], [-1, 0]])
        self.parts.minor_axis.update(Line(self.center, minor_direction))

    @property
    def major_axis_max(self) -> Point:
        """The intersection point of the positive direction of the major axis 
        and the ellipse's curve.
        """
        return self.parts.reference_points[ConstraintReference.X_MAX]

    @property
    def major_axis_min(self) -> Point:
        """The intersection point of the negative direction of the major axis 
        and the ellipse's curve.
        """
        return self.parts.reference_points[ConstraintReference.X_MIN]

    @property
    @two_dimensional_only
    def minor_axis_angle(self) -> Real:
        """The angle from the positive horizontal axis of a 2D ellipse to its 
        minor axis line in radians.
        
        :getter: Returns the angle in radians.
        :setter: Updates the major and minor axes of the Ellipse so that the 
            minor axis has the new angle in radians while keeping the center in 
            the same location.
        :raises ValueError: When the Ellipse is not 2D.
        """
        return self.parts.minor_axis.phi
    @minor_axis_angle.setter
    @two_dimensional_only
    @updates_reference_points
    def minor_axis_angle(self, angle: Real) -> None:
        self.parts.minor_axis.move_to_point(self.center, angle)
        self.minor_axis_line.move_to_point(self.center, angle)
        major_direction = (self.parts.minor_axis.direction
                           @ np.array([[0, -1], [1, 0]]))
        self.parts.major_axis.update(Line(self.center, major_direction))

    @property
    def minor_axis_line(self) -> Line:
        """The line representing the minor axis of the ellipse."""
        return self.parts.minor_axis

    @property
    def minor_axis_direction(self) -> tuple[Real]:
        """The direction vector of the minor axis of the ellipse.
        
        :getter: Returns the vector of the axis direction.
        :setter: Updates the axis to match the new direction while keeping the 
            ellipse center in the same location.
        """
        return self.minor_axis_line.direction
    @minor_axis_direction.setter
    @updates_reference_points
    def minor_axis_direction(self, direction: VectorLike) -> None:
        self.parts.minor_axis.update(Line(self.center, direction))
        major_direction = direction @ np.array([[0, -1], [1, 0]])
        self.parts.major_axis.update(Line(self.center, major_direction))

    @property
    def minor_axis_max(self) -> Point:
        """The intersection point of the positive direction of the minor axis 
        and the ellipse's curve.
        """
        return self.parts.reference_points[ConstraintReference.Y_MAX]

    @property
    def minor_axis_min(self) -> Point:
        """The intersection point of the negative direction of the minor axis 
        and the ellipse's curve.
        """
        return self.parts.reference_points[ConstraintReference.Y_MIN]

    @property
    def semi_major_axis(self) -> Real:
        """The length of the ellipse's semi-major axis."""
        return self.parts.major_semidiameter
    @semi_major_axis.setter
    @updates_reference_points
    def semi_major_axis(self, length: Real) -> None:
        self.parts.major_semidiameter = length

    @property
    def semi_minor_axis(self) -> Real:
        """The length of the ellipse's semi-minor axis."""
        return self.parts.minor_semidiameter
    @semi_minor_axis.setter
    @updates_reference_points
    def semi_minor_axis(self, length: Real) -> None:
        self.parts.minor_semidiameter = length

    # Public Methods #
    def copy(self) -> Ellipse:
        """Returns a copy of the Ellipse at the same position, size, and 
        orientation.
        """
        if len(self) == 2:
            return Ellipse(self.center.copy(),
                           self.semi_major_axis,
                           self.semi_minor_axis,
                           self.major_axis_direction)
        return Ellipse(self.center.copy(),
                       self.semi_major_axis,
                       self.semi_minor_axis,
                       self.major_axis_direction,
                       self.minor_axis_direction)

    def is_equal(self, other: Ellipse) -> bool:
        return all(
            [
                self.semi_major_axis == other.semi_major_axis,
                self.semi_minor_axis == other.semi_minor_axis,
                self.center.is_equal(other.center),
                self.major_axis_line.is_equal(other.major_axis_line),
                self.minor_axis_line.is_equal(other.minor_axis_line),
            ]
        )

    def get_linear_eccentricity(self) -> float:
        """Returns the linear eccentricity value of the Ellipse."""
        return self.parts.linear_eccentricity

    @no_dimensional_mismatch
    @updates_reference_points
    def update(self, other: Ellipse) -> Self:
        self.parts.major_semidiameter = other.parts.major_semidiameter
        self.parts.minor_semidiameter = other.parts.minor_semidiameter
        self.parts.center.update(other.parts.center)
        self.parts.major_axis.update(other.parts.major_axis)
        self.parts.minor_axis.update(other.parts.minor_axis)

    # Private Methods #
    @two_dimensional_only
    def _get_point_at_angle(self, angle: Real) -> Point:
        """Returns a Point on the 2D ellipse that is at the angle, in radians, 
        relative to the x-axis of the Ellipse.
        """
        if len(self) != 2:
            raise ValueError("Not supported for 3D ellipses")
        angle = angle_mod(angle)
        major_axis_rotation = rotation_2(self.major_axis_angle)
        eccentric_anomaly = atan2(self.semi_major_axis * sin(angle),
                                  self.semi_minor_axis * cos(angle))
        canon_location = (self.semi_major_axis * cos(eccentric_anomaly),
                          self.semi_minor_axis * sin(eccentric_anomaly))
        # 'canon' meaning if the ellipse was centered at the origin with its
        # major axis pointing in the X direction and its minor axis pointing
        # in the Y direction.
        coordinates = major_axis_rotation @ canon_location + self.center
        return Point(coordinates)

    # Python Dunders #
    def __copy__(self) -> Ellipse:
        return self.copy()

    def __eq__(self, other: Ellipse) -> bool:
        if isinstance(other, Ellipse):
            if len(self) == len(other):
                return (self.center == other.center
                        and self.semi_major_axis == other.semi_major_axis
                        and self.semi_minor_axis == other.semi_minor_axis
                        and self.major_axis_line == other.major_axis_line
                        and self.minor_axis_line == other.minor_axis_line)
            return False
        return NotImplemented

    def __len__(self) -> int:
        """Returns whether the ellipse is 2D or 3D."""
        return len(self.center)

    def __repr__(self) -> str:
        center_str = str(self.center.cartesian).replace(" ","")
        details = (f"{center_str}"
                   f"a{self.semi_major_axis}b{self.semi_minor_axis}>")
        return super().__repr__().format(details=details)
