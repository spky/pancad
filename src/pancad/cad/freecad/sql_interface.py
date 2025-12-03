"""A module providing functions to interface with the FreeCAD portions of a 
pancad sqlite database.
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from uuid import UUID
from xml.etree import ElementTree
from zipfile import ZipFile

import logging
import sqlite3

from pancad import resources

from .constants.archive_constants import Part, SubFile
from . import xml_readers

if TYPE_CHECKING:
    from typing import Any
    
    from .constants.archive_constants import Tag

logger = logging.getLogger(__name__)

def parse_sketch_geometry(tree: ElementTree,
                          type_: Part,
                          tag: Tag) -> tuple[tuple[str], list[tuple[Any]]]:
    """Reads and translates sketch geometry data from an FCStd file's document 
    tree into data ready to write to sql. Any unrecognized fields will be passed 
    as the existing string.
    
    :param tree: An FCStd document.xml ElementTree.
    :param type_: The type attribute value on a Geometry element.
    :param tag: The tag of the corresponding Geometry subelement.
    :returns: A tuple of column names and a list of data tuples in the same 
        order as the columns.
    :raises UnsupportedGeometryType: Raised when passed an invalid type_.
    # """
    fields, data = xml_readers.read_sketch_geometry(tree, type_, tag)
    try:
        dispatch = _TO_SQL[type_]
    except KeyError:
        raise UnsupportedGeometryType(type_)
    
    parsed = []
    for row in data:
        row_data = []
        for field, string in zip(fields, row):
            try:
                value = dispatch[field](string)
            except KeyError:
                value = string
            row_data.append(value)
        parsed.append(tuple(row_data))
    return fields, parsed

def ensure_fcstd_tables() -> None:
    """Makes sure that the pancad database has the minimum columns for each 
    table
    """
    
# def data_to_sql(table: str, columns: tuple[str], data: list[tuple[Any]]) -> None:
    # with sqlite3.connect(
    

def fcstd_to_sql(path: Path) -> None:
    """Reads a freecad file and loads it into the pancad database."""
    
    with ZipFile(path) as file:
        with file.open(SubFile.DOCUMENT_XML) as document:
            doc_tree = ElementTree.fromstring(document.read())
        with file.open(SubFile.GUI_DOCUMENT_XML) as gui_document:
            gui_tree = ElementTree.fromstring(gui_document.read())
    
    for type_, tag in xml_readers.get_sketch_geometry_types(doc_tree):
        try:
            columns, data = parse_sketch_geometry(doc_tree, type_, tag)
        except UnsupportedGeometryType:
            logger.error(f"Could not parse geometry type in file: {type_}")

class UnsupportedGeometryType(TypeError):
    """Raised when an operation is attempted on an unsupported or unknown 
    geometry element type.
    """

# Dispatch dicts for writing to SQL
_LINE_SEGMENT_TO_SQL = {
    "FileUid": lambda x: UUID(x),
    "id": lambda x: int(x),
    "StartX": lambda x: float(x),
    "StartY": lambda x: float(x),
    "StartZ": lambda x: float(x),
    "EndX": lambda x: float(x),
    "EndY": lambda x: float(x),
    "EndZ": lambda x: float(x),
}

_CIRCLE_TO_SQL = {
    "FileUid": lambda x: UUID(x),
    "id": lambda x: int(x),
    "CenterX": lambda x: float(x),
    "CenterY": lambda x: float(x),
    "CenterZ": lambda x: float(x),
    "NormalX": lambda x: float(x),
    "NormalY": lambda x: float(x),
    "NormalZ": lambda x: float(x),
    "AngleXU": lambda x: float(x),
    "Radius": lambda x: float(x),
}

_ELLIPSE_TO_SQL = {
    "FileUid": lambda x: UUID(x),
    "id": lambda x: int(x),
    "CenterX": lambda x: float(x),
    "CenterY": lambda x: float(x),
    "CenterZ": lambda x: float(x),
    "NormalX": lambda x: float(x),
    "NormalY": lambda x: float(x),
    "NormalZ": lambda x: float(x),
    "MajorRadius": lambda x: float(x),
    "MinorRadius": lambda x: float(x),
    "AngleXU": lambda x: float(x),
}

_ARC_OF_CIRCLE_TO_SQL = {
    "FileUid": lambda x: UUID(x),
    "id": lambda x: int(x),
    "CenterX": lambda x: float(x),
    "CenterY": lambda x: float(x),
    "CenterZ": lambda x: float(x),
    "NormalX": lambda x: float(x),
    "NormalY": lambda x: float(x),
    "NormalZ": lambda x: float(x),
    "AngleXU": lambda x: float(x),
    "Radius": lambda x: float(x),
    "StartAngle": lambda x: float(x),
    "EndAngle": lambda x: float(x),
}

_POINT_TO_SQL = {
    "FileUid": lambda x: UUID(x),
    "id": lambda x: int(x),
    "X": lambda x: float(x),
    "Y": lambda x: float(x),
    "Z": lambda x: float(x),
}

