"""A module providing an enumeration for FreeCAD's sketch magic numbers
"""
from enum import IntEnum

class SketchNumber(IntEnum):
    """An enumeration of magic numbers used in FreeCAD sketches."""
    
    UNUSED_CONSTRAINT_POSITION = -2000
    """Indicates that a constraint position field is not used. Example: the 2nd 
    and 3rd positions of a Horizontal constraint placed onto a line segment 
    would each be -2000.
    """
    CONSTRAINT_X_AXIS = -1
    """The index used by constraints to refer to sketch x axes."""
    CONSTRAINT_Y_AXIS = -2
    """The index used by constraints to refer to sketch y axes."""
    SKETCH_X_AXIS = 0
    """The index of sketches' x axes in their ExternalGeo lists."""
    SKETCH_Y_AXIS = 1
    """The index of sketches' x axes in their ExternalGeo lists."""