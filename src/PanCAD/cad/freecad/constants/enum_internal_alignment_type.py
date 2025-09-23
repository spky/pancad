"""A module providing an enumeration class for the FreeCAD constraint Internal Alignment Types 
options.
"""
from enum import IntEnum

class InternalAlignmentType(IntEnum):
    """An enumeration class used to define FreeCAD InternalAlignment constraint 
    types.
    """
    
    ELLIPSE_MAJOR_DIAMETER = 1
    """Constrains ellipse major axes to the ellipse."""
    ELLIPSE_MINOR_DIAMETER = 2
    """Constrains ellipse minor axes to the ellipse."""
    ELLIPSE_FOCUS_1 = 3
    """Constrains ellipse positive focal points to the ellipse."""
    ELLIPSE_FOCUS_2 = 4
    """Constrains ellipse negative focal points to the ellipse."""