"""A module providing an enumeration class for the lists in a FreeCAD sketch."""

from enum import StrEnum

class ListName(StrEnum):
    """An enumeration class used to reference FreeCAD lists inside of features 
    list sketches. Used to define a unique id to map FreeCAD features to pancad 
    features.
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
