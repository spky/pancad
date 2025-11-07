"""A module containing element linking methods for FreeCADMap. These methods are 
meant to be imported into the FreeCADMap class and used there or by each other.
"""
from __future__ import annotations

from functools import singledispatchmethod
from typing import TYPE_CHECKING

from pancad.geometry import (
    AbstractGeometry,
    AbstractFeature,
    CoordinateSystem,
    Ellipse,
    FeatureContainer,
    Sketch,
    Extrude,
)
from pancad.geometry.constants import ConstraintReference
from pancad.utils.relations import OneToOne, OneToMany

from .constants import InternalAlignmentType, ListName, SketchNumber
from ._application_types import (
    FreeCADBody, FreeCADOrigin, FreeCADPad, FreeCADSketch
)
from ._map_typing import SketchElementID

if TYPE_CHECKING:
    from ._application_types import FreeCADFeature

################################################################################
# Single Dispatches ############################################################
################################################################################
@singledispatchmethod
def _link_features(self, key: AbstractFeature, value: FreeCADFeature) -> None:
    """Adds a pancad parent and FreeCAD child feature pairing to the map along 
    with any geometry elements inside the feature.
    
    :param key: The pancad Feature to link.
    :param value: The FreeCAD Feature to link.
    :raises TypeError: Raised if an unrecognized feature type is provided.
    """
    raise TypeError(f"Unrecognized pancad feature type {key.__class__}")

@singledispatchmethod
def _link_geometry(self,
                   geometry: AbstractGeometry,
                   freecad_id: SketchElementID) -> None:
    """Creates the mapping between the pancad and FreeCAD elements created by 
    FreeCADMap before this step.Does not link the constraints since that cannot 
    be completed until the geometry has been fully linked.
    
    :param geometry: A pancad AbstractGeometry object.
    :param freecad_id: A SketchElementID type FreeCADID for the equivalent 
        FreeCAD object.
    """
    # This default handles cases where the geometry in pancad is one to one with 
    # geometry in FreeCAD.
    sketch_id, list_name, index = freecad_id
    relation = OneToOne(geometry.uid, freecad_id, ConstraintReference.CORE)
    self._pancad_to_freecad[geometry.uid] = (geometry, freecad_id)
    self._freecad_to_pancad[freecad_id] = (geometry,
                                           ConstraintReference.CORE)
    reference_map = dict()
    for reference in geometry.get_all_references():
        reference_map[reference] = index
    self._geometry_map[freecad_id] = reference_map

################################################################################
# pancad ---> FreeCAD Feature Link Registers ###################################
################################################################################
@_link_features.register
def _coordinate_system(self,
                       key: CoordinateSystem,
                       origin: FreeCADOrigin) -> None:
    subelements = {ConstraintReference.CORE: origin.ID,
                   ConstraintReference.ORIGIN: origin.ID}
    subreferences = [ConstraintReference.X,
                     ConstraintReference.Y,
                     ConstraintReference.Z,
                     ConstraintReference.XY,
                     ConstraintReference.XZ,
                     ConstraintReference.YZ]
    for i, reference in enumerate(subreferences):
        subelements[reference] = origin.OriginFeatures[i].ID
    self._feature_map[origin.ID] = subelements
    self._pancad_to_freecad[key.uid] = (key, origin.ID)
    
    # Map back to pancad
    reversed_subelements = dict()
    for reference, feature_id in subelements.items():
        if feature_id not in reversed_subelements:
            # Will skip the ORIGIN reference since that is a duplicate.
            reversed_subelements.update({feature_id: (key, reference)})
    self._freecad_to_pancad.update(reversed_subelements)

@_link_features.register
def _one_to_one(self,
                key: Extrude | FeatureContainer,
                value: FreeCADPad | FreeCADBody) -> None:
    # Handles the cases where the mapping is just one-to-one with pancad.
    self._feature_map[value.ID] = {ConstraintReference.CORE: value.ID}
    self._pancad_to_freecad[key.uid] = (key, value.ID)
    self._freecad_to_pancad[value.ID] = (key, ConstraintReference.CORE)

