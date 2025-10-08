"""A module providing an enumeration class for the FreeCAD constraint sub-part 
options. See the following link for more information:
https://wiki.freecad.org/Sketcher_scripting#Identifying_the_numbering_of_the_sub-parts_of_a_line
"""
from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING

from PanCAD.geometry import Sketch
from PanCAD.geometry.constants import ConstraintReference

if TYPE_CHECKING:
    from PanCAD.geometry import AbstractGeometry

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
    
    def get_constraint_reference(self,
                                 geometry: AbstractGeometry,
                                 reference: ConstraintReference,
                                 ) -> ConstraintReference:
        """Returns the EdgeSubPart's equivalent
        :class:`PanCAD.geometry.constants.ConstraintReference` based on the part 
        of the equivalent PanCAD geometry that it's applied to.
        
        :param geometry: The parent geometry.
        :param reference: A ConstraintReference to the portion of the parent 
            geometry.
        :returns: The equivalent ConstraintReference for the parent's child 
            geometry.
        :raises ValueError: Raised when there is not an equivalent 
            ConstraintReference.
        """
        if isinstance(geometry, Sketch):
            # Handle Sketches as a special case. FreeCAD sketches have their 
            # origin and axes defined using the first two line segments in their 
            # ExternalGeo list. The EdgeSubPart for the corresponding part of 
            # those line segments needs to return those corresponding 
            # ConstraintReferences
            if reference == ConstraintReference.X:
                match self:
                    case EdgeSubPart.EDGE:
                        return ConstraintReference.X
                    case EdgeSubPart.START:
                        return ConstraintReference.ORIGIN
                    case _:
                        raise ValueError(f"Unsupported reference: {reference}")
            elif reference == ConstraintReference.Y:
                match self:
                    case EdgeSubPart.EDGE:
                        return ConstraintReference.Y
                    case _:
                        raise ValueError(f"Unsupported reference: {reference}")
            else:
                raise ValueError(f"Unsupported reference: {reference}")
        else:
            match self:
                case EdgeSubPart.EDGE:
                    return ConstraintReference.CORE
                case EdgeSubPart.START:
                    return ConstraintReference.START
                case EdgeSubPart.END:
                    return ConstraintReference.END
                case EdgeSubPart.CENTER:
                    return ConstraintReference.CENTER
                case _:
                    raise ValueError(f"Unsupported reference: {reference}")