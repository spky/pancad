"""A module providing functions to generate PanCAD/FreeCAD sketch geometry from 
FreeCAD/PanCAD sketch geometry.
"""
from functools import singledispatch

from PanCAD.cad.freecad import App, Part
from PanCAD.geometry import AbstractGeometry, Circle, LineSegment, Ellipse

@singledispatch
def get_freecad_sketch_geometry(pancad: AbstractGeometry) -> object:
    raise TypeError(f"Unsupported PanCAD element type: {pancad}")

@singledispatch
def get_pancad_sketch_geometry(freecad: object) -> AbstractGeometry:
    raise TypeError(f"Unsupported PanCAD element type: {pancad}")

@get_freecad_sketch_geometry.register
def _line_segment(line_segment: LineSegment) -> Part.LineSegment:
    start = App.Vector(tuple(line_segment.point_a) + (0,))
    end = App.Vector(tuple(line_segment.point_b) + (0,))
    return Part.LineSegment(start, end)

@get_freecad_sketch_geometry.register
def _ellipse(ellipse: Ellipse) -> Part.Ellipse:
    major_axis_point = App.Vector(tuple(ellipse.get_major_axis_point()) + (0,))
    minor_axis_point = App.Vector(tuple(ellipse.get_minor_axis_point()) + (0,))
    center = App.Vector(tuple(ellipse.center) + (0,))
    return Part.Ellipse(major_axis_point, minor_axis_point, center)

@get_pancad_sketch_geometry.register
def _line_segment(line_segment: Part.LineSegment) -> LineSegment:
    start = tuple(line_segment.StartPoint)[0:2]
    end = tuple(line_segment.EndPoint)[0:2]
    return LineSegment(start, end)

@get_freecad_sketch_geometry.register
def _circle(circle: Circle) -> Part.Circle:
    center = App.Vector(tuple(circle.center) + (0,))
    normal = App.Vector((0, 0, 1))
    return Part.Circle(center, normal, circle.radius)

@get_pancad_sketch_geometry.register
def _circle(circle: Part.Circle) -> Circle:
    center = tuple(circle.Center)[0:2]
    return Circle(center, circle.Radius)