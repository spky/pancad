"""A module providing an enumeration class for the FreeCAD constraint sub-part 
options. See the following link for more information:
https://wiki.freecad.org/Sketcher_scripting#Identifying_the_numbering_of_the_sub-parts_of_a_line
"""
from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING, Self

from pancad.geometry import Sketch
from pancad.geometry.constants import ConstraintReference

if TYPE_CHECKING:
    from pancad.geometry import AbstractGeometry

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
    
    @classmethod
    def from_constraint_reference(self, reference: ConstraintReference) -> Self:
        """Returns the EdgeSubPart that matches the pancad ConstraintReference 
        when translating from pancad to FreeCAD.
        
        :param reference: A ConstraintReference to a portion of geometry.
        :returns: The FreeCAD equivalent to the reference.
        """
        match reference:
            case (ConstraintReference.CORE
                    | ConstraintReference.X
                    | ConstraintReference.Y):
                # The origin of sketch coordinate systems in FreeCAD is 
                # arbitrarily the start point of the sketch coordinate system's 
                # x-axis line segment located in the Sketch's ExternalGeo list 
                # index 0.
                return EdgeSubPart.EDGE
            case (ConstraintReference.START
                    | ConstraintReference.X_MIN
                    | ConstraintReference.Y_MIN
                    | ConstraintReference.ORIGIN):
                return EdgeSubPart.START
            case (ConstraintReference.END
                    | ConstraintReference.X_MAX
                    | ConstraintReference.Y_MAX):
                return EdgeSubPart.END
            case ConstraintReference.CENTER:
                return EdgeSubPart.CENTER
            case _:
                raise ValueError(f"Unsupported reference: {reference}")
        
    
    def get_constraint_reference(self,
                                 geometry: AbstractGeometry,
                                 reference: ConstraintReference,
                                 ) -> ConstraintReference:
        """Returns the EdgeSubPart's equivalent
        :class:`pancad.geometry.constants.ConstraintReference` based on the part 
        of the equivalent pancad geometry that it's applied to.
        
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