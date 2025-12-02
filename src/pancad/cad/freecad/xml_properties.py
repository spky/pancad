"""A module providing functions for reading and writing FreeCAD xml 
properties from/to its save files.
"""
from __future__ import annotations
from functools import partial

from collections import namedtuple
import logging
from typing import TYPE_CHECKING, Any
from uuid import UUID
from datetime import datetime
from xml.etree import ElementTree as ET

import numpy as np

from .constants.archive_constants import (
    Tag, Attr, PropertyType, App, Sketcher, Part
)
from .xml_geometry import GEOMETRY_DISPATCH

if TYPE_CHECKING:
    from xml.etree.ElementTree import Element

logger = logging.getLogger(__name__)

ARGB = namedtuple("ARGB", ["a", "r", "g", "b"])


def unpack_argb(packed: int) -> ARGB:
    """Returns a tuple of ARGB values from an integer."""
    return ARGB(*[(packed >> shift_by) & 0xFF for shift_by in [24, 16, 8, 0]])

def _read_bad_type(element: Element) -> list[tuple[bool, int, float]]:
    layer_list = element.find(Tag.VISUAL_LAYER_LIST)
    if layer_list.tag != Tag.VISUAL_LAYER_LIST:
        raise ValueError(f"Unexpected tag: {element.tag}")
    layers = []
    for list_ in layer_list.iter(Tag.VISUAL_LAYER):
        visible = list_.attrib[Attr.VISIBLE] == "true"
        line_pattern = int(list_.attrib[Attr.LINE_PATTERN])
        line_width = float(list_.attrib[Attr.LINE_WIDTH])
        layers.append((visible, line_pattern, line_width))
    return layers
    

def _read_bool(element: Element) -> bool:
    if len(element) != 1: raise ValueError(f"Found {len(element)}")
    return element.find(Tag.BOOL).attrib[Attr.VALUE] == "true"

def _read_color(element: Element) -> tuple[int, int, int, int]:
    """Returns the ARGB values from the integer in the element as a tuple."""
    if len(element) != 1: raise ValueError(f"Found {len(element)}")
    ARGB = namedtuple("ARGB", ["a", "r", "g", "b"])
    integer = int(element.find(Tag.PROPERTY_COLOR).attrib[Attr.VALUE])
    return unpack_argb(integer)

def _read_constraint_list(element: Element) -> list[dict]:
    if len(element) != 1: raise ValueError(f"Found {len(element)}")
    TYPE_DICT = {
        int: [
            "First",
            "FirstPos",
            "Second",
            "SecondPos",
            "Third",
            "ThirdPos"
            "Type",
        ],
        float: ["Value", "LabelDistance", "LabelPosition"],
        lambda v: bool(int(v)): ["IsDriving", "IsInVirtualSpace", "IsActive"],
        str: ["Name"],
    }
    type_dispatch = {}
    for func, names in TYPE_DICT.items():
        type_dispatch.update({name: func for name in names})
    
    constraints = []
    for constraint in element.find(Tag.CONSTRAINT_LIST):
        attributes = {}
        for name, value in dict(constraint.attrib).items():
            if name in type_dispatch:
                attributes[name] = type_dispatch[name](value)
            else:
                attributes[name] = value
        constraints.append(attributes)
    return constraints

def _read_enum(element: Element) -> str | int:
    """Returns the custom enumeration string or the selection integer."""
    selection = int(element.find(Tag.INTEGER).attrib[Attr.VALUE])
    if (enum_list := element.find(Tag.CUSTOM_ENUM_LIST)) is not None:
        return enum_list[selection].attrib[Attr.VALUE]
    else:
        return selection

def _read_float(element: Element) -> float:
    if len(element) != 1: raise ValueError(f"Found {len(element)}")
    return float(element.find(Tag.FLOAT).attrib[Attr.VALUE])

