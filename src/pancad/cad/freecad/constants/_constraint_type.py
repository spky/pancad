"""A module providing an enumeration class for the string constants that define 
FreeCAD constraint types like Coincident, Vertical and other features."""
from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from pancad.geometry import Point
from pancad.geometry.constants import SketchConstraint

from pancad.cad.freecad._application_types import FreeCADLineSegment

if TYPE_CHECKING:
    from pancad.geometry.constraints import AbstractConstraint
    from pancad.cad.freecad._application_types import FreeCADConstraint
    from pancad.cad.freecad._feature_mappers import FreeCADMap
    from pancad.cad.freecad._map_typing import SketchElementID

class ConstraintType(StrEnum):
    """An enumeration used to define which FreeCAD constraints are supported."""
    ANGLE = "Angle"
    COINCIDENT = "Coincident"
    DIAMETER = "Diameter"
    DISTANCE = "Distance"
    DISTANCE_X = "DistanceX"
    DISTANCE_Y = "DistanceY"
    EQUAL = "Equal"
    HORIZONTAL = "Horizontal"
    INTERNAL_ALIGNMENT = "InternalAlignment"
    PARALLEL = "Parallel"
    PERPENDICULAR = "Perpendicular"
    POINT_ON_OBJECT = "PointOnObject"
    RADIUS = "Radius"
    TANGENT = "Tangent"
    VERTICAL = "Vertical"
    def get_sketch_constraint(self,
                              mapping: FreeCADMap,
                              constraint: FreeCADConstraint,
                              constraint_id: SketchElementID,
                              ) -> SketchConstraint:
        """Returns the ConstraintType's equivalent 
        :class:`~pancad.geometry.constants.SketchConstraint`
        
        :param constraint: The freecad constraint to get the equivalent 
            SketchConstraint from.
        :param constraint_id: The freecad id of the constraint.
        :raises ValueError: When the ConstraintType does not have an equivalent 
            SketchConstraint.
        """
        if constraint.Type in _TO_SKETCH_CONSTRAINT:
            return _TO_SKETCH_CONSTRAINT[constraint.Type]
        if constraint.Type == ConstraintType.TANGENT:
            geometry = mapping.get_constrained(constraint_id)
            if all(isinstance(g, FreeCADLineSegment) for g in geometry):
                # FreeCAD uses Tangent to mean coincident or collinear when
                # applied to two line segments.
                return SketchConstraint.COINCIDENT
            return SketchConstraint.TANGENT
        if constraint.Type == ConstraintType.INTERNAL_ALIGNMENT:
            raise ValueError("No equivalent SketchConstraint for"
                             " INTERNAL_ALIGNMENT, should stay internal"
                             " to FreeCAD.")
        raise ValueError(f"Unsupported type {self}")
    @classmethod
    def from_pancad(cls, constraint: AbstractConstraint) -> ConstraintType:
        """Returns the pancad constraint's equivalent ConstraintType.
        
        :raises TypeError: Raised when the pancad constraint does not have have 
            a ConstraintType equivalent.
        """
        if (type_ := type(constraint).__qualname__) in _TO_CONSTRAINT_TYPE:
            return _TO_CONSTRAINT_TYPE[type_]
        if type_ == "Coincident":
            geometries = constraint.get_geometry()
            if all(isinstance(g, Point) for g in geometries):
                # Point on Point -> Coincident
                return ConstraintType.COINCIDENT
            if any(isinstance(g, Point) for g in geometries):
                # Point on Curve/Line -> PointOnObject
                return ConstraintType.POINT_ON_OBJECT
            return ConstraintType.TANGENT # Curve/Line on Curve/Line -> Tangent
        raise TypeError(f"Unsupported type {type_}")

_TO_SKETCH_CONSTRAINT = {
    ConstraintType.ANGLE: SketchConstraint.ANGLE,
    ConstraintType.COINCIDENT: SketchConstraint.COINCIDENT,
    ConstraintType.DIAMETER: SketchConstraint.DISTANCE_DIAMETER,
    ConstraintType.DISTANCE: SketchConstraint.DISTANCE,
    ConstraintType.DISTANCE_X: SketchConstraint.DISTANCE_HORIZONTAL,
    ConstraintType.DISTANCE_Y: SketchConstraint.DISTANCE_VERTICAL,
    ConstraintType.EQUAL: SketchConstraint.EQUAL,
    ConstraintType.HORIZONTAL: SketchConstraint.HORIZONTAL,
    ConstraintType.PARALLEL: SketchConstraint.PARALLEL,
    ConstraintType.PERPENDICULAR: SketchConstraint.PERPENDICULAR,
    ConstraintType.POINT_ON_OBJECT: SketchConstraint.COINCIDENT,
    ConstraintType.RADIUS: SketchConstraint.DISTANCE_RADIUS,
    ConstraintType.VERTICAL: SketchConstraint.VERTICAL,
}
"""A map for one-to-one translations from ConstraintType to SketchConstraint."""
_TO_CONSTRAINT_TYPE = {
    "Angle": ConstraintType.ANGLE,
    "Diameter": ConstraintType.DIAMETER,
    "Distance": ConstraintType.DISTANCE,
    "Equal": ConstraintType.EQUAL,
    "Horizontal": ConstraintType.HORIZONTAL,
    "HorizontalDistance": ConstraintType.DISTANCE_X,
    "Parallel": ConstraintType.PARALLEL,
    "Perpendicular": ConstraintType.PERPENDICULAR,
    "Radius": ConstraintType.RADIUS,
    "Vertical": ConstraintType.VERTICAL,
    "VerticalDistance": ConstraintType.DISTANCE_Y,
}
"""A map for one-to-one translations from Constrant name to ConstraintType."""
