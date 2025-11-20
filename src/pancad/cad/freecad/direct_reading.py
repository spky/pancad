"""A module providing functions for reading FreeCAD xml directly."""
from __future__ import annotations

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

from .xml_properties import read_properties, read_private_properties
from .constants import SubFile, XMLTag, XMLAttr

class Document:
    """A class representing a FreeCAD document, read without the FreeCAD API."""
    
    def __init__(self, filepath: str | Path) -> None:
        self.archive = ZipFile(filepath)
        self.members = {m.filename: m for m in self.archive.infolist()}
        with self.archive.open(self.members[SubFile.DOCUMENT_XML]) as file:
            self.tree = ET.fromstring(file.read())
        
        properties_element = self.tree.find(XMLTag.PROPERTIES)
        self.properties = read_properties(properties_element, XMLTag.PROPERTY)
        self.private = read_private_properties(properties_element,
                                               XMLTag.PRIVATE_PROPERTY)
        self.document_schema_version = self.tree.get(XMLAttr.SCHEMA_VERSION)
        self.program_version = self.tree.get(XMLAttr.PROGRAM_VERSION)
        self.file_version = self.tree.get(XMLAttr.FILE_VERSION)
        self.string_hasher = self.tree.get(XMLAttr.STRING_HASHER)
        
        objects = []
        objects_element = self.tree.find(XMLTag.OBJECTS)
        for object_ in objects_element.iter(XMLTag.OBJECT):
            name = object_.get(XMLAttr.NAME)
            type_ = object_.get(XMLAttr.TYPE)
            id_ = int(object_.get(XMLAttr.ID))
            objects.append((name, type_, id_))
        
        dependencies = []
        for object_ in objects_element.iter(XMLTag.OBJECT_DEPENDENCIES):
            name = object_.get(XMLAttr.NAME_CAPITALIZED)
            depends_on = [dep.get(XMLAttr.NAME_CAPITALIZED)
                          for dep in object_.iter(XMLTag.DEP)]
            dependencies.append((name, depends_on))
        
        object_data_element = self.tree.find(XMLTag.OBJECT_DATA)
        object_data = []
        for object_ in object_data_element.iter(XMLTag.OBJECT):
            object_data.append((object_.get(XMLAttr.NAME), object_))
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
        
        with self.archive.open(self.members[SubFile.GUI_DOCUMENT_XML]) as file:
            self.gui_tree = ET.fromstring(file.read())