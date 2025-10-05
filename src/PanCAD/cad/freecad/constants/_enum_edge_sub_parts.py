"""A module providing an enumeration class for the FreeCAD constraint sub-part 
options. See the following link for more information:
https://wiki.freecad.org/Sketcher_scripting#Identifying_the_numbering_of_the_sub-parts_of_a_line
"""
from enum import IntEnum

from PanCAD.geometry import AbstractGeometry, Sketch
from PanCAD.geometry.constants import ConstraintReference

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
        """Returns the equivalent subpart's equivalent constraint reference based 
        on the part of the geometry it's applied to.
        
        :param geometry: The parent geometry.
        :param reference: A ConstraintReference to the portion of geometry.
        :returns: The equivalent ConstraintReference.
        """
        if isinstance(geometry, Sketch):
            if reference == ConstraintReference.X:
                match self:
                    case EdgeSubPart.EDGE:
                        return ConstraintReference.X
                    case EdgeSubPart.START:
                        return ConstraintReference.ORIGIN
                    case _:
                        raise ValueError(f"Unsupported subpart: {sub_part}")
            elif reference == ConstraintReference.Y:
                match self:
                    case EdgeSubPart.EDGE:
                        return ConstraintReference.Y
                    case _:
                        raise ValueError(f"Unsupported subpart: {sub_part}")
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
                    raise ValueError(f"Unsupported subpart: {sub_part}")