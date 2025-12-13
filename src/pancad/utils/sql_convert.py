"""A module for reading and writing pancad objects from/to a sqlite database."""
import sqlite3
import tomllib
from pathlib import Path

from pancad import config, geometry

def _point(value: str) -> geometry.Point:
    return geometry.Point(*map(float, value.split(b";")))

with open(Path(config.__file__).parent / "sqlite.toml", "rb") as file:
    conform_type = tomllib.load(file)["conform_type"]

converters = [
    (conform_type["Point"], _point),
]
for type_, converter in converters:
    print(f"{type_} registered!")
    sqlite3.register_converter(type_, converter)