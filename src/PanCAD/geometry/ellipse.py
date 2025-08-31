"""A module providing a class to represent ellipses in all CAD programs, 
graphics, and other geometry use cases.
"""
from __future__ import annotations

from functools import partial
from math import atan2, cos, radians, sin, sqrt
from numbers import Real
from typing import overload, Self

import numpy as np

from PanCAD.geometry import AbstractGeometry, Point, Line
from PanCAD.geometry.constants import ConstraintReference
from PanCAD.utils import comparison
from PanCAD.utils.pancad_types import VectorLike
from PanCAD.utils.trigonometry import (angle_mod,
                                       get_unit_vector,
                                       get_vector_angle,
                                       rotation_2)

_isclose = partial(comparison.isclose, nan_equal=False)

class Ellipse(AbstractGeometry):
    """A class representing an ellipse in 2D or 3D space.
    
    :param center: The center point of the ellipse.
    :param semi_major_axis: The length of the ellipse's **initial** longest 
        semidiameter. This length will continue to represent the same axis 
        orientation even if the user changes the value to be shorter than the 
        semi-minor axis since the alternative would be semantically correct but 
        very confusing to modify. The lengths will not be compared by PanCAD 
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
    CENTER_UID_FORMAT = "{uid}_center"
    MAJOR_AXIS_UID_FORMAT = "{uid}_major_axis"
    MINOR_AXIS_UID_FORMAT = "{uid}_minor_axis"
    
    REFERENCES = (ConstraintReference.CORE,
                  ConstraintReference.CENTER,
                  ConstraintReference.X,
                  ConstraintReference.Y,
                  ConstraintReference.FOCAL_PLUS,
                  ConstraintReference.FOCAL_MINUS,)
    """All relevant ConstraintReferences for Ellipses."""
    
    @overload
    def __init__(self,
                 center: Point | VectorLike,
                 semi_major_axis: Real,
                 semi_minor_axis: Real,
                 major_direction: VectorLike,
                 uid: str=None) -> None: ...
    
    @overload
    def __init__(self,
                 center: Point | VectorLike,
                 semi_major_axis: Real,
                 semi_minor_axis: Real,
                 major_direction: VectorLike,
                 minor_direction: VectorLike,
                 uid: str=None) -> None: ...
    
    def __init__(self, center, semi_major_axis, semi_minor_axis,
                 major_direction, minor_direction=None, uid=None):
        if isinstance(center, VectorLike):
            center = Point(center)
        self.center = center
        self.semi_major_axis = semi_major_axis
        self.semi_minor_axis = semi_minor_axis
        
        if len(self.center) == 2 and minor_direction is None:
            self._init_2d(major_direction)
        elif len(self.center) == 3 and minor_direction is not None:
            self._init_3d(major_direction, minor_direction)
        elif len(self.center) == 2 and minor_direction is not None:
            raise ValueError("minor_direction must be None for 2D ellipses.")
        elif len(self.center) == 3 and minor_direction is None:
            raise ValueError("minor_direction must be given for 3D ellipses.")
        else:
            inputs = [center, semi_major_axis, semi_minor_axis,
                      major_direction, minor_direction, uid]
            raise ValueError(f"Unhandled combination of inputs: {inputs}")
        self.uid = uid
    
    # Class Methods #
    @classmethod
    def from_angle(cls,
                   center: Point | VectorLike,
                   semi_major_axis: Real,
                   semi_minor_axis: Real,
                   rotation_angle: Real,
                   uid: str=None) -> Self:
        """Returns a 2D ellipse using a rotation angle instead of a direction 
        vector.
        
        :param center: The center point of the ellipse.
        :param semi_major_axis: The length of the ellipse's **initial** longest 
            semidiameter. This length will continue to represent the same axis 
            even if the user changes the length to be shorter than the 
            semi-minor axis since the alternative would be semantically correct 
            but very confusing for users to modify. The lengths will not be 
            compared by PanCAD since this could be read from an already defined 
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
    
    # Getters #
    @property
    def center(self) -> Point:
        """Center point of the ellipse.
        
        :getter: Returns the point.
        :setter: Moves the center point, major axis line, and minor axis line to 
            the new location without rotating the lines.
        :raises ValueError: When the given point's number of dimensions does not 
            match the Ellipse's current number of dimensions.
        """
        return self._center
    
    @property
    def focal_point_minus(self) -> Point:
        """The focal point in the negative direction of the Ellipse major axis.
        
        :getter: Returns the point.
        :setter: Read-only. Would cause undefined center point or axis behavior 
            if changed by itself.
        """
        return self._focal_point_minus
    
    @property
    def focal_point_plus(self) -> Point:
        """The focal point in the positive direction of the Ellipse major axis.
        
        :getter: Returns the point.
        :setter: Read-only. Would cause undefined center point or axis behavior 
            if changed by itself.
        """
        return self._focal_point_plus
    
    @property
    def major_axis_angle(self) -> Real:
        """The angle from the positive horizontal axis of a 2D ellipse to its 
        major axis line.
        
        :getter: Returns the angle in radians.
        :setter: Updates the major and minor axes of the Ellipse so that the 
            major axis has the new angle in radians while keeping the center in 
            the same location.
        :raises ValueError: When the Ellipse not 2D.
        """
        if len(self) == 2:
            return self.major_axis_line.phi
        else:
            raise ValueError("3D ellipses cannot return a well defined axis"
                             " angle")
    
    @property
    def major_axis_line(self) -> Line:
        """The line representing the major axis of the ellipse.
        
        :getter: Returns the line representing the axis.
        :setter: Read-only. Would cause undefined center point behavior if 
            changed by itself.
        """
        return self._major_axis_line
    
    @property
    def major_axis_direction(self) -> tuple[Real]:
        """The direction vector of the major axis of the ellipse.
        
        :getter: Returns the vector of the major axis direction.
        :setter: Updates the major and minor axes so that the major axis matches 
            the new direction while keeping the ellipse center in the same 
            location.
        """
        return self.major_axis_line.direction
    
    @property
    def minor_axis_angle(self) -> Real:
        """The angle from the positive horizontal axis of a 2D ellipse to its 
        minor axis line in radians.
        
        :getter: Returns the angle in radians.
        :setter: Updates the major and minor axes of the Ellipse so that the 
            minor axis has the new angle in radians while keeping the center in 
            the same location.
        :raises ValueError: When the Ellipse not 2D.
        """
        if len(self) == 2:
            return self.minor_axis_line.phi
        else:
            raise ValueError("3D ellipses cannot return a well defined axis"
                             " angle")
    
    @property
    def minor_axis_line(self) -> Line:
        """The line representing the minor axis of the ellipse.
        
        :getter: Returns the line representing the axis.
        :setter: Read-only. Would cause undefined center point behavior if 
            changed by itself.
        """
        return self._minor_axis_line
    
    @property
    def minor_axis_direction(self) -> tuple[Real]:
        """The direction vector of the minor axis of the ellipse.
        
        :getter: Returns the vector of the axis direction.
        :setter: Updates the axis to match the new direction while keeping the 
            ellipse center in the same location.
        """
        return self.minor_axis_line.direction
    
    @property
    def semi_major_axis(self) -> Real:
        """The length of the ellipse's semi-major axis.
        
        :getter: Returns the length of the semi-major axis.
        :setter: Sets the length of the semi-major axis.
        """
        return self._semi_major_axis
    
    @property
    def semi_minor_axis(self) -> Real:
        """The length of the ellipse's semi-minor axis.
        
        :getter: Returns the length of the semi-minor axis.
        :setter: Sets the length of the semi-minor axis.
        """
        return self._semi_minor_axis
    
    @property
    def uid(self) -> str:
        """Unique id of the ellipse.
        
        :getter: Returns the unique id.
        :setter: Updates the ellipse and its center point, major axis line, and 
            minor axis line's unique ids.
        """
        return self._uid
    
    # Setters #
    @center.setter
    def center(self, point: Point | VectorLike) -> None:
        if isinstance(point, VectorLike):
            point = Point(point)
        
        if hasattr(self, "_center"):
            if len(point) == len(self):
                self._center.update(point)
                self._major_axis_line.move_to_point(self._center)
                self._minor_axis_line.move_to_point(self._center)
                self._focal_point_plus.cartesian = self._get_focal_location(
                    True
                )
                self._focal_point_minus.cartesian = self._get_focal_location(
                    False
                )
            else:
                raise ValueError(f"Dimension mismatch: Provided center point is"
                                 f" {len(point)}D, Ellipse is {len(self)}D")
        else:
            # Initialize center
            self._center = point
    
    @major_axis_angle.setter
    def major_axis_angle(self, angle: Real) -> None:
        if len(self) == 2:
            self.major_axis_line.move_to_point(self.center, angle)
            minor_direction = (self.major_axis_line.direction
                               @ np.array([[0, 1], [-1, 0]]))
            self.minor_axis_line.update(Line(self.center, minor_direction))
            self._focal_point_plus.cartesian = self._get_focal_location(True)
            self._focal_point_minus.cartesian = self._get_focal_location(False)
        else:
            raise ValueError("3D ellipses cannot modify their angle in a well"
                             " defined way")
    
    @major_axis_direction.setter
    def major_axis_direction(self, direction: VectorLike) -> None:
        self.major_axis_line.update(Line(self.center, direction))
        minor_direction = direction @ np.array([[0, 1], [-1, 0]])
        self.minor_axis_line.update(Line(self.center, minor_direction))
        self._focal_point_plus.cartesian = self._get_focal_location(True)
        self._focal_point_minus.cartesian = self._get_focal_location(False)
    
    @minor_axis_direction.setter
    def minor_axis_direction(self, direction: VectorLike) -> None:
        self.minor_axis_line.update(Line(self.center, direction))
        major_direction = direction @ np.array([[0, -1], [1, 0]])
        self.major_axis_line.update(Line(self.center, major_direction))
        self._focal_point_plus.cartesian = self._get_focal_location(True)
        self._focal_point_minus.cartesian = self._get_focal_location(False)
    
    @minor_axis_angle.setter
    def minor_axis_angle(self, angle: Real) -> None:
        if len(self) == 2:
            self.minor_axis_line.move_to_point(self.center, angle)
            major_direction = (self.minor_axis_line.direction
                               @ np.array([[0, -1], [1, 0]]))
            self.major_axis_line.update(Line(self.center, major_direction))
            self._focal_point_plus.cartesian = self._get_focal_location(True)
            self._focal_point_minus.cartesian = self._get_focal_location(False)
        else:
            raise ValueError("3D ellipses cannot modify their angle in a well"
                             " defined way")
    
    @semi_major_axis.setter
    def semi_major_axis(self, length: Real) -> None:
        self._semi_major_axis = length
    
    @semi_minor_axis.setter
    def semi_minor_axis(self, length: Real) -> None:
        self._semi_minor_axis = length
    
    @uid.setter
    def uid(self, value: str) -> None:
        self._uid = value
        if self._uid is None:
            self.center.uid = None
            self.major_axis_line.uid = None
            self.minor_axis_line.uid = None
        else:
            self.center.uid = self.CENTER_UID_FORMAT.format(uid=self._uid)
            self.major_axis_line.uid = self.MAJOR_AXIS_UID_FORMAT.format(
                uid=self._uid
            )
            self.minor_axis_line.uid = self.MINOR_AXIS_UID_FORMAT.format(
                uid=self._uid
            )
    
    # Public Methods #
    def copy(self) -> Point:
        """Returns a copy of the Ellipse.
        
        :returns: A new Ellipse at the same position, size, and orientation as 
            this Ellipse.
        """
        return self.__copy__()
    
    def get_linear_eccentricity(self) -> float:
        return sqrt(self.semi_major_axis**2 - self.semi_minor_axis**2)
    
    def get_major_axis_point(self) -> Point:
        """Returns the point on the ellipse at the extreme of the positive major 
        axis.
        """
        return self._get_point_at_angle(0)
    
    def get_minor_axis_point(self) -> Point:
        """Returns the point on the ellipse at the extreme of the positive major 
        axis.
        """
        return self._get_point_at_angle(radians(90))
    
    def get_reference(reference: ConstraintReference) -> Self | Point | Line:
        match reference:
            case ConstraintReference.CORE:
                return self
            case ConstraintReference.CENTER:
                return self.center
            case ConstraintReference.X:
                return self.major_axis_line
            case ConstraintReference.Y:
                return self.minor_axis_line
            case ConstraintReference.FOCAL_PLUS:
                return self.focal_point_plus
            case ConstraintReference.FOCAL_MINUS:
                return self.focal_point_minus
            case _:
                raise ValueError(f"{self.__class__}s do not have any"
                                 f" {reference.name} reference geometry")
    
    def get_all_references() -> tuple[ConstraintReference]:
        return self.REFERENCES
    
    def update(other: Ellipse) -> Self:
        self.center.update(other.center)
    
    # Private Methods #
    def _get_focal_location(self, plus: bool) -> np.ndarray:
        """Returns the coordinates of an ellipse focal point.
        
        :param plus: Whether to return the focal point in the positive or 
            negative direction of the major axis.
        :returns: The focal point in the positive direction of the major axis if 
            plus is 'True', otherwise the focal point in the negative direction.
        """
        c = self.get_linear_eccentricity()
        if plus:
            return self.center.cartesian + c*np.array(self.major_axis_direction)
        else:
            return self.center.cartesian - c*np.array(self.major_axis_direction)
    
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
        # 'canon' meaning if the ellipse was centered at the origin with its 
        # major axis pointing in the X direction and its minor axis pointing 
        # in the Y direction.
        canon_location = (self.semi_major_axis * cos(eccentric_anomaly),
                          self.semi_minor_axis * sin(eccentric_anomaly))
        coordinates = major_axis_rotation @ canon_location + self.center
        return Point(coordinates)
    
    def _init_2d(self, major_direction: VectorLike) -> None:
        """Finishes up initialization for 2D ellipses."""
        if len(major_direction) != 2:
            raise ValueError("major_direction must be 2 long for 2D ellipses,"
                             f" given: {major_direction}")
        self._major_axis_line = Line(self.center, major_direction)
        
        # Using explicit -90 degree rotation matrix to eliminate rounding error 
        # from using the trig.rotation_2 function
        minor_direction = major_direction @ np.array([[0, 1], [-1, 0]])
        self._minor_axis_line = Line(self.center, minor_direction)
        self._focal_point_plus = Point(self._get_focal_location(True))
        self._focal_point_minus = Point(self._get_focal_location(False))
    
    def _init_3d(self,
                 major_direction: VectorLike,
                 minor_direction: VectorLike) -> None:
        """Finishes up initialization for 3D ellipses."""
        raise NotImplementedError("3D ellipses not yet implemented, Issue #117")
    
    # Python Dunders #
    def __copy__(self) -> Ellipse:
        if len(self) == 2:
            return Ellipse(self.center.copy(),
                           self.semi_major_axis,
                           self.semi_minor_axis,
                           self.major_axis_direction)
        else:
            return Ellipse(self.center.copy(),
                           self.semi_major_axis,
                           self.semi_minor_axis,
                           self.major_axis_direction,
                           self.minor_axis_direction)
    
    def __eq__(self, other: Ellipse) -> bool:
        if isinstance(other, Ellipse):
            if len(self) == len(other):
                return (self.center == other.center
                        and self.semi_major_axis == other.semi_major_axis
                        and self.semi_minor_axis == other.semi_minor_axis
                        and self.major_axis_line == other.major_axis_line
                        and self.minor_axis_line == other.minor_axis_line)
            else:
                return False
        else:
            return NotImplemented
    
    def __len__(self) -> int:
        """Returns whether the ellipse is 2D or 3D."""
        return len(self.center)
    
    def __repr__(self) -> str:
        center_str = str(self.center.cartesian).replace(" ","")
        string = (f"<PanCADEllipse'{self.uid}'{center_str}"
                  f"a{self.semi_major_axis}b{self.semi_minor_axis}>")