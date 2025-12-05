"""A module providing functions to interface with the FreeCAD portions of a 
pancad sqlite database.
"""
from __future__ import annotations

from contextlib import closing
from pathlib import Path
from typing import TYPE_CHECKING
from xml.etree import ElementTree
from zipfile import ZipFile

import logging
import sqlite3
import tomllib

from pancad import resources
from pancad.constants.config_paths import DATABASE

from .constants.archive_constants import Part, SubFile
from . import xml_readers

if TYPE_CHECKING:
    from typing import Any
    
    from .constants.archive_constants import Tag

logger = logging.getLogger(__name__)

sqlite3.register_converter("BOOLEAN", lambda x: bool(int(x)))


def write_data_to_sql(database: Path,
                      table: str,
                      columns: tuple[str],
                      data: list[tuple[str]]):
    """Writes data read using xml_readers into sql"""
    con = sqlite3.connect(database) 
    
    # Translate string data to SQL types
    with closing(con.cursor()) as cur:
        column_info = cur.execute(
            f"SELECT name, type FROM  pragma_table_info('{table}')"
        ).fetchall()
    types = {name: type_ for name, type_ in column_info}
    dispatch = _TO_SQL_TYPE
    parsed_data = []
    for row in data:
        parsed_row = []
        for column, value in zip(columns, row):
            try:
                parsed_value = _TO_SQL_TYPE[types[column]](value)
            except KeyError:
                parsed_value = value
            parsed_row.append(parsed_value)
        parsed_data.append(tuple(parsed_row))
    
    questions = ",".join("?" * len(columns))
    columns_csv = ",".join(columns)
    with closing(con.cursor()) as cur:
        command = f"INSERT INTO {table} ({columns_csv}) VALUES ({questions})"
        cur.executemany(command, parsed_data)
    con.commit()
    con.close()

_TO_SQL_TYPE = {
    "TEXT": lambda x: x if x is None else str(x),
    "BOOLEAN": lambda x: x if x is None else bool(int(x)),
    "INTEGER": lambda x: x if x is None else int(x),
    "REAL": lambda x: x if x is None else float(x),
    "UUID": lambda x: x if x is None else str(x),
}

def ensure_tables(database: Path) -> None:
    """Makes sure that the pancad database has the minimum columns for each 
    table based on the freecad.toml settings.
    """
    with open(Path(resources.__file__).parent / "freecad.toml", "rb") as file:
        config = tomllib.load(file)
    
    for name, settings in config["sql"]["tables"].items():
        type_ = settings["type"]
        template = config["sql"]["table_types"][type_]
        match type_:
            case "listed_uniques":
                columns = [f"{column} {type_}"
                           for column, type_ in settings["columns"].items()]
                command = template.format(
                    name=name,
                    columns=",".join(columns),
                    uniques=",".join(settings["unique"])
                )
        try:
            with closing(sqlite3.connect(database)) as con:
                con.execute(command)
                con.commit()
        except sqlite3.OperationalError as err:
            raise FreecadTomlSqlError(
                "freecad.toml caused sqlite3.OperationalError.\n"
                f"Command: \n{command}".strip() + f"\nsqlite3 error: {str(err)}"
            )

def fcstd_to_sql(path: Path) -> None:
    """Reads a freecad file and loads it into the pancad database."""
    
    with open(Path(resources.__file__).parent / "freecad.toml", "rb") as file:
        config = tomllib.load(file)
    
    with ZipFile(path) as file:
        with file.open(SubFile.DOCUMENT_XML) as document:
            doc_tree = ElementTree.fromstring(document.read())
        with file.open(SubFile.GUI_DOCUMENT_XML) as gui_document:
            gui_tree = ElementTree.fromstring(gui_document.read())
    
    ensure_tables(DATABASE)
    
    # Read Non-Geometry Data
    table_funcs = [
        ("FreecadObjectInfo", xml_readers.read_object_info),
        ("FreecadSketchGeometryInfo", xml_readers.read_sketch_geometry_info),
        ("FreecadConstraint", xml_readers.read_sketch_constraints),
        ("FreecadObjectDependencies", xml_readers.read_dependencies),
    ]
    for table, reader in table_funcs:
        columns, data = reader(doc_tree)
        write_data_to_sql(DATABASE, table, columns, data)
    
    # Read Sketch Geometry Data
    geometry_tables = {table["freecad_geometry_type"]: name
                       for name, table in config["sql"]["tables"].items()
                       if "freecad_geometry_type" in table}
    for type_, tag in xml_readers.get_sketch_geometry_types(doc_tree):
        try:
            columns, data = xml_readers.read_sketch_geometry(doc_tree,
                                                             type_, tag)
            write_data_to_sql(DATABASE, geometry_tables[type_], columns, data)
        except UnsupportedGeometryType:
            logger.error(f"Could not parse geometry type in file: {type_}")

class UnsupportedGeometryType(TypeError):
    """Raised when an operation is attempted on an unsupported or unknown 
    FreeCAD geometry element type.
    """

class FreecadTomlSqlError(sqlite3.OperationalError):
    """Raised when the freecad.toml has caused an sqlite3 operational error."""