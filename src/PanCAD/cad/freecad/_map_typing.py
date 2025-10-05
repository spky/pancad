"""
A module providing GenericAlias constants for use in FreeCAD-PanCAD mapping.
"""
from PanCAD.geometry import PanCADThing
from PanCAD.geometry.constants import ConstraintReference

from ._application_types import FreeCADCADObject
from .constants import ListName, InternalAlignmentType

# FreeCAD ID Typing
FeatureID = int
"""The ID that FreeCAD assigns to Features, usually a 4 digit integer."""
GeometryIndex = int
"""The index of a geometry element in a FreeCAD sketch's Geometry or ExternalGeo
list. FreeCAD allows ExternalGeo elements to be referenced by constraints using
negative numbers in addition to the normal Geometry elements in constraints.
"""
ConstraintIndex = int
"""The index of a constraint element in a FreeCAD sketch's Constraints list."""
SketchElementID = tuple[FeatureID, ListName, GeometryIndex]
"""The ID for a FreeCAD geometry or constraint element in a sketch."""
FreeCADID = FeatureID | SketchElementID
"""The unique ID for a FreeCADCADObject."""
SketchSubGeometryID = tuple[FeatureID,
                            ListName,
                            GeometryIndex,
                            ConstraintReference,]
"""The ID for a FreeCAD geometry element acting as the subgeometry of another
geometry element in the same sketch. The FeatureID has to be for a sketch.
"""
SubGeometryMap = dict[ConstraintReference, GeometryIndex]
"""Maps a constraint reference to another sketch index in the same sketch."""

ConstraintMap = dict[SketchElementID, tuple[SketchSubGeometryID]]
"""Maps FreeCAD constraints to their constrained portions of geometry."""

SubFeatureID = tuple[FeatureID, ConstraintReference]
"""Maps FreeCAD features that are really subfeatures of a parent feature to that 
portion of their parent feature (example: An x-axis of an Origin element)
"""
SubFeatureMap = dict[ConstraintReference, FreeCADID]

InternalAlignmentMap = dict[InternalAlignmentType, GeometryIndex]
"""Maps the subgeometry type to the internally aligned geometry index."""
InternalAlignmentConstraintMap = dict[SketchElementID, InternalAlignmentMap]
"""Maps the parent geometry index to its subgeometry being constrained by 
internal alignment constraints.
"""

FreeCADIDMap = dict[FreeCADID, FreeCADCADObject]
"""Maps FreeCAD IDs to their corresponding FreeCADCADObject."""
FreeCADToPanCADMap = dict[FreeCADID, tuple[PanCADThing, ConstraintReference]]
"""Maps FreeCAD IDs back to their PanCAD geometry."""