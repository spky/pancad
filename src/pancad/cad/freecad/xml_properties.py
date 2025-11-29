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

from .constants import XMLTag, XMLAttr, XMLPropertyType
from .xml_geometry import GEOMETRY_DISPATCH

if TYPE_CHECKING:
    from xml.etree.ElementTree import Element

logger = logging.getLogger(__name__)

ARGB = namedtuple("ARGB", ["a", "r", "g", "b"])

def unpack_argb(packed: int) -> ARGB:
    """Returns a tuple of ARGB values from an integer."""
    return ARGB(*[(packed >> shift_by) & 0xFF for shift_by in [24, 16, 8, 0]])

def _read_bad_type(element: Element) -> list[tuple[bool, int, float]]:
    layer_list = element.find(XMLTag.VISUAL_LAYER_LIST)
    if layer_list.tag != XMLTag.VISUAL_LAYER_LIST:
        raise ValueError(f"Unexpected tag: {element.tag}")
    layers = []
    for list_ in layer_list.iter(XMLTag.VISUAL_LAYER):
        visible = list_.attrib[XMLAttr.VISIBLE] == "true"
        line_pattern = int(list_.attrib[XMLAttr.LINE_PATTERN])
        line_width = float(list_.attrib[XMLAttr.LINE_WIDTH])
        layers.append((visible, line_pattern, line_width))
    return layers
    

def _read_bool(element: Element) -> bool:
    if len(element) != 1: raise ValueError(f"Found {len(element)}")
    return element.find(XMLTag.BOOL).attrib[XMLAttr.VALUE] == "true"

def _read_color(element: Element) -> tuple[int, int, int, int]:
    """Returns the ARGB values from the integer in the element as a tuple."""
    if len(element) != 1: raise ValueError(f"Found {len(element)}")
    ARGB = namedtuple("ARGB", ["a", "r", "g", "b"])
    integer = int(element.find(XMLTag.PROPERTY_COLOR).attrib[XMLAttr.VALUE])
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
    for constraint in element.find(XMLTag.CONSTRAINT_LIST):
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
    selection = int(element.find(XMLTag.INTEGER).attrib[XMLAttr.VALUE])
    if (enum_list := element.find(XMLTag.CUSTOM_ENUM_LIST)) is not None:
        return enum_list[selection].attrib[XMLAttr.VALUE]
    else:
        return selection

def _read_float(element: Element) -> float:
    if len(element) != 1: raise ValueError(f"Found {len(element)}")
    return float(element.find(XMLTag.FLOAT).attrib[XMLAttr.VALUE])

def _read_geometry_list(element: Element) -> dict[int, dict]:
    geometries = {}
    for geometry in element.find(XMLTag.GEOMETRY_LIST):
        id_ = geometry.get(XMLAttr.ID)
        extensions = []
        for extension in geometry.find(XMLTag.GEOMETRY_EXTENSIONS):
            extensions.append(dict(extension.attrib))
        
        construction = geometry.find(XMLTag.CONSTRUCTION)
        is_construction = bool(int(construction.attrib[XMLAttr.VALUE]))
        
        migrated = geometry.attrib[XMLAttr.MIGRATED]
        type_ = geometry.attrib[XMLAttr.TYPE]
        if type_ in GEOMETRY_DISPATCH:
                data = GEOMETRY_DISPATCH[type_](geometry)
        else:
            logger.warning(f"Skipped {id_}, unsupported geo type {type_}")
            data = None
        geometries[id_] = {
            XMLTag.GEOMETRY_EXTENSIONS: extensions,
            XMLTag.CONSTRUCTION: is_construction,
            XMLAttr.MIGRATED: is_construction,
            XMLAttr.TYPE: type_,
            XMLTag.GEOMETRY: data,
        }
    return geometries

def _read_integer(element: Element) -> int:
    if len(element) != 1: raise ValueError(f"Found {len(element)}")
    return int(element.find(XMLTag.INTEGER).attrib[XMLAttr.VALUE])

def _read_link_sublist(element: Element) -> list[tuple[str, str]]:
    """Returns the name and sub in each link in the link sublist"""
    if len(element) != 1: raise ValueError(f"Found {len(element)}")
    links = []
    for link in element.find(XMLTag.LINK_SUB_LIST):
        links.append((link.get(XMLAttr.OBJECT), link.get(XMLAttr.LINK_SUB)))
    return links

def _read_link_list(element: Element) -> list:
    """Returns each link in the link list"""
    if len(element) != 1: raise ValueError(f"Found {len(element)}")
    links = []
    for link in element.find(XMLTag.LINK_LIST):
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
    material_element = element.find(XMLTag.PROPERTY_MATERIAL)
    material = {}
    for field, value in dict(material_element.attrib).items():
        if field in dispatch:
            material[field] = dispatch[field](value)
        else:
            material[field] = value
    return material

