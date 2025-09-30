"""
A module providing GenericAlias constants for use in FreeCAD-PanCAD mapping.
"""
from PanCAD.geometry.constants import ConstraintReference
from PanCAD.cad.freecad import FreeCADCADObject
from PanCAD.cad.freecad.constants import ListName, InternalAlignmentType

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

SubFeatureID = tuple[FeatureID, ConstraintReference]
SubFeatureMap = dict[ConstraintReference, FreeCADID]

InternalAlignmentMap = dict[InternalAlignmentType, GeometryIndex]

FreeCADIDMap = dict[FreeCADID, FreeCADCADObject]
"""Maps FreeCAD IDs to their corresponding FreeCADCADObject."""