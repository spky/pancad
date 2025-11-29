"""A module providing functions for reading and writing FreeCAD appearance 
files.
"""
from __future__ import annotations

from itertools import islice
from typing import TYPE_CHECKING
import struct


if TYPE_CHECKING:
    from zipfile import ZipFile, ZipInfo

def batched(iterable, n, *, strict=False):
    # batched('ABCDEFG', 2) → AB CD EF G
    if n < 1:
        raise ValueError('n must be at least one')
    iterator = iter(iterable)
    while batch := tuple(islice(iterator, n)):
        if strict and len(batch) != n:
            raise ValueError('batched(): incomplete batch')
        yield batch

def read_shape_appearance(archive: ZipFile,
                          filename: str | ZipInfo
                          ) -> dict[str, float | tuple[int]]:
    """Reads shape appearance file data.
    
    :param archive: A ZipFile of a FreeCAD file.
    :param filename: The name of the ShapeAppearance file to read.
    :returns: A dictionary of labels to either their float values or their RGBA 
        color integer tuples.
    """
    with archive.open(filename) as file:
        data = bytes(file.read())
    
    parsed = {}
    
    if len(data) > 40:
        parsed["uid"] = data[40:].decode()
        data = data[:40]
    
    LABELS = [
        "header",
        "ambient",
        "diffuse",
        "specular",
        "emissive",
        "shininess",
        "transparency",
        "blank0",
        "blank1",
        "uuid_sync",
    ]
    COLORS = ["ambient", "diffuse", "specular", "emissive"]
    FLOATS = ["shininess", "transparency"]
    for label, entry in zip(LABELS, batched(data, 4)):
        if label in COLORS:
            parsed[label] = entry[::-1]
        elif label in FLOATS:
            parsed[label] = struct.unpack("<f", bytes(entry))[0]
        elif label == "header":
            assert entry == (1, 0, 0, 0)
        elif label == "uuid_sync":
            assert entry == (0, 0, 0, 0) or entry == (36, 0, 0, 0)
        elif label.startswith("blank"):
            assert entry == (0, 0, 0, 0)
        else:
            raise ValueError(f"Unhandled label {label}")
    return parsed

def read_color_array(archive: ZipFile, filename: str | ZipInfo) -> tuple[int]:
    """Reads color array file data.
    
    :param archive: A ZipFile of a FreeCAD file.
    :param filename: The name of the Point or Line ColorArray file to read.
    :returns: A tuple of ARGB integer values.
    """
    with archive.open(filename) as file:
        data = bytes(file.read())
    
    header, color = list(batched(data, 4))
    assert header == (1, 0, 0, 0)
    return color

def read_string_hasher(archive: ZipFile, filename: str | ZipInfo):
    """Reads data from StringHasher files"""
    with archive.open(filename) as file:
        lines = [line.rstrip() for line in file]
    title, version, count = lines.pop(0).split()
    assert title.decode() == "StringTableStart"