def _read_material_list(element: Element) -> dict[str, str]:
    list_element = element.find(XMLTag.MATERIAL_LIST)
    return dict(list_element.attrib)

def _read_expression_engine(element: Element) -> list:
    raise NotImplementedError("Expression Engine not implemented yet")

def _read_placement(element: Element) -> tuple[tuple[float], np.quaternion]:
    """Returns the position vector and quaternion."""
    if len(element) != 1: raise ValueError(f"Found {len(element)}")
    POSITION_ATTR = [XMLAttr.POSITION_X, XMLAttr.POSITION_Y, XMLAttr.POSITION_Z]
    QUAT_ATTR = [XMLAttr.QUAT_3, XMLAttr.QUAT_0, XMLAttr.QUAT_1, XMLAttr.QUAT_2]
    
    placement = element.find(XMLTag.PROPERTY_PLACEMENT)
    position = [float(placement.get(a)) for a in POSITION_ATTR]
    quat_params = [float(placement.get(a)) for a in QUAT_ATTR]
    
    return tuple(position), np.quaternion(*quat_params)

def _read_python_object(element: Element) -> dict[str, str]:
    if len(element) != 1: raise ValueError(f"Found {len(element)}")
    return dict(element.find(XMLTag.PYTHON).attrib)

def _read_nested_string(element: Element, tag: XMLTag, field: XMLAttr) -> str:
    """Used to read nested strings that aren't necessarily in a String tag."""
    if len(element) != 1: raise ValueError(f"Found {len(element)}")
    return element.find(tag).attrib[field]

_read_string = partial(_read_nested_string,
                       tag=XMLTag.STRING, field=XMLAttr.VALUE)
_read_color_list = partial(_read_nested_string,
                           tag=XMLTag.COLOR_LIST, field=XMLAttr.FILE)

def _read_uuid(element: Element) -> UUID | None:
    if len(element) != 1: raise ValueError(f"Found {len(element)}")
    return UUID(element.find(XMLTag.UUID).attrib[XMLAttr.VALUE])

def _read_vector(element: Element) -> tuple[float, float, float]:
    if len(element) != 1: raise ValueError(f"Found {len(element)}")
    XYZ_FIELDS = ["valueX", "valueY", "valueZ"]
    vector = element.find(XMLTag.PROPERTY_VECTOR)
    return tuple(float(vector.attrib[component]) for component in XYZ_FIELDS)

PROPERTY_DISPATCH = {
        XMLPropertyType.APP_ANGLE: _read_float,
        XMLPropertyType.APP_BOOL: _read_bool,
        XMLPropertyType.APP_COLOR: _read_color,
        XMLPropertyType.APP_COLOR_LIST: _read_color_list,
        XMLPropertyType.APP_ENUM: _read_enum,
        XMLPropertyType.APP_FLOAT: _read_float,
        XMLPropertyType.APP_FLOAT_CONSTRAINT: _read_float,
        XMLPropertyType.APP_LENGTH: _read_float,
        XMLPropertyType.APP_LINK_SUBLIST: _read_link_sublist,
        XMLPropertyType.APP_LINK_LIST_HIDDEN: _read_link_list,
        XMLPropertyType.APP_MATERIAL: _read_material,
        XMLPropertyType.APP_MATERIAL_LIST: _read_material_list,
        XMLPropertyType.APP_PLACEMENT: _read_placement,
        XMLPropertyType.APP_PYTHON_OBJECT: _read_python_object,
        XMLPropertyType.APP_PERCENT: _read_integer,
        XMLPropertyType.APP_PRECISION: _read_float,
        XMLPropertyType.APP_VECTOR: _read_vector,
        XMLPropertyType.APP_STRING: _read_string,
        XMLPropertyType.APP_UUID: _read_uuid,
        
        XMLPropertyType.BAD_TYPE: _read_bad_type,
        
        XMLPropertyType.PART_GEOMETRY_LIST: _read_geometry_list,
        
        XMLPropertyType.SKETCHER_CONSTRAINT_LIST: _read_constraint_list,
}

def read_properties(element: Element) -> list[tuple[str, str, int, Any]]:
    """Reads the property formatted tags under the element.
    
    :param element: The Properties element with elements underneath.
    :returns: A list of (Name, Type, Status, Value) tuples.
    """
    return [read_property(prop) for prop in element.iter(XMLTag.PROPERTY)]

def read_property(element: Element) -> tuple[str, int, Any]:
    """Reads the name, type, status and value of a Property element"""
    name = element.get(XMLAttr.NAME)
    type_ = element.get(XMLAttr.TYPE)
    if (status := element.get(XMLAttr.STATUS)) is not None: 
        status = int(status)
    
    if type_ in PROPERTY_DISPATCH:
        value = PROPERTY_DISPATCH[type_](element)
    else:
        logger.warning(f"Skipped {name}, unsupported type {type_}")
        value = None
    return (name, type_, status, value)