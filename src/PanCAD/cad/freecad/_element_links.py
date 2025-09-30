from functools import singledispatchmethod

from PanCAD.geometry import (
    PanCADThing,
    AbstractGeometry,
    AbstractFeature,
    Circle,
    CoordinateSystem,
    Ellipse,
    FeatureContainer,
    LineSegment,
    Sketch,
    Extrude,
)
from PanCAD.geometry.constants import ConstraintReference
from PanCAD.cad.freecad import (
    App,
    Sketcher,
    Part,
    FreeCADBody,
    FreeCADConstraint,
    FreeCADFeature,
    FreeCADGeometry,
    FreeCADCADObject,
    FreeCADOrigin,
    FreeCADPad,
    FreeCADSketch,
)
from PanCAD.cad.freecad.constants import ListName, InternalAlignmentType

from ._map_typing import (
    FeatureID,
    SketchElementID,
    FreeCADID,
    SketchSubGeometryID,
    SubGeometryMap,
    SubFeatureID,
    SubFeatureMap,
)

# Link Features Geometry #######################################################
@singledispatchmethod
def _link_pancad_to_freecad_feature_geometry(self,
                                             key: PanCADThing,
                                             value: FreeCADCADObject):
    """Adds a PanCAD parent and FreeCAD child feature pairing to the map.
    Each key is the PanCAD element's uid, mapped to a tuple with the PanCAD
    parent will be the first element and the FreeCAD feature ID as the
    second element.
    """
    raise TypeError(f"Unrecognized PanCAD geometry type {key.__class__}")

@_link_pancad_to_freecad_feature_geometry.register
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
    
    # Map back to PanCAD
    reversed_subelements = dict()
    for reference, feature_id in subelements.items():
        if feature_id not in reversed_subelements:
            # Will skip the ORIGIN reference since that is a duplicate.
            reversed_subelements.update({feature_id: (key.uid, reference)})
    self._freecad_to_pancad.update(reversed_subelements)

@_link_pancad_to_freecad_feature_geometry.register
def _extrude(self, key: Extrude, pad: FreeCADPad) -> None:
    self._feature_map[pad.ID] = {ConstraintReference.CORE: pad.ID}
    self._pancad_to_freecad[key.uid] = (key, pad.ID)
    self._freecad_to_pancad[pad.ID] = (key.uid, ConstraintReference.CORE)

@_link_pancad_to_freecad_feature_geometry.register
def _feature_container(self,
                       key: FeatureContainer,
                       body: FreeCADBody) -> None:
    self._feature_map[body.ID] = {ConstraintReference.CORE: body.ID}
    self._pancad_to_freecad[key.uid] = (key, body.ID)
    self._freecad_to_pancad[body.ID] = (key.uid, ConstraintReference.CORE)

@_link_pancad_to_freecad_feature_geometry.register
def _sketch(self, key: Sketch, sketch: FreeCADSketch) -> None:
    
    # Map Feature
    self._pancad_to_freecad[key.uid] = (key, sketch.ID)
    
    y_axis_id = (sketch.ID, ListName.EXTERNALS, 1)
    x_axis_id = (sketch.ID, ListName.EXTERNALS, 0)
    subelements = {ConstraintReference.CORE: sketch.ID,
                   ConstraintReference.ORIGIN: x_axis_id,
                   ConstraintReference.X: x_axis_id,
                   ConstraintReference.Y: y_axis_id,}
    self._feature_map[sketch.ID] = subelements
    self._freecad_to_pancad.update(
        {freecad_id: (key.uid, reference)
         for reference, freecad_id in subelements.items()}
    )
    
    # Map the geometry inside of the sketch
    self._id_map[x_axis_id] = sketch.ExternalGeo[0]
    self._id_map[y_axis_id] = sketch.ExternalGeo[1]
    self._geometry_map[x_axis_id] = dict.fromkeys(LineSegment.REFERENCES, 0)
    self._geometry_map[y_axis_id] = dict.fromkeys(LineSegment.REFERENCES, 1)
    
    for geometry, construction in zip(key.geometry, key.construction):
        _, freecad_id = self._pancad_to_freecad[geometry.uid]
        self._link_pancad_to_freecad_geometry(geometry, freecad_id)
    
    # for constraint in key.constraints:
        # constraint_index = len(sketch.Constraints)
        # new_constraint = translate_constraint(key, constraint)
        # sketch.addConstraint(new_constraint)
        # constraint_id = (sketch.ID, ListName.CONSTRAINTS, constraint_index)
        # constrained_ids = tuple()
        # for parent, reference in zip(constraint.get_constrained(),
                                     # constraint.get_references()):
            # sketch_geometry_id = self.get_freecad_id(parent, reference)
            # constrained_ids = constrained_ids + (
                # (*sketch_geometry_id, reference),
            # )
        # self._pancad_to_freecad[constraint.uid] = (constraint,
                                                   # constraint_id)
        # self._freecad_to_pancad[constraint_id] = (constraint.uid,
                                                  # ConstraintReference.CORE)
        # self._id_map[constraint_id] = new_constraint
        # self._constraint_map[constraint_id] = constrained_ids

# Link Geometry ################################################################
@singledispatchmethod
def _link_pancad_to_freecad_geometry(self,
                                     pancad_geometry: AbstractGeometry,
                                     freecad_id: SketchElementID) -> None:
    """Adds the PanCAD geometry to the FreeCAD sketch while also mapping 
    the relations between the new geometry and constraints to PanCAD 
    geometry.
    
    :param pancad_geometry: A PanCAD AbstractGeometry object.
    :param sketch: A FreeCAD sketch.
    :param construction: Sets the geometry to construction is True, 
        non-construction if False.
    :param geometry_index: The index to set the geometry to in the 
        FreeCAD sketch.
    :param constraint_id: The index for the next constraint, if any will 
        be added.
    :returns: The new geometry_index.
    """
    # Default handles cases where the geometry in PanCAD is one to one with 
    # geometry in FreeCAD.
    sketch_id, list_name, index = freecad_id
    self._pancad_to_freecad[pancad_geometry.uid] = (pancad_geometry, freecad_id)
    self._freecad_to_pancad[freecad_id] = (pancad_geometry.uid,
                                           ConstraintReference.CORE)
    reference_map = dict()
    for reference in pancad_geometry.get_all_references():
        reference_map[reference] = index
    self._geometry_map[freecad_id] = reference_map

@_link_pancad_to_freecad_geometry.register
def _ellipse(self,
             ellipse: Ellipse,
             freecad_id: SketchElementID) -> None:
    sketch_id, list_name, index = freecad_id
    self._pancad_to_freecad[ellipse.uid] = (ellipse, freecad_id)
    self._freecad_to_pancad[freecad_id] = (ellipse.uid,
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
        # Map back to PanCAD to the first reference option
        self._freecad_to_pancad[sub_id] = (ellipse.uid, references[0])
        self._geometry_map[sub_id] = {ConstraintReference.CORE: index}
        for reference in references:
            subgeometry[reference] = index
    
    self._geometry_map[freecad_id] = subgeometry
