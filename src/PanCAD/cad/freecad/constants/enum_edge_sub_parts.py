"""A module providing an enumeration class for the FreeCAD constraint sub-part 
options. See the following link for more information:
https://wiki.freecad.org/Sketcher_scripting#Identifying_the_numbering_of_the_sub-parts_of_a_line
"""
from enum import IntEnum

class EdgeSubPart(IntEnum):
    EDGE = 0
    START = 1
    END = 2
    CENTER = 3
    # FreeCAD also supports n for the nth pole of the B-spline, but that should 
    # be passed as a number.