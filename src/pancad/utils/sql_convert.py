"""A module for reading and writing pancad objects from/to a sqlite database. 
Simply importing this module registers the converters to sqlite3.
"""
import sqlite3
import tomllib
from pathlib import Path

from pancad import config, geometry

def _point(value: bytes) -> geometry.Point:
    return geometry.Point(*map(float, value.split(b";")))

def _circle(value: bytes) -> geometry.Circle:
    if len(dimensions := value.split(b";")) == 3:
        *center, radius = dimensions
        x_vector = None
        y_vector = None
    else:
        raise NotImplementedError("3D Circles not implemented yet")
    center = tuple(map(float, center))
    radius = float(radius)
    return geometry.Circle(center, radius)

def _line(value: bytes) -> geometry.Line:
    if len(dimensions := value.split(b";")) == 4:
        closest_x, closest_y, *direction = dimensions
        closest = [closest_x, closest_y]
    elif len(dimensions) == 6:
        closest_x, closest_y, closest_z, *direction = dimensions
        closest = [closest_x, closest_y, closest_z]
    else:
        raise ValueError(f"Invalid Line parameter count ({len(dimensions)})!")
    closest = tuple(map(float, closest))
    direction = tuple(map(float, direction))
    return geometry.Line(geometry.Point(closest), direction)

with open(Path(config.__file__).parent / "sqlite.toml", "rb") as file:
    conform_type = tomllib.load(file)["conform_type"]

converters = {
    "Point": _point,
    "Circle": _circle,
    "Line": _line,
}
for type_, converter in converters.items():
    sqlite3.register_converter(conform_type[type_], converter)