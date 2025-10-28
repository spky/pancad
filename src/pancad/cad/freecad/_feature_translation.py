"""A module providing methods for FreeCADMap to translate features to and from 
FreeCAD.
"""
from functools import singledispatchmethod

from math import pi
import numpy as np

from pancad.geometry import (
    AbstractFeature,
    AbstractGeometry,
    Circle,
    CircularArc,
    CoordinateSystem,
    Ellipse,
    Extrude,
    FeatureContainer,
    LineSegment,
    Point,
    Sketch,
)
from pancad.geometry.constants import ConstraintReference
from . import App, Part
from .constants import ListName, ObjectType, PadType
from ._application_types import (
    FreeCADBody,
    FreeCADCircle,
    FreeCADCircularArc,
    FreeCADEllipse,
    FreeCADFeature,
    FreeCADGeometry,
    FreeCADLineSegment,
    FreeCADOrigin,
    FreeCADPad,
    FreeCADPoint,
    FreeCADSketch,
)
from ._map_typing import SketchElementID

################################################################################
# pancad ---> FreeCAD Features
################################################################################
@singledispatchmethod
def _pancad_to_freecad_feature(self,
                               feature: AbstractFeature) -> FreeCADFeature:
    """Creates a FreeCAD equivalent to the pancad feature and adds its id to the 
    id map. Will also create geometry inside of features if any exist and add 
    them to the map.
    """
    raise TypeError(f"Unrecognized pancad feature type {key.__class__}")

@_pancad_to_freecad_feature.register
def _coordinate_system(self, system: CoordinateSystem) -> FreeCADOrigin:
    parent = self[system.context]
    origin = parent.Origin
    self._id_map[origin.ID] = origin
    for subfeature in origin.OriginFeatures:
        self._id_map[subfeature.ID] = subfeature
    return origin

@_pancad_to_freecad_feature.register
def _extrude(self, pancad_extrude: Extrude) -> FreeCADFeature:
    pad = self._document.addObject(ObjectType.PAD, pancad_extrude.name)
    parent = self[pancad_extrude.context]
    parent.addObject(pad)
    pad.Profile = (self[pancad_extrude.profile], [""])
    pad.Length = pancad_extrude.length
    pad.ReferenceAxis = (self[pancad_extrude.profile], ["N_Axis"])
    self[pancad_extrude.profile].Visibility = False
    self._id_map[pad.ID] = pad
    return pad

@_pancad_to_freecad_feature.register
def _feature_container(self, container: FeatureContainer) -> FreeCADBody:
    body = self._document.addObject(ObjectType.BODY, container.name)
    self._id_map[body.ID] = body
    return body

@_pancad_to_freecad_feature.register
def _sketch(self, pancad_sketch: Sketch) -> FreeCADSketch:
    # Creates both the feature and the equivalent geometry inside the sketch.
    sketch = self._document.addObject(ObjectType.SKETCH, pancad_sketch.name)
    sketch_plane = self[pancad_sketch.coordinate_system,
                        pancad_sketch.plane_reference]
    parent = self[pancad_sketch.context]
    parent.addObject(sketch)
    sketch.AttachmentSupport = (sketch_plane, [""])
    sketch.MapMode = "FlatFace"
    sketch.Label = pancad_sketch.name
    self._id_map[sketch.ID] = sketch
    
    # Add geometry in the sketch
    pancad_pairs = zip(pancad_sketch.geometry, pancad_sketch.construction)
    for pancad_geometry, construction in pancad_pairs:
        geometry = self._pancad_to_freecad_geometry(pancad_geometry)
        geometry_id = self._freecad_add_to_sketch(geometry,
                                                  sketch,
                                                  construction)
        # The initial map between the pancad sketch geometry and the core 
        # element of the freecad sketch geometry has to be set here because 
        # there's no way to know which element corresponds to which unless 
        # the single core relationship is mapped during generation.
        self._pancad_to_freecad[pancad_geometry.uid] = (pancad_geometry,
                                                        geometry_id)
    return sketch

################################################################################
# pancad ---> FreeCAD Geometry
################################################################################
@singledispatchmethod
@staticmethod
def _pancad_to_freecad_geometry(geometry: AbstractGeometry) -> FreeCADGeometry:
    """Returns an equivalent FreeCAD geometry element from pancad Geometry."""
    raise TypeError(f"Unsupported pancad element type: {geometry}")

@_pancad_to_freecad_geometry.register
@staticmethod
def _line_segment(line_segment: LineSegment) -> FreeCADLineSegment:
    start = App.Vector(tuple(line_segment.point_a) + (0,))
    end = App.Vector(tuple(line_segment.point_b) + (0,))
    return Part.LineSegment(start, end)

