"""A module providing functions for reading FreeCAD xml directly."""
from __future__ import annotations

from contextlib import closing
from pathlib import Path
from uuid import UUID
import sqlite3
import tomllib
from typing import TYPE_CHECKING, Any
from xml.etree import ElementTree
from zipfile import ZipFile

from pancad import data as pancad_data

from .xml_properties import read_properties, read_property
from .xml_appearance import read_shape_appearance
from .constants import SubFile, XMLTag, XMLAttr

if TYPE_CHECKING:
    from pathlib import Path
    from xml.etree.ElementTree import Element

sqlite3.register_adapter(UUID, lambda u: str(u))
sqlite3.register_adapter(bool, int)
sqlite3.register_converter("BOOLEAN", lambda v: bool(int(v)))

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

def read_extensions(extensions: Element) -> list[tuple[str, str]]:
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

def read_metadata(filepath: Path | str) -> dict[str, Any]:
    """Returns a dict of metadata field name to values from FCStd files."""
    tree = get_xml_tree(filepath, SubFile.DOCUMENT_XML)
    element = tree.find(XMLTag.PROPERTIES)
    return {name: value for name, *_, value in read_properties(element)}

def read_object_dependencies(filepath: str) -> dict[str, list[str]]:
    """Returns a dict of object name to a list of its dependencies from FCStd 
    files. The lists of dependencies may have duplicates.
    """
    tree = get_xml_tree(filepath, SubFile.DOCUMENT_XML)
    objects = tree.find(XMLTag.OBJECTS)
    data = []
    for object_ in objects.iter(XMLTag.OBJECT_DEPENDENCIES):
        name = object_.get(XMLAttr.NAME_CAPITALIZED)
        dep_iter = object_.iter(XMLTag.DEP)
        depends_on = [dep.get(XMLAttr.NAME_CAPITALIZED) for dep in dep_iter]
        data.append((name, depends_on))
    return {name: dependencies for name, dependencies in data}

def read_object_types(filepath: str) -> dict[str, str]:
    """Returns a dict of object name to its type from FCStd files."""
    tree = get_xml_tree(filepath, SubFile.DOCUMENT_XML)
    objects = tree.find(XMLTag.OBJECTS)
    data = read_objects(objects)
    return {name: type_ for name, type_, _ in data}

def read_object_ids(filepath: str) -> dict[str, int]:
    """Returns a dict of object name to its id integer from FCStd files."""
    tree = get_xml_tree(filepath, SubFile.DOCUMENT_XML)
    objects = tree.find(XMLTag.OBJECTS)
    data = read_objects(objects)
    return {name: id_ for name, _, id_ in data}

def read_object_extensions(filepath: str) -> dict[str, list[tuple[str, str]]]:
    """Returns a dict of object name to a (type, name) tuple for each of its 
    extensions from FCStd files.
    """
    tree = get_xml_tree(filepath, SubFile.DOCUMENT_XML)
    extensions = {}
    object_data = tree.find(XMLTag.OBJECT_DATA)
    for object_ in object_data.iter(XMLTag.OBJECT):
        if (obj_exts := object_.find(XMLTag.EXTENSIONS)) is None:
            continue
        name = object_.attrib[XMLAttr.NAME]
        extensions[name] = [(ext.get(XMLAttr.TYPE), ext.get(XMLAttr.NAME))
                            for ext in obj_exts.iter(XMLTag.EXTENSION)]
    return extensions

def object_property_lists(filepath: str
                          ) -> dict[str, list[tuple[str, str, int | None]]]:
    """Returns a dict of object name to (name, type, status) tuples from FCStd 
    files.
    """
    tree = get_xml_tree(filepath, SubFile.DOCUMENT_XML)
    property_lists = {}
    object_data = tree.find(XMLTag.OBJECT_DATA)
    for object_ in object_data.iter(XMLTag.OBJECT):
        name = object_.attrib[XMLAttr.NAME]
        for property_ in object_.find(XMLTag.PROPERTIES).iter(XMLTag.PROPERTY):
            if (status := property_.get(XMLAttr.STATUS)) is not None:
                status = int(status)
            property_lists.setdefault(name, []).append(
                (property_.get(XMLAttr.NAME),
                 property_.get(XMLAttr.TYPE),
                 status)
            )
    return property_lists

