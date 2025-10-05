"""A module providing an enumeration class for the FreeCAD constraint sub-part 
options. See the following link for more information:
https://wiki.freecad.org/Sketcher_scripting#Identifying_the_numbering_of_the_sub-parts_of_a_line
"""
from enum import StrEnum

class ListName(StrEnum):
    """An enumeration class used to reference FreeCAD lists inside of features 
    list sketches.
    """
    
    CONSTRAINTS = "Constraints"
    """The Constraints list inside of a sketch object."""
    EXTERNALS = "ExternalGeo"
    """The Externals list inside of a sketch object."""
    GEOMETRY = "Geometry"
    """The Geometry list inside of a sketch object."""
    INTERNAL_ALIGNMENT = "InternalAlignment"
    """Not a list explicitly in FreeCAD, but represents the list of 
    InternalAlignment constraints that are used to define other parts of the 
    geometry.
    """