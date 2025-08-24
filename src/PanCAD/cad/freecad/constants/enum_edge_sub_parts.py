"""A module providing an enumeration class for the FreeCAD constraint sub-part 
options. See the following link for more information:
https://wiki.freecad.org/Sketcher_scripting#Identifying_the_numbering_of_the_sub-parts_of_a_line
"""
from enum import IntEnum

class EdgeSubPart(IntEnum):
    """An enumeration class used to define FreeCAD constraints with the 
    sub-parts of the geometry they reference.
    
    :note: FreeCAD also supports n for the nth pole of the B-spline, but that 
        should be passed as a number and is outside the scope of this 
        enumeration.
    """
    
    EDGE = 0
    """Constraint affects the entire edge."""
    START = 1
    """Constraint affects the start point of an edge."""
    END = 2
    """Constraint affects the end point of an edge."""
    CENTER = 3
    """Constraint affects the center point of an edge."""