"""A module providing an enumeration class for the FreeCAD constraint Internal 
Alignment Types options.
"""
from enum import IntEnum

from pancad.geometry.constants import ConstraintReference as CR
from pancad.cad.freecad.constants import EdgeSubPart as ESP

class InternalAlignmentType(IntEnum):
    """An enumeration used to define FreeCAD InternalAlignment constraint types 
    supported by pancad.
    """
    ELLIPSE_MAJOR_DIAMETER = 1
    """Constrains ellipse major axes to the ellipse."""
    ELLIPSE_MINOR_DIAMETER = 2
    """Constrains ellipse minor axes to the ellipse."""
    ELLIPSE_FOCUS_1 = 3
    """Constrains ellipse positive focal points to the ellipse."""
    ELLIPSE_FOCUS_2 = 4
    """Constrains ellipse negative focal points to the ellipse."""
    def get_constraint_reference(self, sub_part: ESP) -> CR:
        """Returns the equivalent constraint references for the internal 
        alignment type and a provided EdgeSubPart of the internal geometry.
        
        :raises ValueError: Raised when provided an unexpected EdgeSubPart for 
            the InternalAlignmentType.
        """
        try:
            return _TO_CONSTRAINT_REFERENCE[self, sub_part]
        except KeyError as err:
            raise ValueError("Unexpected EdgeSubPart Combo") from err

_TO_CONSTRAINT_REFERENCE = {
    (InternalAlignmentType.ELLIPSE_MAJOR_DIAMETER, ESP.EDGE): CR.X,
    (InternalAlignmentType.ELLIPSE_MAJOR_DIAMETER, ESP.START): CR.X_MAX,
    (InternalAlignmentType.ELLIPSE_MAJOR_DIAMETER, ESP.END): CR.X_MIN,
    (InternalAlignmentType.ELLIPSE_MINOR_DIAMETER, ESP.EDGE): CR.Y,
    (InternalAlignmentType.ELLIPSE_MINOR_DIAMETER, ESP.START): CR.Y_MAX,
    (InternalAlignmentType.ELLIPSE_MINOR_DIAMETER, ESP.END): CR.Y_MIN,
    (InternalAlignmentType.ELLIPSE_FOCUS_1, ESP.START): CR.FOCAL_PLUS,
    (InternalAlignmentType.ELLIPSE_FOCUS_2, ESP.START): CR.FOCAL_MINUS,
}
"""A map from an FreeCAD ellipse reference to the equivalent ConstraintReference.
"""
