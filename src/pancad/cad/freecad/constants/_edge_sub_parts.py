"""A module providing an enumeration class for the FreeCAD constraint sub-part 
options. See the following link for more information:
https://wiki.freecad.org/Sketcher_scripting#Identifying_the_numbering_of_the_sub-parts_of_a_line
"""
from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING, Self

from pancad.geometry import Sketch, CircularArc
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
    def from_constraint_reference(cls,
                                  geometry: AbstractGeometry,
                                  reference: ConstraintReference) -> Self:
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
                if isinstance(geometry, CircularArc) and geometry.is_clockwise:
                    # All FreeCAD arcs are counterclockwise
                    return EdgeSubPart.END
                return EdgeSubPart.START
            case (ConstraintReference.END
                    | ConstraintReference.X_MAX
                    | ConstraintReference.Y_MAX):
                if isinstance(geometry, CircularArc) and geometry.is_clockwise:
                    # All FreeCAD arcs are counterclockwise
                    return EdgeSubPart.START
                return EdgeSubPart.END
            case ConstraintReference.CENTER:
                return EdgeSubPart.CENTER
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
            # those line segments need to return those corresponding
            # ConstraintReferences
            try:
                return SKETCH_REFERENCE[reference, self]
            except KeyError as err:
                raise ValueError("Unsupported Reference") from err
        if isinstance(geometry, CircularArc):
            try:
                return CIRCULAR_ARC_REFERENCE[self, geometry.is_clockwise]
            except KeyError as err:
                raise ValueError("Unsupported Reference") from err
        try:
            return DEFAULT_REFERENCE[self]
        except KeyError as err:
            raise ValueError("Unsupported Reference") from err

SKETCH_REFERENCE = {
    (ConstraintReference.X, EdgeSubPart.EDGE): ConstraintReference.X,
    (ConstraintReference.X, EdgeSubPart.START): ConstraintReference.ORIGIN,
    (ConstraintReference.Y, EdgeSubPart.EDGE): ConstraintReference.Y,
}
"""A map for unconditional translations from FreeCAD reference to 
ConstraintReference for sketches
"""
CIRCULAR_ARC_REFERENCE = {
    (EdgeSubPart.EDGE, True): ConstraintReference.CORE,
    (EdgeSubPart.EDGE, False): ConstraintReference.CORE,
    (EdgeSubPart.CENTER, True): ConstraintReference.CENTER,
    (EdgeSubPart.CENTER, False): ConstraintReference.CENTER,
    (EdgeSubPart.START, True): ConstraintReference.END,
    (EdgeSubPart.START, False): ConstraintReference.START,
    (EdgeSubPart.END, True): ConstraintReference.START,
    (EdgeSubPart.END, False): ConstraintReference.END,
}
"""A map for unconditional translations from FreeCAD reference to 
ConstraintReference for Arc of Circles. The second map argument is True for 
clockwise arcs and False for counterclockwise arcs.
"""
DEFAULT_REFERENCE = {
    EdgeSubPart.EDGE: ConstraintReference.CORE,
    EdgeSubPart.START: ConstraintReference.START,
    EdgeSubPart.END: ConstraintReference.END,
    EdgeSubPart.CENTER: ConstraintReference.CENTER,
}
"""A map for unconditional translations from FreeCAD reference to 
ConstraintReference for non-special cases.
"""
