"""
A module providing methods for FreeCADMap to translate features to and from 
FreeCAD.
"""
from functools import singledispatchmethod

from PanCAD.cad.freecad import (
    App,
    Sketcher,
    Part,
    FreeCADBody,
    FreeCADCircle,
    FreeCADEllipse,
    FreeCADFeature,
    FreeCADGeometry,
    FreeCADLineSegment,
    FreeCADOrigin,
    FreeCADSketch,
)
from PanCAD.cad.freecad.constants import ListName, ObjectType
from PanCAD.geometry import (
    AbstractFeature,
    AbstractGeometry,
    Circle,
    CoordinateSystem,
    Ellipse,
    Extrude,
    FeatureContainer,
    LineSegment,
    Sketch,
)
from ._map_typing import SketchElementID

# PanCAD to FreeCAD
@singledispatchmethod
def _pancad_to_freecad_feature(self,
                               feature: AbstractFeature) -> FreeCADFeature:
    raise TypeError(f"Unrecognized PanCAD feature type {key.__class__}")

@_pancad_to_freecad_feature.register
def _coordinate_system(self, system: CoordinateSystem) -> FreeCADOrigin:
    parent = self[system.context]
    return parent.Origin

@_pancad_to_freecad_feature.register
def _feature_container(self, container: FeatureContainer) -> FreeCADBody:
    body = self._document.addObject(ObjectType.BODY, container.name)
    return body

@_pancad_to_freecad_feature.register
def _extrude(self, pancad_extrude: Extrude) -> FreeCADFeature:
    pad = self._document.addObject(ObjectType.PAD, pancad_extrude.name)
    parent = self[pancad_extrude.context]
    parent.addObject(pad)
    pad.Profile = (self[pancad_extrude.profile], [""])
    pad.Length = pancad_extrude.length
    pad.ReferenceAxis = (self[pancad_extrude.profile], ["N_Axis"])
    self[pancad_extrude.profile].Visibility = False
    return pad

@_pancad_to_freecad_feature.register
def _sketch(self, pancad_sketch: Sketch) -> FreeCADSketch:
    sketch = self._document.addObject(ObjectType.SKETCH, pancad_sketch.name)
    sketch_plane = self[pancad_sketch.coordinate_system,
                        pancad_sketch.plane_reference]
    parent = self[pancad_sketch.context]
    parent.addObject(sketch)
    sketch.AttachmentSupport = (sketch_plane, [""])
    sketch.MapMode = "FlatFace"
    sketch.Label = pancad_sketch.name
    
    geometry_iter = zip(pancad_sketch.geometry, pancad_sketch.construction)
    for pancad_geometry, construction in geometry_iter:
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



# Generating FreeCAD Geometry
@singledispatchmethod
@staticmethod
def _pancad_to_freecad_geometry(geometry: AbstractGeometry) -> FreeCADGeometry:
    raise TypeError(f"Unsupported PanCAD element type: {geometry}")

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

# Adding FreeCAD Geometry to Sketch and setting internal id
@singledispatchmethod
def _freecad_add_to_sketch(self,
                           geometry: FreeCADGeometry,
                           sketch: Sketcher.Sketch,
                           construction: bool) -> SketchElementID:
    """Adds the geometry to the FreeCAD sketch and returns its unique PanCAD 
    derived id. Updates the internal FreeCADMap's id map to include the new 
    geometry and any sub geometry.
    """
    raise TypeError(f"Unsupported PanCAD element type: {geometry}")

@_freecad_add_to_sketch.register
def _ellipse(self,
             ellipse: FreeCADEllipse,
             sketch: Sketcher.Sketch,
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
                      geometry: FreeCADLineSegment | FreeCADCircle,
                      sketch: Sketcher.Sketch,
                      construction: bool) -> SketchElementID:
    index = len(sketch.Geometry)
    sketch.addGeometry(geometry, construction)
    geometry_id = (sketch.ID, ListName.GEOMETRY, index)
    self._id_map[geometry_id] = geometry
    return geometry_id