"""A module providing an enumeration for the constraint types available to 2D 
sketches"""

from enum import Flag, auto

class SketchConstraint(Flag):
    ANGLE = auto()
    COINCIDENT = auto()
    COLLINEAR = auto()
    DISTANCE = auto()
    DISTANCE_HORIZONTAL = auto()
    DISTANCE_VERTICAL = auto()
    DISTANCE_RADIUS = auto()
    DISTANCE_DIAMETER = auto()
    EQUAL = auto()
    HORIZONTAL = auto()
    PARALLEL = auto()
    PERPENDICULAR = auto()
    SYMMETRIC = auto()
    TANGENT = auto()
    VERTICAL = auto()