"""A module providing an enumeration class for the string constants that define 
FreeCAD constraint types like Coincident, Vertical and other features."""
from __future__ import annotations

from enum import StrEnum

from PanCAD.geometry.constraints import (
    AbstractConstraint,
    Angle,
    Coincident,
    Diameter,
    Distance,
    Equal,
    Horizontal,
    HorizontalDistance, 
    Parallel,
    Perpendicular,
    Radius,
    Vertical,
    VerticalDistance, 
)

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
    VERTICAL = "Vertical"
    TANGENT = "Tangent"
    
    @classmethod
    def from_pancad(cls, constraint: AbstractConstraint) -> ConstraintType:
        match type(constraint).__qualname__:
            case "Angle":
                return ConstraintType.ANGLE
            case "Coincident":
                return ConstraintType.COINCIDENT
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