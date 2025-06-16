"""A module providing an enumeration for the portions of geometry that a 
constraint is referencing. For example, a constraint can be defined between a 
point and a line's end point, so constraints need a way to track what part 
of the line is being constrained.

"""
from enum import Flag, auto

class ConstraintReference(Flag):
    # A core reference is used for cases where the geometry as a whole can be 
    # constrained.
    # Example: A line's core can be parallel to another line's core.
    CORE = auto()
    
    # Point Reference
    START = auto()
    END = auto()
    CENTER = auto()
    ORIGIN = CENTER
    # Line Reference
    X = auto()
    Y = auto()
    Z = auto()
    # Plane Reference
    XY = auto()
    XZ = auto()
    YZ = auto()
    # Coordinate System Reference (usually for sketches)
    CS = auto()
    COORDINATE_SYSTEM = CS