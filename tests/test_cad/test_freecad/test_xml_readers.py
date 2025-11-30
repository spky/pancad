import os
from pathlib import Path
from pprint import pp
import datetime
from uuid import UUID
import sqlite3
from zipfile import ZipFile
from contextlib import closing
from unittest import TestCase, skip
from xml.etree import ElementTree

from tests import sample_freecad

from itertools import islice

from pancad.cad.freecad.xml_readers import (
    read_metadata,
    read_sub_attrib,
    read_dependencies,
    read_sketch_geometry_info,
    read_sketch_constraints,
    read_line_segments,
    read_circles,
    write_fcstd_sql,
)
from pancad.cad.freecad.xml_properties import read_properties
from pancad.cad.freecad import xml_appearance
from pancad.cad.freecad.constants import XMLTag, SubFile, XMLAttr

from . import dump

class FCStdXMLUtils(TestCase):
    def setUp(self):
        sample_dir = Path(sample_freecad.__file__).parent
        self.path = sample_dir / "cube_1x1x1.FCStd"
        with ZipFile(self.path).open(SubFile.DOCUMENT_XML) as document:
            self.tree = ElementTree.fromstring(document.read())
    
    def test_read_sub_attrib_properties(self):
        # Checking an element with consistent subelement attributes
        element = self.tree.find(XMLTag.PROPERTIES)
        names, attrs = read_sub_attrib(element, XMLTag.PROPERTY)
        print("Names:", names); print("Attributes:"); pp(attrs)
        self.assertTupleEqual(names, ("name", "type", "status"))
    
    def test_read_sub_attrib_string_hasher(self):
        # Checking an element with no sub elements
        element = self.tree.find(XMLTag.STRING_HASHER)
        names, attrs = read_sub_attrib(element, XMLTag.PROPERTY)
        print("Names:", names, "Attributes:", attrs)
        self.assertTupleEqual(names, tuple())
    
    def test_read_sub_attrib_body(self):
        # Checking an element with inconsistent subelement attributes
        element = self.tree.find("./ObjectData/Object[@name='Body']/Properties")
        names, attrs = read_sub_attrib(element, XMLTag.PROPERTY)
        print("Names:", names); print("Attributes:"); pp(attrs)
        group = [element for element in attrs if element[0] == "Group"][0]
        self.assertTupleEqual(group, ("Group", "App::PropertyLinkList", None))

class OneOfEachSketchGeometry(TestCase):
    def setUp(self):
        sample_dir = Path(sample_freecad.__file__).parent
        self.path = sample_dir / "one_of_each_sketch_geometry.FCStd"
        with ZipFile(self.path).open(SubFile.DOCUMENT_XML) as document:
            self.tree = ElementTree.fromstring(document.read())
    
    def test_read_sketch_geometry_info(self):
        test = read_sketch_geometry_info(self.tree)
        rows = [test[0], *test[1]]
        print()
        for row in rows:
            print(row)
    
    def test_read_sketch_constraints(self):
        test = read_sketch_constraints(self.tree)
        rows = [test[0], *test[1]]
        print()
        for row in rows:
            print(row)
    
    def test_read_line_segments(self):
        test = read_line_segments(self.tree)
        pp(test)
    
    def test_read_circles(self):
        test = read_circles(self.tree)
        pp(test)

class Cube1x1x1(TestCase):
    
    def setUp(self):
        sample_dir = Path(sample_freecad.__file__).parent
        self.path = sample_dir / "cube_1x1x1.FCStd"
    
    def test_read_metadata(self):
        data = read_metadata(self.path)
        pp(data)
        self.assertDictEqual(data, expected)
    
    def test_read_dependencies(self):
        data = read_dependencies(self.path)
        pp(data)
        self.assertDictEqual(data, expected)
    
    def test_read_object_types(self):
        data = read_object_types(self.path)
        pp(data)
        self.assertDictEqual(data, expected)
    
    def test_read_object_ids(self):
        data = read_object_ids(self.path)
        pp(data)
        self.assertDictEqual(data, expected)
    
    def test_write_fcstd_sql(self):
        db = Path(dump.__file__).parent / "test_write_fcstd_sql.db"
        db.unlink(missing_ok=True)
        write_fcstd_sql(self.path, db)
        
        def dict_factory(cursor, row):
            fields = [column[0] for column in cursor.description]
            return {key: value for key, value in zip(fields, row)}
        
        with closing(sqlite3.connect(db, detect_types=sqlite3.PARSE_DECLTYPES)) as con:
            con.row_factory = dict_factory
            rows = con.execute("SELECT * FROM FreecadDocumentMetadata")
            metadata = rows.fetchall()
            
            rows = con.execute("SELECT * FROM FreecadObjectsCommon")
            objects = rows.fetchall()
            
            rows = con.execute("SELECT * FROM FreecadObjectDependencies")
            dependencies = rows.fetchall()
            
            rows = con.execute("SELECT * FROM FreecadSketchConstraints")
            constraints = rows.fetchall()
            
            rows = con.execute("SELECT * FROM FreecadSketchGeometry")
            geometry = rows.fetchall()
        # pp(metadata)
        # pp(objects)
        # pp(dependencies)
        # pp(constraints)
        pp(geometry)
        db.unlink()