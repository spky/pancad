"""A module providing an enumeration class for the string constants that define 
FreeCAD constraint types like Coincident, Vertical and other features."""

from enum import StrEnum

class ConstraintType(StrEnum):
    ANGLE = "Angle"
    COINCIDENT = "Coincident"
    DIAMETER = "Diameter"
    DISTANCE = "Distance"
    DISTANCE_X = "DistanceX"
    DISTANCE_Y = "DistanceY"
    EQUAL = "Equal"
    HORIZONTAL = "Horizontal"
    PARALLEL = "Parallel"
    PERPENDICULAR = "Perpendicular"
    POINT_ON_OBJECT = "PointOnObject"
    RADIUS = "Radius"
    VERTICAL = "Vertical"
    TANGENT = "Tangent"