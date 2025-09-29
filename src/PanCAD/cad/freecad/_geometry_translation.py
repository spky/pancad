from functools import singledispatchmethod

from PanCAD.cad.freecad import (
    App,
    Sketcher,
    Part,
    FreeCADCircle,
    FreeCADEllipse,
    FreeCADGeometry,
    FreeCADLineSegment,
)
from PanCAD.cad.freecad.constants import ListName
from PanCAD.geometry import (
    AbstractGeometry,
    Circle,
    LineSegment,
    Ellipse,
)
from ._map_typing import SketchElementID

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