@_pancad_to_freecad_geometry.register
@staticmethod
def _ellipse(ellipse: Ellipse) -> FreeCADEllipse:
    major_axis_point = App.Vector(tuple(ellipse.get_major_axis_point()) + (0,))
    minor_axis_point = App.Vector(tuple(ellipse.get_minor_axis_point()) + (0,))
    center = App.Vector(tuple(ellipse.center) + (0,))
    return Part.Ellipse(major_axis_point, minor_axis_point, center)

@_pancad_to_freecad_geometry.register
@staticmethod
def _circle(circle: Circle) -> FreeCADCircle:
    center = App.Vector(tuple(circle.center) + (0,))
    normal = App.Vector((0, 0, 1))
    return Part.Circle(center, normal, circle.radius)

@_pancad_to_freecad_geometry.register
@staticmethod
def _circular_arc(arc: CircularArc) -> FreeCADCircularArc:
    center = App.Vector(tuple(arc.center) + (0,))
    normal = App.Vector((0, 0, 1))
    circle =  Part.Circle(center, normal, arc.radius)
    
    if arc.is_clockwise:
        # All FreeCAD circular arcs are drawn counterclockwise
        end = arc.start_angle
        start = arc.end_angle
    else:
        start = arc.start_angle
        end = arc.end_angle
    
    # FreeCAD's circular arc angles are all positive
    if start < 0:
        start += 2 * pi
    if end < 0:
        end += 2 * pi
    if end < start:
        # FreeCAD forces the end angle to be larger than the start angle
        end += 2 * pi
    return Part.ArcOfCircle(circle, start, end)

# Adding FreeCAD Geometry to Sketch and setting internal id
@singledispatchmethod
def _freecad_add_to_sketch(self,
                           geometry: FreeCADGeometry,
                           sketch: FreeCADSketch,
                           construction: bool) -> SketchElementID:
    """Adds the geometry to the FreeCAD sketch and returns its unique pancad 
    derived id. Updates the internal FreeCADMap's id map to include the new 
    geometry and any sub geometry.
    """
    raise TypeError(f"Unsupported pancad element type: {geometry}")

@_freecad_add_to_sketch.register
def _ellipse(self,
             ellipse: FreeCADEllipse,
             sketch: FreeCADSketch,
             construction:bool) -> SketchElementID:
    initial_index = len(sketch.Geometry)
    sketch.addGeometry(ellipse, construction)
    sketch.exposeInternalGeometry(initial_index)
    for index in range(initial_index, initial_index + 4):
        geometry_id = (sketch.ID, ListName.GEOMETRY, index) 
        self._id_map[geometry_id] = sketch.Geometry[index]
    # Returns the id of the ellipse element, not the sub elements
    return (sketch.ID, ListName.GEOMETRY, initial_index)

@_freecad_add_to_sketch.register
def _one_to_one_cases(self,
                      geometry: (FreeCADLineSegment
                                 | FreeCADCircle
                                 | FreeCADCircularArc),
                      sketch: FreeCADSketch,
                      construction: bool) -> SketchElementID:
    index = len(sketch.Geometry)
    sketch.addGeometry(geometry, construction)
    geometry_id = (sketch.ID, ListName.GEOMETRY, index)
    self._id_map[geometry_id] = geometry
    return geometry_id

################################################################################
# FreeCAD ---> pancad Features
################################################################################

def _freecad_to_pancad_feature(self,
                               feature: FreeCADFeature) -> AbstractFeature:
    """Generates a contextless pancad feature equivalent to the FreeCAD feature.
    """
    match feature.TypeId:
        # Poor man's singledispatchmethod using the FreeCAD TypeId
        case ObjectType.BODY:
            pancad_feature = _ftpf_container(self, feature)
        case ObjectType.SKETCH:
            pancad_feature = _ftpf_sketch(self, feature)
        case ObjectType.PAD:
            pancad_feature = _ftpf_extrude(self, feature)
        case ObjectType.ORIGIN:
            pancad_feature = _ftpf_coordinate_system(self, feature)
        case _:
            raise TypeError(f"Unrecognized TypeId '{feature.TypeId}'")
    
    # Eliminate duplicate parents
    parent_list = list(set(feature.Parents))
    if len(parent_list) == 1:
        # Add pancad geometry to its context
        parent, _ = parent_list[0]
        pancad_context, _ = self._freecad_to_pancad[parent.ID]
        pancad_context.add_feature(pancad_feature)
    elif not parent_list and isinstance(pancad_feature, FeatureContainer):
        # Found the top level element, can only have one right now
        self._part_file.container = pancad_feature
    elif not parent_list:
        raise ValueError("Elements with no parents are expected to be"
                         " PartFile container and expected to be"
                         " FeatureContainers, got: "
                         f" {pancad_feature.__class__}")
    else:
        raise ValueError("Unknown situation where FreeCAD object has two"
                         " or more unique parents! Please make a github"
                         " issue so it can be supported.")
    return pancad_feature

