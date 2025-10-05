"""A module providing an enumeration class for the FreeCAD constraint Internal Alignment Types 
options.
"""
from enum import IntEnum

from PanCAD.geometry.constants import ConstraintReference
from PanCAD.cad.freecad.constants import EdgeSubPart


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
    
    def get_constraint_reference(self,
                                 sub_part: EdgeSubPart) -> ConstraintReference:
        """Returns the equivalent constraint references for the internal 
        alignment type and a provided EdgeSubPart of the internal geometry.
        """
        match self:
            case self.ELLIPSE_MAJOR_DIAMETER:
                match sub_part:
                    case EdgeSubPart.EDGE:
                        return ConstraintReference.X
                    case EdgeSubPart.START:
                        return ConstraintReference.X_MAX
                    case EdgeSubPart.END:
                        return ConstraintReference.X_MIN
            case self.ELLIPSE_MINOR_DIAMETER:
                match sub_part:
                    case EdgeSubPart.EDGE:
                        return ConstraintReference.Y
                    case EdgeSubPart.START:
                        return ConstraintReference.Y_MAX
                    case EdgeSubPart.END:
                        return ConstraintReference.Y_MIN
            case self.ELLIPSE_FOCUS_1:
                if sub_part == EdgeSubPart.START:
                    return ConstraintReference.FOCAL_PLUS
                else:
                    raise ValueError("Unexpected EdgeSubPart for positive focal"
                                     f" point: {sub_part}")
            case self.ELLIPSE_FOCUS_2:
                if sub_part == EdgeSubPart.START:
                    return ConstraintReference.FOCAL_MINUS
                else:
                    raise ValueError("Unexpected EdgeSubPart for positive focal"
                                     f" point: {sub_part}")
