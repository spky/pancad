from collections import OrderedDict

from PanCAD.cad.freecad import App, Sketcher, Part
# from PanCAD.cad.freecad.feature_mappers import map_freecad
from PanCAD.cad.freecad.sketch_constraints import translate_constraint
from PanCAD.cad.freecad.sketch_geometry import (pancad_to_freecad_geometry,
                                                pancad_to_freecad_feature)
from PanCAD.cad.freecad.constants import ObjectType, EdgeSubPart

from PanCAD.filetypes import PartFile
from PanCAD.geometry import (
    Circle, CoordinateSystem, Extrude, LineSegment, Sketch
)
from PanCAD.geometry.constraints import (
    Coincident, Vertical, Horizontal,
    Distance, HorizontalDistance, VerticalDistance,
    Radius, Diameter,
)
from PanCAD.geometry.constants import ConstraintReference
from PanCAD.utils import file_handlers

def add_feature_to_freecad(feature: Sketch | Extrude,
                           feature_map: dict) -> dict:
    """Adds the feature to the freecad file and updates the feature map to 
    maintain the connection between the new freecad feature and the pancad 
    feature.
    
    :param feature: A PanCAD feature.
    :param feature_map: A dict connecting pancad objects to equivalent freecad 
        objects.
    :return: The feature_map with new entries for the feature.
    """
    freecad_feature = pancad_to_freecad_feature(feature, feature_map)
    feature_map.update(
        {(feature, ConstraintReference.CORE): freecad_feature}
    )
    if isinstance(feature, Sketch):
        feature_map = map_sketch_geometry(feature, feature_map)
    # if isinstance(feature, Sketch):
        # # Assumes that the sketch is placed on a freecad coordinate system
        # freecad_origin = feature_map[
            # (feature.coordinate_system, ConstraintReference.ORIGIN)
        # ]
        # origin_parent = freecad_origin.getParent()
        # # Add sketch to file and to map
        # freecad_sketch = origin_parent.newObject(ObjectType.SKETCH, feature.uid)
        # support = feature_map[
            # (feature.coordinate_system, feature.plane_reference)
        # ]
        # freecad_sketch.AttachmentSupport = (support, [""])
        # freecad_sketch.MapMode = "FlatFace"
        # feature_map.update(
            # {(feature, ConstraintReference.CORE): freecad_sketch}
        # )
        # # Add geometry to sketch and to map
        # feature_map = map_sketch_geometry(feature, feature_map)
    # elif isinstance(feature, Extrude):
        # freecad_profile = feature_map[
            # (feature.profile, ConstraintReference.CORE)
        # ]
        # profile_parent = freecad_profile.getParent()
        # freecad_pad = profile_parent.newObject(ObjectType.PAD, feature.uid)
        
        # freecad_pad.Profile = (freecad_profile, [""])
        # freecad_pad.Length = feature.length
        # freecad_pad.ReferenceAxis = (freecad_profile, ["N_Axis"])
        # freecad_profile.Visibility = False
    # else:
        # raise ValueError(f"Feature class {feature.__class__} not recognized")
    return feature_map

def map_sketch_geometry(sketch: Sketch, feature_map: dict) -> dict:
    """Updates and returns a feature_map with the geometry in the sketch.
    
    :param sketch: A PanCAD sketch.
    :param feature_map: A dict connecting pancad objects to equivalent freecad 
        objects.
    """
    freecad_sketch = feature_map[(sketch, ConstraintReference.CORE)]
    
    for i, (geo, cons) in enumerate(zip(sketch.geometry, sketch.construction)):
        # Add all sketch geometry
        new_geometry = pancad_to_freecad_geometry(geo)
        freecad_sketch.addGeometry(new_geometry, cons)
        feature_map.update({(sketch, "geometry", i): new_geometry})
    
    for i, constraint in enumerate(sketch.constraints):
        # Add all sketch constraints
        new_constraint = translate_constraint(sketch, constraint)
        freecad_sketch.addConstraint(new_constraint)
        feature_map.update(
            {(sketch, "constraint", i): new_constraint}
        )
    
    return feature_map