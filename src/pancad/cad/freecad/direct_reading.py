"""A module providing functions for reading FreeCAD xml directly."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any
from uuid import UUID
from xml.etree import ElementTree as ET
from zipfile import ZipFile

# TEMP #
from pprint import pp
# TEMP #

if TYPE_CHECKING:
    from pathlib import Path
    from xml.etree.ElementTree import Element

from .constants import SubFile, XMLTag, XMLAttr, XMLPropertyType

logger = logging.getLogger(__name__)

def _read_bool(element: Element) -> bool:
    if len(element) != 1: raise ValueError(f"Found {len(element)}")
    return element.find(XMLTag.BOOL).attrib[XMLAttr.VALUE] == "true"

def _read_string(element: Element) -> str:
    if len(element) != 1: raise ValueError(f"Found {len(element)}")
    return element.find(XMLTag.STRING).attrib[XMLAttr.VALUE]

def _read_uuid(element: Element) -> UUID:
    if len(element) != 1: raise ValueError(f"Found {len(element)}")
    return element.find(XMLTag.UUID).attrib[XMLAttr.VALUE]

def _read_enum(element: Element) -> str | int:
    """Returns the enumeration string value if custom, otherwise the selection 
    integer.
    """
    selection = int(element.find(XMLTag.INTEGER).attrib[XMLAttr.VALUE])
    if (enum_list := element.find(XMLTag.CUSTOM_ENUM_LIST)) is not None:
        return enum_list[selection].attrib[XMLAttr.VALUE]
    else:
        return selection

def _read_map(element: Element) -> list:
    raise NotImplementedError("Not implemented yet")

class Document:
    """A class representing a FreeCAD document, read without the FreeCAD API."""
    
    PROPERTY_DISPATCH = {
        XMLPropertyType.APP_STRING: _read_string,
        XMLPropertyType.APP_BOOL: _read_bool,
        XMLPropertyType.APP_ENUM: _read_enum,
        XMLPropertyType.APP_UUID: _read_uuid,
    }
    
    def __init__(self, filepath: str | Path) -> None:
        self.archive = ZipFile(filepath)
        self.members = {m.filename: m for m in self.archive.infolist()}
        with self.archive.open(self.members[SubFile.DOCUMENT_XML]) as file:
            self.tree = ET.fromstring(file.read())
        
        properties_element = self.tree.find(XMLTag.PROPERTIES)
        self.properties = self._read_properties(properties_element,
                                                XMLTag.PROPERTY)
        # pp(self.properties)
        
        objects = []
        objects_element = self.tree.find(XMLTag.OBJECTS)
        for object_ in objects_element.iter(XMLTag.OBJECT):
            name = object_.get(XMLAttr.NAME)
            type_ = object_.get(XMLAttr.TYPE)
            id_ = int(object_.get(XMLAttr.ID))
            objects.append((name, type_, id_))
        
        dependencies = []
        for object_ in objects_element.iter(XMLTag.OBJECT_DEPENDENCIES):
            name = object_.get(XMLAttr.CAPITALIZED_NAME)
            depends_on = [dep.get(XMLAttr.CAPITALIZED_NAME)
                          for dep in object_.iter(XMLTag.DEP)]
            dependencies.append((name, depends_on))
        
        object_data_element = self.tree.find(XMLTag.OBJECT_DATA)
        object_data = []
        for object_ in object_data_element.iter(XMLTag.OBJECT):
            object_data.append((object_.get(XMLAttr.NAME), object_))
        pp(object_data)
        self.objects = {}
        for name, type_, id_ in objects:
            object_dict = {XMLAttr.NAME: name, XMLAttr.TYPE: type_}
            for dependency_name, list_ in dependencies:
                if name == dependency_name:
                    object_dict[XMLTag.OBJECT_DEPENDENCIES] = list_
                    break
            for object_data_name, element in object_data:
                if name == object_data_name:
                    object_dict[XMLTag.OBJECT_DATA] = element
            self.objects[id_] = object_dict
        pp(self.objects)
    
    def _read_properties(self,
                         element: Element,
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
            
            if type_ in self.PROPERTY_DISPATCH:
                value = self.PROPERTY_DISPATCH[type_](property_)
            else:
                # print(f"Skipped {name}, unsupported type {type_}")
                logger.warning(f"Skipped {name}, unsupported type {type_}")
                value = None
            properties.append((name, type_, status, value))
        return properties





# def read_property(element: ET.Element):
    # match element.get(