def _read_geometry_list(element: Element) -> dict[int, dict]:
    geometries = {}
    for geometry in element.find(Tag.GEOMETRY_LIST):
        id_ = geometry.get(Attr.ID)
        extensions = []
        for extension in geometry.find(Tag.GEOMETRY_EXTENSIONS):
            extensions.append(dict(extension.attrib))
        
        construction = geometry.find(Tag.CONSTRUCTION)
        is_construction = bool(int(construction.attrib[Attr.VALUE]))
        
        migrated = geometry.attrib[Attr.MIGRATED]
        type_ = geometry.attrib[Attr.TYPE]
        if type_ in GEOMETRY_DISPATCH:
                data = GEOMETRY_DISPATCH[type_](geometry)
        else:
            logger.warning(f"Skipped {id_}, unsupported geo type {type_}")
            data = None
        geometries[id_] = {
            Tag.GEOMETRY_EXTENSIONS: extensions,
            Tag.CONSTRUCTION: is_construction,
            Attr.MIGRATED: is_construction,
            Attr.TYPE: type_,
            Tag.GEOMETRY: data,
        }
    return geometries

def _read_integer(element: Element) -> int:
    if len(element) != 1: raise ValueError(f"Found {len(element)}")
    return int(element.find(Tag.INTEGER).attrib[Attr.VALUE])

def _read_link_sublist(element: Element) -> list[tuple[str, str]]:
    """Returns the name and sub in each link in the link sublist"""
    if len(element) != 1: raise ValueError(f"Found {len(element)}")
    links = []
    for link in element.find(Tag.LINK_SUB_LIST):
        links.append((link.get(Attr.OBJECT), link.get(Attr.LINK_SUB)))
    return links

def _read_link_list(element: Element) -> list:
    """Returns each link in the link list"""
    if len(element) != 1: raise ValueError(f"Found {len(element)}")
    links = []
    for link in element.find(Tag.LINK_LIST):
        links.append(link)
    return links

def _read_map(element: Element) -> list:
    raise NotImplementedError("Map not implemented yet")

def _read_material(element: Element) -> dict[str, ARGB | float | str | UUID]:
    FUNC_DISPATCH = {
        lambda value: unpack_argb(int(value)): [
            "ambientColor", "diffuseColor", "specularColor", "emissiveColor",
        ],
        float: ["shininess", "transparency"],
        lambda value: UUID if value else "": ["uuid",]
    }
    dispatch = {}
    for func, fields in FUNC_DISPATCH.items():
        dispatch.update({field: func for field in fields})
    material_element = element.find(Tag.PROPERTY_MATERIAL)
    material = {}
    for field, value in dict(material_element.attrib).items():
        if field in dispatch:
            material[field] = dispatch[field](value)
        else:
            material[field] = value
    return material

def _read_material_list(element: Element) -> dict[str, str]:
    list_element = element.find(Tag.MATERIAL_LIST)
    return dict(list_element.attrib)

def _read_expression_engine(element: Element) -> list:
    raise NotImplementedError("Expression Engine not implemented yet")

def _read_placement(element: Element) -> tuple[tuple[float], np.quaternion]:
    """Returns the position vector and quaternion."""
    if len(element) != 1: raise ValueError(f"Found {len(element)}")
    POSITION_ATTR = [Attr.POSITION_X, Attr.POSITION_Y, Attr.POSITION_Z]
    QUAT_ATTR = [Attr.QUAT_3, Attr.QUAT_0, Attr.QUAT_1, Attr.QUAT_2]
    
    placement = element.find(Tag.PROPERTY_PLACEMENT)
    position = [float(placement.get(a)) for a in POSITION_ATTR]
    quat_params = [float(placement.get(a)) for a in QUAT_ATTR]
    
    return tuple(position), np.quaternion(*quat_params)

def _read_python_object(element: Element) -> dict[str, str]:
    if len(element) != 1: raise ValueError(f"Found {len(element)}")
    return dict(element.find(Tag.PYTHON).attrib)