@_link_features.register
def _sketch(self, key: Sketch, sketch: FreeCADSketch) -> None:
    # First, map the Feature
    self._pancad_to_freecad[key.uid] = (key, sketch.ID)
    
    # Link FreeCAD sketch origin/axes definition in its ExternalGeo list.
    x_axis_id = (sketch.ID, ListName.EXTERNALS, SketchNumber.SKETCH_X_AXIS)
    y_axis_id = (sketch.ID, ListName.EXTERNALS, SketchNumber.SKETCH_Y_AXIS)
    subelements = {ConstraintReference.CORE: sketch.ID,
                   ConstraintReference.ORIGIN: x_axis_id,
                   ConstraintReference.X: x_axis_id,
                   ConstraintReference.Y: y_axis_id,}
    self._feature_map[sketch.ID] = subelements
    self._freecad_to_pancad.update(
        {freecad_id: (key, reference)
         for reference, freecad_id in subelements.items()}
    )
    
    # Second, map the geometry inside of the sketch
    self._id_map[x_axis_id] = sketch.ExternalGeo[SketchNumber.SKETCH_X_AXIS]
    self._id_map[y_axis_id] = sketch.ExternalGeo[SketchNumber.SKETCH_Y_AXIS]
    x_line_references = [ConstraintReference.CORE,
                         ConstraintReference.X,
                         ConstraintReference.ORIGIN]
    y_line_references = [ConstraintReference.CORE, ConstraintReference.Y]
    self._geometry_map[x_axis_id] = dict.fromkeys(x_line_references,
                                                  SketchNumber.SKETCH_X_AXIS)
    self._geometry_map[y_axis_id] = dict.fromkeys(y_line_references,
                                                  SketchNumber.SKETCH_Y_AXIS)
    
    for geometry, construction in zip(key.geometry, key.construction):
        _, freecad_id = self._pancad_to_freecad[geometry.uid]
        self._link_geometry(geometry, freecad_id)

################################################################################
# pancad ---> FreeCAD Geometry Link Registers ##################################
################################################################################

@_link_geometry.register
def _ellipse(self,
             ellipse: Ellipse,
             freecad_id: SketchElementID) -> None:
    # This register handles the Ellipse as a special case because FreeCAD aligns 
    # internal geometry with ellipse portions, making the mapping more complex 
    # than just one-to-one.
    sketch_id, list_name, index = freecad_id
    self._pancad_to_freecad[ellipse.uid] = (ellipse, freecad_id)
    self._freecad_to_pancad[freecad_id] = (ellipse,
                                           ConstraintReference.CORE)
    
    subgeometry = {ConstraintReference.CORE: index,
                   ConstraintReference.CENTER: index}
    # Get the internal geometry and add to subgeometry
    internals = self._constraint_map.get_internal_geometry(freecad_id)
    for alignment_type, index in internals.items():
        match alignment_type:
            # First element is the primary reference
            case InternalAlignmentType.ELLIPSE_MAJOR_DIAMETER:
                references = [ConstraintReference.X,
                              ConstraintReference.X_MAX,
                              ConstraintReference.X_MIN]
            case InternalAlignmentType.ELLIPSE_MINOR_DIAMETER:
                references = [ConstraintReference.Y,
                              ConstraintReference.Y_MAX,
                              ConstraintReference.Y_MIN]
            case InternalAlignmentType.ELLIPSE_FOCUS_1:
                references = [ConstraintReference.FOCAL_PLUS]
            case InternalAlignmentType.ELLIPSE_FOCUS_2:
                references = [ConstraintReference.FOCAL_MINUS]
            case _:
                raise ValueError("Unrecognized InternalAlignmentType ellipse"
                                 f"option: {alignment_type}")
        
        sub_id = (sketch_id, ListName.GEOMETRY, index)
        # Map back to pancad to the primary reference option for each internal 
        # sub geometry
        self._freecad_to_pancad[sub_id] = (ellipse, references[0])
        self._geometry_map[sub_id] = {ConstraintReference.CORE: index}
        for reference in references:
            subgeometry[reference] = index
    self._geometry_map[freecad_id] = subgeometry
