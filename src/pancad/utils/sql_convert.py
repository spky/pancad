"""A module for reading and writing pancad objects from/to a sqlite database.
Importing this module registers the converters to sqlite3.
"""
import sqlite3
import tomllib
from pathlib import Path

from pancad import resources
from pancad.geometry.point import Point
from pancad.geometry.line import Line
from pancad.geometry.line_segment import LineSegment
from pancad.geometry.circle import Circle
from pancad.geometry.circular_arc import CircularArc
from pancad.geometry.coordinate_system import CoordinateSystem
from pancad.geometry.ellipse import Ellipse
from pancad.geometry.plane import Plane

def _point(value: bytes) -> Point:
    return Point(*map(float, value.split(b";")))

def _circle(value: bytes) -> Circle:
    param_count_2d = 3
    if len(dimensions := value.split(b";")) != param_count_2d:
        raise NotImplementedError("3D Circles not implemented yet")
    *center, radius = dimensions
    center = tuple(map(float, center))
    radius = float(radius)
    return Circle(center, radius)

def _line(value: bytes) -> Line:
    param_count_2d = 4
    param_count_3d = 6
    if len(dimensions := value.split(b";")) == param_count_2d:
        closest_x, closest_y, *direction = dimensions
        closest = [closest_x, closest_y]
    elif len(dimensions) == param_count_3d:
        closest_x, closest_y, closest_z, *direction = dimensions
        closest = [closest_x, closest_y, closest_z]
    else:
        class_ = Line.__name__
        raise ValueError(f"Wrong {class_} param count ({len(dimensions)})!")
    closest = tuple(map(float, closest))
    direction = tuple(map(float, direction))
    return Line(Point(closest), direction)

def _line_segment(value: bytes) -> LineSegment:
    param_count_2d = 4
    param_count_3d = 6
    if len(dimensions := value.split(b";")) == param_count_2d:
        a_x, a_y, *b = dimensions
        a = [a_x, a_y]
    elif len(dimensions) == param_count_3d:
        a_x, a_y, a_z, *b = dimensions
        a = [a_x, a_y, a_z]
    else:
        class_ = Line.__name__
        raise ValueError(f"Wrong {class_} param count ({len(dimensions)})!")
    a = tuple(map(float, a))
    b = tuple(map(float, b))
    return LineSegment(a, b)

def _circular_arc(value: bytes) -> CircularArc:
    param_count_2d = 5
    param_count_3d = 6
    if len(dimensions := value.split(b"|")) == param_count_2d:
        *vectors, is_clockwise, radius = dimensions
        float_vectors = [list(map(float, v.split(b";"))) for v in vectors]
        try:
            center, start, end = float_vectors
        except ValueError as exc:
            exc.add_note("Unexpected number of vectors in circular arc"
                         f" sql value: {value}")
            raise
        normal = None
    elif len(dimensions) == param_count_3d:
        raise NotImplementedError("3D CircularArcs not implemented yet")
    else:
        class_ = CircularArc.__name__
        raise ValueError(f"Wrong {class_} param count ({len(dimensions)})!")
    is_clockwise = bool(int(is_clockwise))
    radius = float(radius)
    return CircularArc(center, radius, start, end, is_clockwise, normal)

def _ellipse(value: bytes) -> Ellipse:
    raise NotImplementedError

def _coordinate_system(value: bytes) -> CoordinateSystem:
    raise NotImplementedError

def _plane(value: bytes) -> Plane:
    raise NotImplementedError


with open(Path(resources.__file__).parent / "pancad.toml", "rb") as file:
    conform_type = tomllib.load(file)["sqlite"]["conform_type"]

converters = {
    "Point": _point,
    "Circle": _circle,
    "Line": _line,
    "LineSegment": _line_segment,
    "CircularArc": _circular_arc,
    "Ellipse": _ellipse,
    "CoordinateSystem": _coordinate_system,
    "Plane": _plane,
}
for type_, converter in converters.items():
    sqlite3.register_converter(conform_type[type_], converter)
