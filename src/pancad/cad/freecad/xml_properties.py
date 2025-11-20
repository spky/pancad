"""A module providing functions for reading and writing FreeCAD xml 
properties from/to its save files.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any
from xml.etree import ElementTree as ET

import numpy as np

from .constants import XMLTag, XMLAttr, XMLPropertyType
from .xml_geometry import GEOMETRY_DISPATCH

if TYPE_CHECKING:
    from xml.etree.ElementTree import Element

logger = logging.getLogger(__name__)

def _read_bool(element: Element) -> bool:
    if len(element) != 1: raise ValueError(f"Found {len(element)}")
    return element.find(XMLTag.BOOL).attrib[XMLAttr.VALUE] == "true"

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

def _read_string(element: Element) -> str:
    if len(element) != 1: raise ValueError(f"Found {len(element)}")
    return element.find(XMLTag.STRING).attrib[XMLAttr.VALUE]

def _read_uuid(element: Element) -> UUID:
    if len(element) != 1: raise ValueError(f"Found {len(element)}")
    return element.find(XMLTag.UUID).attrib[XMLAttr.VALUE]

PROPERTY_DISPATCH = {
        XMLPropertyType.APP_BOOL: _read_bool,
        XMLPropertyType.APP_ENUM: _read_enum,
        XMLPropertyType.APP_FLOAT: _read_float,
        XMLPropertyType.APP_LINK_SUBLIST: _read_link_sublist,
        XMLPropertyType.APP_LINK_LIST_HIDDEN: _read_link_list,
        XMLPropertyType.APP_PLACEMENT: _read_placement,
        XMLPropertyType.APP_PRECISION: _read_float,
        XMLPropertyType.APP_STRING: _read_string,
        XMLPropertyType.APP_UUID: _read_uuid,
        
        XMLPropertyType.PART_GEOMETRY_LIST: _read_geometry_list,
        
        XMLPropertyType.SKETCHER_CONSTRAINT_LIST: _read_constraint_list,
}

def read_properties(element: Element,
                    tag: XMLTag) -> list[tuple[str, str, int, Any]]:
    """Reads the property formatted tags under the element.
    
    :param element: The Properties element with elements underneath.
    :param tag: The subelement tag to search for.
    :returns: A list of (Name, Type, Status, Value) tuples.
    """
    properties = []
    for property_ in element.iter(tag):
        name = property_.get(XMLAttr.NAME)
        type_ = property_.get(XMLAttr.TYPE)
        if (status := property_.get(XMLAttr.STATUS)) is not None: 
            status = int(status)
        
        if type_ in PROPERTY_DISPATCH:
            value = PROPERTY_DISPATCH[type_](property_)
        else:
            # print(f"Skipped {name}, unsupported type {type_}")
            logger.warning(f"Skipped {name}, unsupported type {type_}")
            value = None
        properties.append((name, type_, status, value))
    return properties

def read_private_properties(element: Element,
                            tag: XMLTag) -> list[tuple[str, str, int]]:
    """Reads the _Property like formatted tags under the element.
    
    :param element: The Properties element with elements underneath.
    :param tag: The subelement tag to search for.
    :returns: A list of (Name, Type, Status) tuples.
    """
    properties = []
    for property_ in element.iter(tag):
        name = property_.get(XMLAttr.NAME)
        type_ = property_.get(XMLAttr.TYPE)
        if (status := property_.get(XMLAttr.STATUS)) is not None: 
            status = int(status)
        properties.append((name, type_, status))
    return properties