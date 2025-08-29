"""A module providing a class to represent ellipses in all CAD programs, 
graphics, and other geometry use cases.
"""
from __future__ import annotations

import math
from numbers import Real
from typing import overload, Self

import numpy as np

from PanCAD.geometry import AbstractGeometry, Point, Line
from PanCAD.geometry.constants import ConstraintReference
from PanCAD.utils.pancad_types import VectorLike
from PanCAD.utils.trigonometry import (get_unit_vector,
                                       get_vector_angle)

class Ellipse(AbstractGeometry):
    CENTER_UID_FORMAT = "{uid}_center"
    MAJOR_AXIS_UID_FORMAT = "{uid}_major_axis"
    MINOR_AXIS_UID_FORMAT = "{uid}_minor_axis"
    
    REFERENCES = (ConstraintReference.CORE,
                  ConstraintReference.CENTER,
                  ConstraintReference.X,
                  ConstraintReference.Y,)
    
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
                 major_direction, minor_direction=None, uid=None) -> None:
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
    def from_angle(self,
                   center: Point | VectorLike,
                   semi_major_axis: Real,
                   semi_minor_axis: Real,
                   rotation_angle: Real,
                   uid: str=None) -> Self:
        """Returns a new ellipse using a rotation angle instead of direction 
        vectors. For 2D ellipse definition only.
        """
        pass
    
    # Getters #
    @property
    def center(self) -> Point:
        """Center point of the ellipse.
        
        :getter: Returns the point.
        :setter: Updates the internal center point with values from a new point. 
            Moves the ellipse axes to the new location as well.
        """
        return self._center
    
    @property
    def major_axis_line(self) -> Line:
        """The major axis of the ellipse.
        
        :getter: Returns the line representing the axis.
        :setter: Updates the axis to match the new line.
        """
        return self._major_axis_line
    
    @property
    def major_axis_direction(self) -> tuple:
        """The direction vector of the major axis of the ellipse.
        
        :getter: Returns the vector of the axis direction.
        :setter: Updates the axis to match the new direction.
        """
        return self.major_axis_line.direction
    
    @property
    def minor_axis_line(self) -> Line:
        """The major axis of the ellipse.
        
        :getter: Returns the line representing the axis.
        :setter: Updates the axis to match the new line.
        """
        return self._minor_axis_line
    
    @property
    def minor_axis_direction(self) -> tuple:
        """The direction vector of the minor axis of the ellipse.
        
        :getter: Returns the vector of the axis direction.
        :setter: Updates the axis to match the new direction.
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
        :setter: Updates the ellipse and its center point's unique ids.
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
            else:
                raise ValueError(f"Dimension mismatch: Provided center point is"
                                 f" {len(point)}D, Ellipse is {len(self)}D")
        else:
            self._center = point
    
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
            case _:
                raise ValueError(f"{self.__class__}s do not have any"
                                 f" {reference.name} reference geometry")
    
    def get_all_references() -> tuple[ConstraintReference]:
        return self.REFERENCES
    
    def update(other: Ellipse) -> Self:
        self.center.update(other.center)
    
    # Private Methods #
    def _init_2d(self, major_direction: VectorLike) -> None:
        if len(major_direction) != 2:
            raise ValueError("major_direction must be 2 long for 2D ellipses,"
                             f" given: {major_direction}")
        self._major_axis_line = Line(self.center, major_direction)
        
        # Using explicit -90 degree rotation matrix to eliminate rounding error
        minor_direction = major_direction @ np.array([[0, 1], [-1, 0]])
        self._minor_axis_line = Line(self.center, minor_direction)
    
    def _init_3d(self,
                 major_direction: VectorLike,
                 minor_direction: VectorLike) -> None:
        raise NotImplementedError("3D ellipses not yet implemented")
    
    # Python Dunders #
    def __len__(self) -> int:
        """Returns whether the ellipse is 2D or 3D."""
        return len(self.center)
    
    def __repr__(self) -> str:
        center_str = str(self.center.cartesian).replace(" ","")
        string = (f"<PanCADEllipse'{self.uid}'{center_str}"
                  f"a{self.semi_major_axis}b{self.semi_minor_axis}>")