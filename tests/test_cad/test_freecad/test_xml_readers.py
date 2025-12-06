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
    read_dependencies,
    read_sketch_geometry_info,
    read_sketch_constraints,
    read_sketch_geometry,
    get_sketch_geometry_types
)
from pancad.cad.freecad.xml_properties import read_properties
from pancad.cad.freecad import xml_appearance
from pancad.cad.freecad.constants.archive_constants import (
    Tag, SubFile, XMLGeometryType
)

from . import dump

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
    
    def test_read_sketch_geometry(self):
        tests = [
            XMLGeometryType.ARC_OF_CIRCLE,
            XMLGeometryType.CIRCLE,
            XMLGeometryType.ELLIPSE,
            XMLGeometryType.LINE_SEGMENT,
            XMLGeometryType.POINT,
        ]
        for type_ in tests:
            with self.subTest(f"Read {type_.value} geometry"):
                fields, data = read_sketch_geometry(self.tree, type_)
                print(type_)
                print(fields)
                for row in data:
                    print(row)
    
    def test_get_sketch_geometry_types(self):
        test = get_sketch_geometry_types(self.tree)
        pp(test)

class Cube1x1x1(TestCase):
    
    def setUp(self):
        sample_dir = Path(sample_freecad.__file__).parent
        self.path = sample_dir / "cube_1x1x1.FCStd"
        with ZipFile(self.path).open(SubFile.DOCUMENT_XML) as document:
            self.tree = ElementTree.fromstring(document.read())
    
    def test_read_metadata(self):
        data = read_metadata(self.tree)
        pp(data)
    
    def test_read_dependencies(self):
        data = read_dependencies(self.tree)
        pp(data)