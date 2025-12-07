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

from pancad.cad.freecad import xml_readers
from pancad.cad.freecad.constants.archive_constants import (
    Tag, SubFile, Part, Sketcher, PartDesign, App
)

from . import dump

class OneOfEachSketchGeometry(TestCase):
    def setUp(self):
        sample_dir = Path(sample_freecad.__file__).parent
        self.path = sample_dir / "one_of_each_sketch_geometry.FCStd"
        with ZipFile(self.path).open(SubFile.DOCUMENT_XML) as document:
            self.tree = ElementTree.fromstring(document.read())
    
    def test_read_sketch_geometry_info(self):
        test = xml_readers.read_sketch_geometry_info(self.tree)
        rows = [test[0], *test[1]]
        print()
        for row in rows:
            print(row)
    
    def test_read_sketch_constraints(self):
        test = xml_readers.read_sketch_constraints(self.tree)
        rows = [test[0], *test[1]]
        print()
        for row in rows:
            print(row)
    
    def test_read_sketch_geometry(self):
        tests = [
            Part.ARC_OF_CIRCLE,
            Part.CIRCLE,
            Part.ELLIPSE,
            Part.LINE_SEGMENT,
            Part.POINT,
        ]
        for type_ in tests:
            with self.subTest(f"Read {type_.value} geometry"):
                fields, data = xml_readers.read_sketch_geometry(self.tree, type_)
                print(type_)
                print(fields)
                for row in data:
                    print(row)
    
    def test_get_sketch_geometry_types(self):
        test = xml_readers.get_sketch_geometry_types(self.tree)
        pp(test)
    
    def test_get_object_types(self):
        test = xml_readers.get_object_types(self.tree)
        expected = [PartDesign.BODY, Sketcher.SKETCH, 
                    App.PLANE, App.ORIGIN, App.LINE,]
        self.assertCountEqual(test, expected)
        pp(test)
    
    def test_read_object_type(self):
        types = xml_readers.get_object_types(self.tree)
        for type_ in types:
            with self.subTest(f"Read {type_} object"):
                columns, data = xml_readers.read_object_type(self.tree, type_)
                dicts = []
                for row in data:
                    dicts.append(
                        {column: value for column, value in zip(columns, row)}
                    )
                print(type_)
                pp(dicts[0])

class Cube1x1x1(TestCase):
    
    def setUp(self):
        sample_dir = Path(sample_freecad.__file__).parent
        self.path = sample_dir / "cube_1x1x1.FCStd"
        with ZipFile(self.path).open(SubFile.DOCUMENT_XML) as document:
            self.tree = ElementTree.fromstring(document.read())
    
    def test_read_metadata(self):
        data = xml_readers.read_metadata(self.tree)
        pp(data)
    
    def test_read_dependencies(self):
        data = xml_readers.read_dependencies(self.tree)
        pp(data)