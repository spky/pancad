"""A module providing functions for reading FreeCAD xml directly."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any
from xml.etree import ElementTree as ET
from zipfile import ZipFile

# TEMP #
from pprint import pp
# TEMP #

if TYPE_CHECKING:
    from pathlib import Path
    from xml.etree.ElementTree import Element

from .xml_properties import read_properties
from .xml_appearance import read_shape_appearance
from .constants import SubFile, XMLTag, XMLAttr

def read_objects(objects: Element) -> list[tuple[str, str, int]]:
    """Reads the objects inside an Objects element
    
    :param element: The Objects element with Object elements underneath.
    :returns: A list of (Name, Type, ID) tuples for each object.
    """
    data = []
    for object_ in objects.iter(XMLTag.OBJECT):
        name = object_.get(XMLAttr.NAME)
        type_ = object_.get(XMLAttr.TYPE)
        id_ = int(object_.get(XMLAttr.ID))
        data.append((name, type_, id_))
    return data

def read_object_deps(objects: Element) -> list[tuple[str, list[str]]]:
    """Reads the dependency lists inside an Objects element.
    
    :param element: The Objects element with Object elements underneath.
    :returns: A list of (Name, list of dependency Names) tuples for each object.
    """
    data = []
    for object_ in objects.iter(XMLTag.OBJECT_DEPENDENCIES):
        name = object_.get(XMLAttr.NAME_CAPITALIZED)
        dep_iter = object_.iter(XMLTag.DEP)
        depends_on = [dep.get(XMLAttr.NAME_CAPITALIZED) for dep in dep_iter]
        data.append((name, depends_on))
    return data

def read_transient_properties(element: Element) -> list[tuple[str, str, int]]:
    """Reads the _Property like formatted tags under the element.
    
    :param element: The Properties element with elements underneath.
    :returns: A list of (Name, Type, Status) tuples.
    """
    properties = []
    for property_ in element.iter(XMLTag.TRANSIENT_PROPERTY):
        name = property_.get(XMLAttr.NAME)
        type_ = property_.get(XMLAttr.TYPE)
        if (status := property_.get(XMLAttr.STATUS)) is not None: 
            status = int(status)
        properties.append((name, type_, status))
    return properties

def read_expand(expand: Element) -> set[str]:
    """Recursively reads the names that are expanded in the expand element."""
    all_expanded = set()
    if name := expand.get(XMLAttr.NAME):
        all_expanded.add(name)
    for sub in expand.findall(XMLTag.EXPAND):
        for sub_name in read_expand(sub):
            all_expanded.add(sub_name)
    return all_expanded

def read_extensions(extendable: Element) -> list[tuple[str, str]]:
    """Finds and reads an Extensions element and provides a list of (type, name) 
    tuples for each one.
    """
    data = []
    if not (extensions := extendable.find(XMLTag.EXTENSIONS)):
        return data # Return empty list of no extensions found
    for ext in extensions.iter(XMLTag.EXTENSION):
        data.append((ext.get(XMLAttr.TYPE), ext.get(XMLAttr.NAME)))
    return data

def read_view_provider_data(view_provider_data: Element
                            ) -> list[tuple[dict[str, str], list, list]]:
    """Reads ViewProvider elements from a ViewProviderData element as a list of 
    (attributes, extensions, properties) tuples.
    """
    data = []
    for provider in view_provider_data.iter(XMLTag.VIEW_PROVIDER):
        extensions = read_extensions(provider)
        properties = read_properties(provider.find(XMLTag.PROPERTIES))
        attributes = dict(provider.attrib)
        data.append((attributes, extensions, properties))
    return data

class Document:
    """A class representing a FreeCAD document, read without the FreeCAD API."""
    
    def __init__(self, filepath: str | Path) -> None:
        self.archive = ZipFile(filepath)
        self.members = {m.filename: m for m in self.archive.infolist()}
        with self.archive.open(self.members[SubFile.DOCUMENT_XML]) as file:
            self.tree = ET.fromstring(file.read())
        
        properties_element = self.tree.find(XMLTag.PROPERTIES)
        object_element = self.tree.find(XMLTag.OBJECTS)
        object_data_element = self.tree.find(XMLTag.OBJECT_DATA)
        
        self.properties = read_properties(properties_element)
        self.private = read_transient_properties(properties_element)
        self.document_schema_version = self.tree.get(XMLAttr.SCHEMA_VERSION)
        self.program_version = self.tree.get(XMLAttr.PROGRAM_VERSION)
        self.file_version = self.tree.get(XMLAttr.FILE_VERSION)
        self.string_hasher = self.tree.get(XMLAttr.STRING_HASHER)
        
        objects = read_objects(object_element)
        dependencies = read_object_deps(object_element)
        
        self.name_to_id = {name: id_ for name, _, id_ in objects}
        self.id_to_name = {id_: name for name, _, id_ in objects}
        
        object_data = []
        for object_ in object_data_element.iter(XMLTag.OBJECT):
            object_data.append((object_.get(XMLAttr.NAME), object_))
        self.objects = {}
        for name, type_, id_ in objects:
            object_dict = {XMLAttr.NAME: name, XMLAttr.TYPE: type_, XMLAttr.ID: id_}
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
        
        expand_element = self.gui_tree.find(XMLTag.EXPAND)
        view_data_element = self.gui_tree.find(XMLTag.VIEW_PROVIDER_DATA)
        
        self.expand = read_expand(expand_element)
        self.view_provider_data = read_view_provider_data(view_data_element)
        
