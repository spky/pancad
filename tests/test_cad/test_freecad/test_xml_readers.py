import os
from pathlib import Path
from pprint import pp
import datetime
from uuid import UUID
import sqlite3
from contextlib import closing
from unittest import TestCase, skip

from tests import sample_freecad

from itertools import islice

from pancad.cad.freecad.xml_readers import (
    Document,
    read_metadata,
    read_object_dependencies,
    read_object_types,
    read_object_ids,
    read_object_extensions,
    object_property_lists,
    write_fcstd_sql,
)
from pancad.cad.freecad.xml_properties import read_properties
from pancad.cad.freecad import xml_appearance
from pancad.cad.freecad.constants import XMLTag, SubFile, XMLAttr

from . import dump

class Cube1x1x1(TestCase):
    
    def setUp(self):
        sample_dir = Path(sample_freecad.__file__).parent
        self.path = sample_dir / "cube_1x1x1.FCStd"
    
    def test_init(self):
        test = Document(self.path)
    
    def test_read_metadata(self):
        data = read_metadata(self.path)
        expected = {
            'Comment': 'A companion',
            'Company': 'Bob Corp',
            'CreatedBy': 'Bob',
            'CreationDate': '2025-06-21T14:22:37Z',
            'Id': 'PART-0001',
            'Label': 'cube_1x1x1',
            'LastModifiedBy': 'Other Bob',
            'LastModifiedDate': '2025-06-26T12:31:25Z',
            'License': 'CC0 1.0 Universal',
            'LicenseURL': 'https://creativecommons.org/publicdomain/zero/1.0/',
            'Material': None,
            'Meta': None,
            'ShowHidden': False,
            'TipName': '',
            'Uid': UUID('7c2a603d-b250-44ce-8938-f714395e519f'),
            'UnitSystem': 'US customary (in, lb)',
            'UseHasher': True
        }
        pp(data)
        self.assertDictEqual(data, expected)
    
    def test_read_object_dependencies(self):
        data = read_object_dependencies(self.path)
        expected = {
            'Body': ['Pad', 'Origin', 'Sketch', 'Pad'],
            'Origin': ['X_Axis', 'Y_Axis', 'Z_Axis',
                       'XY_Plane', 'XZ_Plane', 'YZ_Plane'],
            'X_Axis': [],
            'Y_Axis': [],
            'Z_Axis': [],
            'XY_Plane': [],
            'XZ_Plane': [],
            'YZ_Plane': [],
            'Sketch': ['XY_Plane'],
            'Pad': ['Sketch', 'Sketch', 'Body']
        }
        pp(data)
        self.assertDictEqual(data, expected)
    
    def test_read_object_types(self):
        data = read_object_types(self.path)
        expected = {
            'Body': 'PartDesign::Body',
            'Origin': 'App::Origin',
            'X_Axis': 'App::Line',
            'Y_Axis': 'App::Line',
            'Z_Axis': 'App::Line',
            'XY_Plane': 'App::Plane',
            'XZ_Plane': 'App::Plane',
            'YZ_Plane': 'App::Plane',
            'Sketch': 'Sketcher::SketchObject',
            'Pad': 'PartDesign::Pad'
        }
        pp(data)
        self.assertDictEqual(data, expected)
    
    def test_read_object_ids(self):
        data = read_object_ids(self.path)
        expected = {
            'Body': 2666,
            'Origin': 2667,
            'X_Axis': 2668,
            'Y_Axis': 2669,
            'Z_Axis': 2670,
            'XY_Plane': 2671,
            'XZ_Plane': 2672,
            'YZ_Plane': 2673,
            'Sketch': 2674,
            'Pad': 2675
        }
        pp(data)
        self.assertDictEqual(data, expected)
    
    def test_read_object_extensions(self):
        data = read_object_extensions(self.path)
        expected = {
            'Body': [('App::OriginGroupExtension', 'OriginGroupExtension')],
            'Origin': [('App::GeoFeatureGroupExtension', 'GeoFeatureGroupExtension')],
            'Sketch': [('Part::AttachExtension', 'AttachExtension')],
            'Pad': [('App::SuppressibleExtension', 'SuppressibleExtension')]
        }
        pp(data)
        self.assertDictEqual(data, expected)
    
    def test_object_property_lists(self):
        data = object_property_lists(self.path)
        pp(data)
    
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
        # pp(metadata)
        pp(objects)
        # pp(dependencies)
        db.unlink()
    
    @skip
    def test_read_sketch_properties(self):
        test = Document(self.path)
        sketch_element = test.objects[2674][XMLTag.OBJECT_DATA]
        properties = sketch_element.find(XMLTag.PROPERTIES)
        result = read_properties(sketch_element)
        pp(result)
        # empty = [r for r in result if r[3] is None]
        # print()
        # pp(empty)

class Cube1x1x1Files(TestCase):
    """Tests reading the individual archived files in cube_1x1x1.FCStd"""
    
    def setUp(self):
        sample_dir = Path(sample_freecad.__file__).parent
        filepath = sample_dir / "cube_1x1x1.FCStd"
        self.doc = Document(filepath)
    
    def test_string_hasher(self):
        filename = "StringHasher.Table.txt"
        test = xml_appearance.read_string_hasher(self.doc.archive, filename)

class Cube1x1x1Colored(TestCase):
    
    def setUp(self):
        sample_dir = Path(sample_freecad.__file__).parent
        self.path = sample_dir / "cube_1x1x1_colored.FCStd"
    
    def test_init(self):
        print()
        test = Document(self.path)

@skip
class Empty(TestCase):
    
    def setUp(self):
        sample_dir = Path(sample_freecad.__file__).parent
        self.path = sample_dir / "empty.FCStd"
    
    def test_init(self):
        test = Document(self.path)
        # print("\nProperties")
        # pp(test.properties)
        # print("\nPrivate Properties")
        # pp(test.private)
        # print(test.expand)

@skip
class OnlyOneSketch(TestCase):
    
    def setUp(self):
        sample_dir = Path(sample_freecad.__file__).parent
        self.path = sample_dir / "only_one_sketch.FCStd"
    
    def test_init(self):
        test = Document(self.path)
        