# ABBREVIATION
# ftpf = freecad_to_pancad_feature
def _ftpf_container(self, body: FreeCADBody) -> FeatureContainer:
    self._id_map[body.ID] = body
    return FeatureContainer(name=body.Label)

def _ftpf_coordinate_system(self, origin: FreeCADOrigin) -> FeatureContainer:
    if len(origin.Parents) > 1:
        raise ValueError("Unknown situation where FreeCAD object has"
                         " two or more unique parents! Please make a"
                         " github issue so it can be supported.")
    self._id_map[origin.ID] = origin
    for subfeature in origin.OriginFeatures:
        self._id_map[subfeature.ID] = subfeature
    body, _ = origin.Parents[0]
    location = tuple(body.Placement.Base)
    components = body.Placement.Rotation.Q
    components =(components[-1],) + components[0:3]
    quat = np.quaternion(*components)
    return CoordinateSystem.from_quaternion(location, quat, name=origin.Label)

def _ftpf_extrude(self, pad: FreeCADPad) -> Extrude:
    self._id_map[pad.ID] = pad
    freecad_profile, _ = pad.Profile
    profile, _ = self._freecad_to_pancad[freecad_profile.ID]
    feature_type = PadType(pad.Type).get_feature_type(pad.Midplane,
                                                      pad.Reversed)
    unit = pad.Length.toStr().split(" ")[-1]
    # Up to face/feature not handled in the return, future work
    return Extrude(profile,
                   feature_type,
                   length=pad.Length.Value,
                   opposite_length=pad.Length2.Value, # Assuming the same unit
                   is_midplane=pad.Midplane,
                   is_reverse_direction=pad.Reversed,
                   unit=unit,
                   name=pad.Label)

def _ftpf_sketch(self, freecad_sketch: FreeCADSketch) -> Sketch:
    self._id_map[freecad_sketch.ID] = freecad_sketch
    support, _ = freecad_sketch.AttachmentSupport[0]
    coordinate_system, reference = self.get_pancad(support.ID)
    sketch = Sketch(coordinate_system=coordinate_system,
                    plane_reference=reference,
                    name=freecad_sketch.Label)
    # Ensure that all internal geometry has been added to Geometry
    for i, freecad_geometry in enumerate(freecad_sketch.Geometry):
        try:
            freecad_sketch.exposeInternalGeometry(i)
        except ValueError:
            # FreeCAD doesn't provide a way to check whether something has 
            # internal geometry, so this function can be run on each item and 
            # then pancad can just ignore the errors
            pass
    
    # Actually translate geometry
    for i, freecad_geometry in enumerate(freecad_sketch.Geometry):
        geometry = self._freecad_to_pancad_geometry(freecad_geometry)
        sketch.add_geometry(geometry, freecad_sketch.getConstruction(i))
        geometry_id = (freecad_sketch.ID, ListName.GEOMETRY, i)
        self._id_map[geometry_id] = freecad_geometry
        self._pancad_to_freecad[geometry.uid] = (geometry, geometry_id)
        self._freecad_to_pancad[geometry_id] = (geometry,
                                                ConstraintReference.CORE)
    return sketch

################################################################################
# FreeCAD ---> pancad Geometry
################################################################################

@singledispatchmethod
@staticmethod
def _freecad_to_pancad_geometry(geometry: FreeCADGeometry) -> AbstractGeometry:
    """Returns pancad geometry from FreeCAD geometry elements."""
    raise TypeError(f"Unsupported FreeCAD element type: {geometry}")

@_freecad_to_pancad_geometry.register
@staticmethod
def _line_segment(line_segment: FreeCADLineSegment) -> LineSegment:
    return LineSegment(line_segment.StartPoint[0:2],
                       line_segment.EndPoint[0:2])

@_freecad_to_pancad_geometry.register
@staticmethod
def _circle(circle: FreeCADCircle) -> Circle:
    return Circle(circle.Center[0:2], circle.Radius)

@_freecad_to_pancad_geometry.register
@staticmethod
def _circular_arc(arc: FreeCADCircularArc) -> CircularArc:
    center = np.array(arc.Center[0:2])
    start_vector = np.array(arc.StartPoint[0:2]) - center
    end_vector = np.array(arc.EndPoint[0:2]) - center
    return CircularArc(center, arc.Radius, start_vector, end_vector, False)

@_freecad_to_pancad_geometry.register
@staticmethod
def _point(point: FreeCADPoint) -> Point:
    return Point(point.X, point.Y)

@_freecad_to_pancad_geometry.register
@staticmethod
def _ellipse(ellipse: FreeCADEllipse) -> Ellipse:
    return Ellipse.from_angle(ellipse.Center[0:2],
                              ellipse.MajorRadius,
                              ellipse.MinorRadius,
                              ellipse.AngleXU)