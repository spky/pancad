"""A module providing an enumeration class for the string constants that define 
FreeCAD constraint types like Coincident, Vertical and other features."""
from __future__ import annotations

from enum import StrEnum, Flag
from typing import TYPE_CHECKING

from pancad.geometry import Point
from pancad.geometry.constants import SketchConstraint

if TYPE_CHECKING:
    from pancad.geometry.constraints import AbstractConstraint

class ConstraintType(StrEnum):
    """An enumeration used to define which FreeCAD constraints are supported."""
    ANGLE = "Angle"
    COINCIDENT = "Coincident"
    DIAMETER = "Diameter"
    DISTANCE = "Distance"
    DISTANCE_X = "DistanceX"
    DISTANCE_Y = "DistanceY"
    EQUAL = "Equal"
    HORIZONTAL = "Horizontal"
    INTERNAL_ALIGNMENT = "InternalAlignment"
    PARALLEL = "Parallel"
    PERPENDICULAR = "Perpendicular"
    POINT_ON_OBJECT = "PointOnObject"
    RADIUS = "Radius"
    TANGENT = "Tangent"
    VERTICAL = "Vertical"
    
    def get_sketch_constraint(self) -> SketchConstraint:
        """Returns the ConstraintType's equivalent 
        :class:`~pancad.geometry.constants.SketchConstraint`
        
        :raises ValueError: When the ConstraintType does not have an equivalent 
            SketchConstraint.
        """
        match self:
            case ConstraintType.ANGLE:
                return SketchConstraint.ANGLE
            case ConstraintType.COINCIDENT:
                return SketchConstraint.COINCIDENT
            case ConstraintType.DIAMETER:
                return SketchConstraint.DISTANCE_DIAMETER
            case ConstraintType.DISTANCE:
                return SketchConstraint.DISTANCE
            case ConstraintType.DISTANCE_X:
                return SketchConstraint.DISTANCE_HORIZONTAL
            case ConstraintType.DISTANCE_Y:
                return SketchConstraint.DISTANCE_VERTICAL
            case ConstraintType.EQUAL:
                return SketchConstraint.EQUAL
            case ConstraintType.HORIZONTAL:
                return SketchConstraint.HORIZONTAL
            case ConstraintType.PARALLEL:
                return SketchConstraint.PARALLEL
            case ConstraintType.PERPENDICULAR:
                return SketchConstraint.PERPENDICULAR
            case ConstraintType.POINT_ON_OBJECT:
                return SketchConstraint.COINCIDENT
            case ConstraintType.RADIUS:
                return SketchConstraint.RADIUS
            case ConstraintType.TANGENT:
                return SketchConstraint.TANGENT
            case ConstraintType.VERTICAL:
                return SketchConstraint.VERTICAL
            case ConstraintType.INTERNAL_ALIGNMENT:
                raise ValueError("No equivalent SketchConstraint for"
                                 " INTERNAL_ALIGNMENT, should stay internal"
                                 " to FreeCAD.")
            case _:
                raise ValueError(f"Unsupported type {self}")
    
    @classmethod
    def from_pancad(cls, constraint: AbstractConstraint) -> ConstraintType:
        """Returns the pancad constraint's equivalent ConstraintType.
        
        :raises TypeError: Raised when the pancad constraint does not have have 
            a ConstraintType equivalent.
        """
        type_ = type(constraint).__qualname__
        match type_:
            case "Angle":
                return ConstraintType.ANGLE
            case "Coincident":
                geometries = constraint.get_geometry()
                if all([isinstance(g, Point) for g in geometries]):
                    # Point on Point -> Coincident
                    return ConstraintType.COINCIDENT
                elif any([isinstance(g, Point) for g in geometries]):
                    # Point on Curve/Line -> PointOnObject
                    return ConstraintType.POINT_ON_OBJECT
                else:
                    # Curve/Line on Curve/Line -> Tangent
                    return ConstraintType.TANGENT
            case "Diameter":
                return ConstraintType.DIAMETER
            case "Distance":
                return ConstraintType.DISTANCE
            case "Equal":
                return ConstraintType.EQUAL
            case "Horizontal":
                return ConstraintType.HORIZONTAL
            case "HorizontalDistance":
                return ConstraintType.DISTANCE_X
            case "Parallel":
                return ConstraintType.PARALLEL
            case "Perpendicular":
                return ConstraintType.PERPENDICULAR
            case "Radius":
                return ConstraintType.RADIUS
            case "Vertical":
                return ConstraintType.VERTICAL
            case "VerticalDistance":
                return ConstraintType.DISTANCE_Y
            case _:
                raise TypeError(f"Unsupported type {type_}")