def read_object_property(filepath: str,
                         object_: str,
                         property_: str) -> tuple[str, int, Any]:
    """Returns the type, status, and value of the property for the object in a 
    FCStd file.
    
    :param filepath: Path of a FCStd file.
    :param object_: The name of an object.
    :param property_: The name of a property.
    """
    tree = get_xml_tree(filepath, SubFile.DOCUMENT_XML)
    object_data = tree.find(XMLTag.OBJECT_DATA)
    for data in object_data.iter(XMLTag.OBJECT):
        if data.get(XMLAttr.NAME) == object_:
            properties = data.find(XMLTag.PROPERTIES)
            break
    try:
        for element in properties.iter(XMLTag.PROPERTY):
            if element.get(XMLAttr.NAME) == property_:
                _, type_, status, value = read_property(element)
                return (type_, status, value)
    except UnboundLocalError as err:
        print(f"Object {object_} not found")
        raise

def table_exists(cur: sqlite3.Cursor, name: str):
    tables = cur.execute("""SELECT name FROM sqlite_master WHERE
                         type='table' and name='%s'""" % name).fetchall()
    return len(tables) == 1

def write_fcstd_sql(fcstd: str, database: str):
    OBJECTS_TABLE = "FreecadObjects"
    SHARED_PROPERTIES = ["Label", "Label2", "Visibility"]
    
    object_ids = read_object_ids(fcstd)
    object_types = read_object_types(fcstd)
    
    object_data = []
    for name, id_ in object_ids.items():
        shared = []
        for property_name in SHARED_PROPERTIES:
            *_, value = read_object_property(fcstd, name, property_name)
            shared.append(value)
        type_ = object_types[name]
        object_data.append(
            (name, id_, type_, *shared)
        )
    metadata = read_metadata(fcstd)
    file_uid = metadata["Uid"]
    
    write_metadata(database, metadata)
    write_objects_common(database, object_data, file_uid)
    
    dependencies = read_object_dependencies(fcstd)
    write_object_dependencies(database, dependencies, file_uid)

def table_columns(table: str) -> list[str]:
    with open(Path(pancad_data.__file__).parent / "freecad.toml", "rb") as file:
        config = tomllib.load(file)["sql_columns"][table]
    return list(config.keys())

def table_column_settings(table: str) -> list[str]:
    with open(Path(pancad_data.__file__).parent / "freecad.toml", "rb") as file:
        config = tomllib.load(file)["sql_columns"][table]
    return [f"{name} {type_}" for name, type_ in config.items()]

def write_metadata(database: str, as_read_data: dict[str, Any]) -> None:
    """Writes FCStd file metadata to sql database. Only stores default FreeCAD 
    metadata.
    """
    TABLE = "FreecadDocumentMetadata"
    columns = table_column_settings(TABLE)
    data = [as_read_data[column] for column in table_columns(TABLE)]
    
    with closing(sqlite3.connect(database)) as con:
        con.execute("CREATE TABLE IF NOT EXISTS %s(%s, UNIQUE(Uid))"
                    % (TABLE, ",".join(columns)))
        q_marks = ",".join("?" * len(columns))
        con.execute("INSERT INTO %s VALUES(%s)" % (TABLE, q_marks), data)
        con.commit()

def write_objects_common(database: str,
                         as_read_data: list[tuple[Any]],
                         file_uid: UUID) -> None:
    """Writes the data that all FCStd objects share in common to sql database."""
    TABLE = "FreecadObjectsCommon"
    columns = table_column_settings(TABLE)
    data = [(file_uid,) + row for row in as_read_data]
    
    with closing(sqlite3.connect(database)) as con:
        con.execute("CREATE TABLE IF NOT EXISTS %s(%s, UNIQUE(FileUid, Id, Name))"
                    % (TABLE, ",".join(columns)))
        q_marks = ",".join("?" * len(columns))
        con.executemany("INSERT INTO %s VALUES(%s)" % (TABLE, q_marks), data)
        con.commit()

