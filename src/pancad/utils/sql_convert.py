"""A module for reading and writing pancad objects from/to a sqlite database. 
Importing this module registers the converters to sqlite3.
"""
import sqlite3
import tomllib
from pathlib import Path

from pancad import resources, geometry

def _point(value: bytes) -> geometry.Point:
    return geometry.Point(*map(float, value.split(b";")))

def _circle(value: bytes) -> geometry.Circle:
    PARAM_COUNT_2D = 3
    if len(dimensions := value.split(b";")) == PARAM_COUNT_2D:
        *center, radius = dimensions
        x_vector = None
        y_vector = None
    else:
        raise NotImplementedError("3D Circles not implemented yet")
    center = tuple(map(float, center))
    radius = float(radius)
    return geometry.Circle(center, radius)

def _line(value: bytes) -> geometry.Line:
    PARAM_COUNT_2D = 4
    PARAM_COUNT_3D = 6
    if len(dimensions := value.split(b";")) == PARAM_COUNT_2D:
        closest_x, closest_y, *direction = dimensions
        closest = [closest_x, closest_y]
    elif len(dimensions) == PARAM_COUNT_3D:
        closest_x, closest_y, closest_z, *direction = dimensions
        closest = [closest_x, closest_y, closest_z]
    else:
        class_ = geometry.Line.__name__
        raise ValueError(f"Wrong {class_} param count ({len(dimensions)})!")
    closest = tuple(map(float, closest))
    direction = tuple(map(float, direction))
    return geometry.Line(geometry.Point(closest), direction)

def _line_segment(value: bytes) -> geometry.LineSegment:
    PARAM_COUNT_2D = 4
    PARAM_COUNT_3D = 6
    if len(dimensions := value.split(b";")) == PARAM_COUNT_2D:
        a_x, a_y, *b = dimensions
        a = [a_x, a_y]
    elif len(dimensions) == PARAM_COUNT_3D:
        a_x, a_y, a_z, *b = dimensions
        a = [a_x, a_y, a_z]
    else:
        class_ = geometry.Line.__name__
        raise ValueError(f"Wrong {class_} param count ({len(dimensions)})!")
    a = tuple(map(float, a))
    b = tuple(map(float, b))
    return geometry.LineSegment(a, b)

def _circular_arc(value: bytes) -> geometry.CircularArc:
    PARAM_COUNT_2D = 5
    PARAM_COUNT_3D = 6
    if len(dimensions := value.split(b"|")) == PARAM_COUNT_2D:
        *vectors, is_clockwise, radius = dimensions
        float_vectors = []
        for vector in vectors:
            float_vectors.append(list(map(float, vector.split(b";"))))
        center, start, end = float_vectors
        normal = None
    elif len(dimensions) == PARAM_COUNT_3D:
        raise NotImplementedError("3D CircularArcs not implemented yet")
    else:
        class_ = geometry.CircularArc.__name__
        raise ValueError(f"Wrong {class_} param count ({len(dimensions)})!")
    is_clockwise = bool(int(is_clockwise))
    radius = float(radius)
    return geometry.CircularArc(center, radius, start, end, is_clockwise, normal)

def _ellipse(value: bytes) -> geometry.Ellipse:
    raise NotImplementedError

def _coordinate_system(value: bytes) -> geometry.CoordinateSystem:
    raise NotImplementedError

def _plane(value: bytes) -> geometry.Plane:
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