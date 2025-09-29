"""A module providing functions to generate PanCAD/FreeCAD sketch geometry from 
FreeCAD/PanCAD sketch geometry.
"""
from functools import singledispatch

import numpy as np
import quaternion

from PanCAD.cad.freecad import (App, Sketcher, Part,
                                FreeCADBody,
                                FreeCADConstraint,
                                FreeCADFeature,
                                FreeCADGeometry,
                                FreeCADCADObject,
                                FreeCADOrigin,)
from PanCAD.cad.freecad.constants import ObjectType

from PanCAD.geometry import (AbstractGeometry,
                             AbstractFeature,
                             Circle,
                             CoordinateSystem,
                             Ellipse,
                             Extrude,
                             FeatureContainer,
                             LineSegment,
                             Sketch,)
from PanCAD.geometry.constants import ConstraintReference

################################################################################
# PanCAD --> FreeCAD
################################################################################

# FreeCAD Sketch Geometry ######################################################

@singledispatch
def pancad_to_freecad_geometry(pancad: AbstractGeometry) -> object:
    raise TypeError(f"Unsupported PanCAD element type: {pancad}")

@pancad_to_freecad_geometry.register
def _line_segment(line_segment: LineSegment) -> Part.LineSegment:
    start = App.Vector(tuple(line_segment.point_a) + (0,))
    end = App.Vector(tuple(line_segment.point_b) + (0,))
    return Part.LineSegment(start, end)

@pancad_to_freecad_geometry.register
def _ellipse(ellipse: Ellipse) -> Part.Ellipse:
    major_axis_point = App.Vector(tuple(ellipse.get_major_axis_point()) + (0,))
    minor_axis_point = App.Vector(tuple(ellipse.get_minor_axis_point()) + (0,))
    center = App.Vector(tuple(ellipse.center) + (0,))
    return Part.Ellipse(major_axis_point, minor_axis_point, center)

@pancad_to_freecad_geometry.register
def _circle(circle: Circle) -> Part.Circle:
    center = App.Vector(tuple(circle.center) + (0,))
    normal = App.Vector((0, 0, 1))
    return Part.Circle(center, normal, circle.radius)

# Generate PanCAD Sketch Geometry
@singledispatch
def get_pancad_sketch_geometry(freecad: object) -> AbstractGeometry:
    raise TypeError(f"Unsupported PanCAD element type: {pancad}")

@get_pancad_sketch_geometry.register
def _line_segment(line_segment: Part.LineSegment) -> LineSegment:
    start = tuple(line_segment.StartPoint)[0:2]
    end = tuple(line_segment.EndPoint)[0:2]
    return LineSegment(start, end)

@get_pancad_sketch_geometry.register
def _circle(circle: Part.Circle) -> Circle:
    center = tuple(circle.Center)[0:2]
    return Circle(center, circle.Radius)

# FreeCAD Features #############################################################

@singledispatch
def pancad_to_freecad_feature(pancad: AbstractFeature,
                              document: App.Document) -> FreeCADFeature:
    raise TypeError(f"Unsupported PanCAD element type: {pancad}")

@pancad_to_freecad_feature.register
def _sketch(pancad_sketch: Sketch, document: App.Document) -> Sketcher.Sketch:
    sketch = document.addObject(ObjectType.SKETCH, sketch.name)
    
    origin = feature_map[(pancad_sketch.coordinate_system,
                          ConstraintReference.ORIGIN)]
    support = feature_map[(pancad_sketch.coordinate_system,
                           pancad_sketch.plane_reference)]
    parent = origin.getParent()
    sketch = parent.newObject(ObjectType.SKETCH, pancad_sketch.uid)
    sketch.AttachmentSupport = (support, [""])
    sketch.MapMode = "FlatFace"
    return sketch

@pancad_to_freecad_feature.register
def _pad(pancad_extrude: Extrude, feature_map: dict) -> Part.Feature:
    profile = feature_map[(pancad_extrude.profile, ConstraintReference.CORE)]
    parent = profile.getParent()
    pad = parent.newObject(ObjectType.PAD, pancad_extrude.uid)
    pad.Profile = (profile, [""])
    pad.Length = pancad_extrude.length
    pad.ReferenceAxis = (profile, ["N_Axis"])
    profile.Visibility = False

################################################################################
# FreeCAD --> PanCAD
################################################################################

# PanCAD Features ##############################################################

def freecad_to_pancad_feature(feature: FreeCADFeature) -> AbstractFeature:
    """Generates a contextless PanCAD feature equivalent to the FreeCAD feature.
    """
    match feature.TypeId:
        # Poor man's singledispatchmethod using the FreeCAD TypeId
        case ObjectType.BODY:
            return _freecad_to_pancad_feature_container(feature)
        case ObjectType.SKETCH:
            pass
        case ObjectType.PAD:
            pass
        case ObjectType.ORIGIN:
            return _freecad_to_pancad_feature_coordinate_system(feature)
        case _:
            raise TypeError(f"Unrecognized TypeId '{feature.TypeId}'")

def _freecad_to_pancad_feature_container(body: FreeCADBody) -> FeatureContainer:
    return FeatureContainer(name=body.Label)

def _freecad_to_pancad_feature_coordinate_system(origin: FreeCADOrigin
                                                 ) -> FeatureContainer:
    if len(origin.Parents) > 1:
        raise ValueError("Unknown situation where FreeCAD object has"
                         " two or more unique parents! Please make a"
                         " github issue so it can be supported.")
    
    body, _ = origin.Parents[0]
    location = tuple(body.Placement.Base)
    quaternion_components = body.Placement.Rotation.Q
    quat = np.quaternion(*quaternion_components)
    return CoordinateSystem.from_quaternion(location, quat, name=origin.Label)