def _read_nested_string(element: Element, tag: Tag, field: Attr) -> str:
    """Used to read nested strings that aren't necessarily in a String tag."""
    if len(element) != 1: raise ValueError(f"Found {len(element)}")
    return element.find(tag).attrib[field]

_read_string = partial(_read_nested_string,
                       tag=Tag.STRING, field=Attr.VALUE)
_read_color_list = partial(_read_nested_string,
                           tag=Tag.COLOR_LIST, field=Attr.FILE)

def _read_uuid(element: Element) -> UUID | None:
    if len(element) != 1: raise ValueError(f"Found {len(element)}")
    return UUID(element.find(Tag.UUID).attrib[Attr.VALUE])

def _read_vector(element: Element) -> tuple[float, float, float]:
    if len(element) != 1: raise ValueError(f"Found {len(element)}")
    XYZ_FIELDS = ["valueX", "valueY", "valueZ"]
    vector = element.find(Tag.PROPERTY_VECTOR)
    return tuple(float(vector.attrib[component]) for component in XYZ_FIELDS)

PROPERTY_DISPATCH = {
        App.ANGLE: _read_float,
        App.BOOL: _read_bool,
        App.COLOR: _read_color,
        App.COLOR_LIST: _read_color_list,
        App.ENUM: _read_enum,
        App.FLOAT: _read_float,
        App.FLOAT_CONSTRAINT: _read_float,
        App.LENGTH: _read_float,
        App.LINK_SUBLIST: _read_link_sublist,
        App.LINK_LIST_HIDDEN: _read_link_list,
        App.MATERIAL: _read_material,
        App.MATERIAL_LIST: _read_material_list,
        App.PLACEMENT: _read_placement,
        App.PYTHON_OBJECT: _read_python_object,
        App.PERCENT: _read_integer,
        App.PRECISION: _read_float,
        App.VECTOR: _read_vector,
        App.STRING: _read_string,
        App.UUID: _read_uuid,
        
        PropertyType.BAD_TYPE: _read_bad_type,
        
        Part.GEOMETRY_LIST: _read_geometry_list,
        
        Sketcher.CONSTRAINT_LIST: _read_constraint_list,
}

def read_sketch_geometry_common(object_: Element) -> tuple[tuple[str], list[tuple[Any]]]:
    """Returns a list of data common to all geometry tuples for each sketch 
    geometry element in the properties list element.
    """
    
    list_names = ["ExternalGeo", "Geometry"]
    lists = []
    for property_ in properties.iter(Tag.PROPERTY):
        if (name := property_.get(Attr.NAME)) in list_names:
            lists.append((name, property_))
    
    if not lists:
        return None
    
    geometry = []
    for list_name, property_element in lists:
        list_element = property_element.find(Tag.GEOMETRY_LIST)
        for list_index, element in enumerate(list_element):
            type_ = element.get(Attr.TYPE)
            id_ = int(element.get(Attr.ID))
            construction = bool(
                int(element.find(Tag.CONSTRUCTION).get(Attr.VALUE))
            )
            migrated = bool(int(element.get(Attr.MIGRATED)))
            geometry.append(
                (list_name, list_index, id_, type_, construction, migrated)
            )
    return geometry

def read_properties(element: Element) -> list[tuple[str, str, int, Any]]:
    """Reads the property formatted tags under the element.
    
    :param element: The Properties element with elements underneath.
    :returns: A list of (Name, Type, Status, Value) tuples.
    """
    return [read_property(prop) for prop in element.iter(Tag.PROPERTY)]

def read_property(element: Element) -> tuple[str, int, Any]:
    """Reads the name, type, status and value of a Property element"""
    name = element.get(Attr.NAME)
    type_ = element.get(Attr.TYPE)
    if (status := element.get(Attr.STATUS)) is not None: 
        status = int(status)
    
    if type_ in PROPERTY_DISPATCH:
        value = PROPERTY_DISPATCH[type_](element)
    else:
        logger.warning(f"Skipped {name}, unsupported type {type_}")
        value = None
    return (name, type_, status, value)