_TO_SQL = {
    Part.LINE_SEGMENT: _LINE_SEGMENT_TO_SQL,
    Part.CIRCLE: _CIRCLE_TO_SQL,
    Part.ELLIPSE: _ELLIPSE_TO_SQL,
    Part.ARC_OF_CIRCLE: _ARC_OF_CIRCLE_TO_SQL,
    Part.POINT: _POINT_TO_SQL,
}

# sqlite3.register_adapter(UUID, lambda u: str(u))
# sqlite3.register_adapter(bool, int)
# sqlite3.register_converter("BOOLEAN", lambda v: bool(int(v)))

# def write_line_segment(tree: 

# def table_columns(table: str) -> list[str]:
    # with open(Path(pancad_data.__file__).parent / "freecad.toml", "rb") as file:
        # config = tomllib.load(file)["sql_columns"][table]
    # return list(config.keys())

# def table_column_settings(table: str) -> list[str]:
    # with open(Path(pancad_data.__file__).parent / "freecad.toml", "rb") as file:
        # config = tomllib.load(file)["sql_columns"][table]
    # return [f"{name} {type_}" for name, type_ in config.items()]

# def write_sketch_geometry(database: str,
                          # as_read_data: list[tuple[Any]],
                          # file_uid: str) -> None:
    # TABLE = "FreecadSketchGeometry"
    # columns = table_column_settings(TABLE)
    # data = [(file_uid, *values) for values in as_read_data]
    
    # with closing(sqlite3.connect(database)) as con:
        # con.execute("CREATE TABLE IF NOT EXISTS %s(%s)"
                    # % (TABLE, ",".join(columns)))
        # q_marks = ",".join("?" * len(columns))
        # con.executemany("INSERT INTO %s VALUES(%s)" % (TABLE, q_marks), data)
        # con.commit()

# def write_constraints(database: str,
                      # as_read_data: dict[str, list[dict]],
                      # file_uid: UUID) -> None:
    # TABLE = "FreecadSketchConstraints"
    # columns = table_column_settings(TABLE)
    # data = []
    # for sketch, constraints in as_read_data.items():
        # for i, constraint in enumerate(constraints):
            # constraint.update(
                # {"FileUid": file_uid, "SketchName": sketch, "ListIndex": i}
            # )
            # data.append(tuple(constraint[column]
                              # for column in table_columns(TABLE)))
    
    # with closing(sqlite3.connect(database)) as con:
        # command = """CREATE TABLE IF NOT EXISTS %s(%s,
                  # UNIQUE(FileUid, SketchName, ListIndex))"""
        # con.execute(command % (TABLE, ", ".join(columns)))
        # q_marks = ",".join("?" * len(columns))
        # con.executemany("INSERT INTO %s VALUES(%s)" % (TABLE, q_marks), data)
        # con.commit()

# def write_metadata(database: str, as_read_data: dict[str, Any]) -> None:
    # """Writes FCStd file metadata to sql database. Only stores default FreeCAD 
    # metadata.
    # """
    # TABLE = "FreecadDocumentMetadata"
    # columns = table_column_settings(TABLE)
    # data = [as_read_data[column] for column in table_columns(TABLE)]
    
    # with closing(sqlite3.connect(database)) as con:
        # con.execute("CREATE TABLE IF NOT EXISTS %s(%s, UNIQUE(Uid))"
                    # % (TABLE, ",".join(columns)))
        # q_marks = ",".join("?" * len(columns))
        # con.execute("INSERT INTO %s VALUES(%s)" % (TABLE, q_marks), data)
        # con.commit()

# def write_objects_common(database: str,
                         # as_read_data: list[tuple[Any]],
                         # file_uid: UUID) -> None:
    # """Writes the data that all FCStd objects share in common to sql database."""
    # TABLE = "FreecadObjectsCommon"
    # columns = table_column_settings(TABLE)
    # data = [(file_uid,) + row for row in as_read_data]
    
    # with closing(sqlite3.connect(database)) as con:
        # con.execute("CREATE TABLE IF NOT EXISTS %s(%s, UNIQUE(FileUid, Id, Name))"
                    # % (TABLE, ",".join(columns)))
        # q_marks = ",".join("?" * len(columns))
        # con.executemany("INSERT INTO %s VALUES(%s)" % (TABLE, q_marks), data)
        # con.commit()

# def write_object_dependencies(database: str,
                              # as_read_data: dict[str, list[str]],
                              # file_uid: str) -> None:
    # TABLE = "FreecadObjectDependencies"
    # columns = table_column_settings(TABLE)
    # data = []
    # for result, dependencies in as_read_data.items():
        # data.extend([(file_uid, result, dep) for dep in set(dependencies)])
    
    # with closing(sqlite3.connect(database)) as con:
        # con.execute("CREATE TABLE IF NOT EXISTS %s(%s)"
                    # % (TABLE, ",".join(columns)))
        # q_marks = ",".join("?" * len(columns))
        # con.executemany("INSERT INTO %s VALUES(%s)" % (TABLE, q_marks), data)
        # con.commit()