def write_object_dependencies(database: str,
                              as_read_data: dict[str, list[str]],
                              file_uid: str) -> None:
    TABLE = "FreecadObjectDependencies"
    columns = table_column_settings(TABLE)
    data = []
    for result, dependencies in as_read_data.items():
        data.extend([(file_uid, result, dep) for dep in set(dependencies)])
    
    with closing(sqlite3.connect(database)) as con:
        con.execute("CREATE TABLE IF NOT EXISTS %s(%s)"
                    % (TABLE, ",".join(columns)))
        q_marks = ",".join("?" * len(columns))
        con.executemany("INSERT INTO %s VALUES(%s)" % (TABLE, q_marks), data)
        con.commit()

def get_xml_tree(filepath: Path | str, sub_name: SubFile) -> ElementTree:
    """Returns an xml tree from inside a FCStd file.
    
    :param filepath: A filepath to a FreeCAD FCStd file.
    :param sub_name: The name of the file inside the FCStd file to be accessed.
    """
    zipped = ZipFile(filepath)
    with zipped.open(SubFile.DOCUMENT_XML) as document:
        return ElementTree.fromstring(document.read())

class Document:
    """A class representing a FreeCAD document, read without the FreeCAD API."""
    
    def __init__(self, filepath: str | Path) -> None:
        self.archive = ZipFile(filepath)
        self.members = {m.filename: m for m in self.archive.infolist()}
        with self.archive.open(self.members[SubFile.DOCUMENT_XML]) as file:
            self.tree = ElementTree.fromstring(file.read())
        
        
        # properties_element = self.tree.find(XMLTag.PROPERTIES)
        # object_element = self.tree.find(XMLTag.OBJECTS)
        # object_data_element = self.tree.find(XMLTag.OBJECT_DATA)
        
        # self.properties = read_properties(properties_element)
        # self.private = read_transient_properties(properties_element)
        # self.document_schema_version = self.tree.get(XMLAttr.SCHEMA_VERSION)
        # self.program_version = self.tree.get(XMLAttr.PROGRAM_VERSION)
        # self.file_version = self.tree.get(XMLAttr.FILE_VERSION)
        # self.string_hasher = self.tree.get(XMLAttr.STRING_HASHER)
        
        # objects = read_objects(object_element)
        # dependencies = read_object_deps(object_element)
        
        # self.name_to_id = {name: id_ for name, _, id_ in objects}
        # self.id_to_name = {id_: name for name, _, id_ in objects}
        
        # object_data = []
        # for object_ in object_data_element.iter(XMLTag.OBJECT):
            # object_data.append((object_.get(XMLAttr.NAME), object_))
        # self.objects = {}
        # for name, type_, id_ in objects:
            # object_dict = {XMLAttr.NAME: name, XMLAttr.TYPE: type_, XMLAttr.ID: id_}
            # for dependency_name, list_ in dependencies:
                # if name == dependency_name:
                    # object_dict[XMLTag.OBJECT_DEPENDENCIES] = list_
                    # break
            # for object_data_name, element in object_data:
                # if name == object_data_name:
                    # object_dict[XMLTag.OBJECT_DATA] = element
            # self.objects[id_] = object_dict
        
        # with self.archive.open(self.members[SubFile.GUI_DOCUMENT_XML]) as file:
            # self.gui_tree = ElementTree.fromstring(file.read())
        
        # expand_element = self.gui_tree.find(XMLTag.EXPAND)
        # view_data_element = self.gui_tree.find(XMLTag.VIEW_PROVIDER_DATA)
        
        # self.expand = read_expand(expand_element)
        # self.view_provider_data = read_view_provider_data(view_data_element)
        
