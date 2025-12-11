from pathlib import Path
from pprint import pp
from zipfile import ZipFile
from unittest import TestCase
from xml.etree import ElementTree

from pancad.cad.freecad import read_xml
from pancad.cad.freecad.constants.archive_constants import (
    App, Part, PartDesign, Sketcher, SubFile
)

from tests import sample_freecad

from . import dump

class OneOfEachSketchGeometry(TestCase):
    def setUp(self):
        sample_dir = Path(sample_freecad.__file__).parent
        self.path = sample_dir / "one_of_each_sketch_geometry.FCStd"
        with ZipFile(self.path).open(SubFile.DOCUMENT_XML) as document:
            self.tree = ElementTree.fromstring(document.read())
    
    def test_object_info(self):
        data = read_xml.object_info(self.tree)
        pp(data)
    
    def test_sketch_geometry_info(self):
        test = read_xml.sketch_geometry_info(self.tree)
        pp(test)
    
    def test_sketch_constraints(self):
        test = read_xml.sketch_constraints(self.tree)
        pp(test)
    
    def test_sketch_geometry(self):
        tests = [
            Part.ARC_OF_CIRCLE,
            Part.CIRCLE,
            Part.ELLIPSE,
            Part.LINE_SEGMENT,
            Part.POINT,
        ]
        for type_ in tests:
            with self.subTest(f"Read {type_.value} geometry"):
                data = read_xml.sketch_geometry(self.tree, type_)
                pp(data)
    
    def test_sketch_geometry_types(self):
        test = read_xml.sketch_geometry_types(self.tree)
        pp(test)
    
    def test_object_types(self):
        test = read_xml.object_types(self.tree)
        expected = [PartDesign.BODY, Sketcher.SKETCH, 
                    App.PLANE, App.ORIGIN, App.LINE,]
        self.assertCountEqual(test, expected)
        pp(test)
    
    def test_object_type(self):
        types = read_xml.object_types(self.tree)
        for type_ in types:
            with self.subTest(f"Read {type_} object"):
                data = read_xml.object_type(self.tree, type_)
                print(type_)
                pp(data)

class OneOfEachFeature(TestCase):
    def setUp(self):
        sample_dir = Path(sample_freecad.__file__).parent
        self.path = sample_dir / "one_of_each_feature.FCStd"
        with ZipFile(self.path).open(SubFile.DOCUMENT_XML) as document:
            self.tree = ElementTree.fromstring(document.read())
    
    def test_object_type(self):
        types = read_xml.object_types(self.tree)
        for type_ in types:
            with self.subTest(f"Read {type_} object"):
                data = read_xml.object_type(self.tree, type_)
                pp(data)

class Cube1x1x1(TestCase):
    def setUp(self):
        sample_dir = Path(sample_freecad.__file__).parent
        self.path = sample_dir / "cube_1x1x1.FCStd"
        with ZipFile(self.path).open(SubFile.DOCUMENT_XML) as document:
            self.tree = ElementTree.fromstring(document.read())
        with ZipFile(self.path).open(SubFile.GUI_DOCUMENT_XML) as document:
            self.gui_tree = ElementTree.fromstring(document.read())
    
    def test_metadata(self):
        data = read_xml.metadata(self.tree)
        pp(data)
    
    def test_dependencies(self):
        data = read_xml.dependencies(self.tree)
        pp(data)
    
    def test_object_type(self):
        types = read_xml.object_types(self.tree)
        for type_ in types:
            with self.subTest(f"Read {type_} object"):
                data = read_xml.object_type(self.tree, type_)
                pp(data)
    
    def test_view_provider_properties(self):
        data = read_xml.view_provider_properties(self.gui_tree, "Sketch")
        pp(data)
    
    def test_camera(self):
        data = read_xml.camera(self.gui_tree)
        expected = {
            'CameraType': 'OrthographicCamera',
            'viewportMapping': 'ADJUST_CAMERA',
            'position': '0.55408478 -3.0705452 22.883564',
            'orientation': '-0.74290597 0.30772173 0.59447283 5.0660691',
            'nearDistance': '1.429081e-005',
            'farDistance': '44.038101',
            'aspectRatio': '1',
            'focalDistance': '15.944237',
            'height': '122.14027'
         }
        self.assertDictEqual(data, expected)