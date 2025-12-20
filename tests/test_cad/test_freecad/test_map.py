from os.path import join
from math import radians
import unittest

try:
    import FreeCAD as App
    import Sketcher
    import Part
except ImportError:
    import sys
    from ._bootstrap import get_app_dir
    sys.path.append(str(get_app_dir()))
    import FreeCAD as App
    import Sketcher
    import Part

from pancad import PartFile
from pancad.cad.freecad._feature_mappers import FreeCADMap
from pancad.cad.freecad._map_typing import (
    FeatureID,
    SubFeatureID,
    SketchElementID,
    SketchSubGeometryID,
)
from pancad.cad.freecad.constants import ListName
from pancad.geometry import (LineSegment,
                             CoordinateSystem,
                             Sketch,
                             FeatureContainer,
                             Extrude,)
from pancad.geometry.constants import ConstraintReference

from tests.sample_pancad_objects import sample_sketches
from tests import sample_freecad

class TestMapIDTypes(unittest.TestCase):
    
    def test_get_id_type(self):
        tests = [
            (1000, FeatureID),
            ((1000, ConstraintReference.CORE), SubFeatureID),
            ((1000, ListName.GEOMETRY, 0), SketchElementID),
            ((1000, ListName.EXTERNALS, 0), SketchElementID),
            (
                (1000, ListName.GEOMETRY, 0, ConstraintReference.CORE),
                SketchSubGeometryID
            ),
        ]
        for freecad_id, expected_type in tests:
            with self.subTest(freecad_id=freecad_id, expected=expected_type):
                self.assertEqual(FreeCADMap.get_id_type(freecad_id),
                                 expected_type)

class TestPancadtoFreeCAD(unittest.TestCase):
    
    def setUp(self):
        self.file = PartFile("Testing Mapping")
        self.document = App.newDocument()
        self.test_map = FreeCADMap(self.document, self.file)
    
    def test_map_add_feature_container(self):
        container = FeatureContainer(name="TestBucket")
        coordinate_system = CoordinateSystem()
        line = LineSegment((0, 0), (1, 1))
        sketch = Sketch(name="Test Mapping Sketch",
                        geometry=[line],
                        coordinate_system=coordinate_system)
        container.features = [coordinate_system, sketch]
        self.test_map.add_pancad_feature(container)
    
    def test_map_cube_extrude(self):
        container = FeatureContainer(name="TestBucket")
        cs = CoordinateSystem()
        sketch = sample_sketches.square(cs)
        extrude = Extrude.from_length(sketch, 1, name="Test Extrude")
        container.features = [cs, sketch, extrude]
        self.test_map.add_pancad_feature(container)
    
    def test_map_ellipse_extrude(self):
        container = FeatureContainer(name="TestBucket")
        cs = CoordinateSystem()
        sketch = sample_sketches.ellipse(cs)
        extrude = Extrude.from_length(sketch, 1, name="Test Extrude")
        container.features = [cs, sketch, extrude]
        self.test_map.add_pancad_feature(container)

class TestFreeCADtoPancadCube1x1x1(unittest.TestCase):
    
    def setUp(self):
        sample_dir = sample_freecad.__path__[0]
        filename = "cube_1x1x1.FCStd"
        filepath = join(sample_dir, filename)
        self.part_file = PartFile("Testing Mapping")
        self.document = App.open(filepath)
        self.test_map = FreeCADMap(self.document, self.part_file)
    
    def test_add_cube_body(self):
        body = self.document.Objects[0]
        self.test_map.add_freecad_feature(body)
    
    def test_str_dunder(self):
        # Checking if str errors out
        body = self.document.Objects[0]
        self.test_map.add_freecad_feature(body)
        out = str(self.test_map)
    
    def test_repr_dunder(self):
        body = self.document.Objects[0]
        self.test_map.add_freecad_feature(body)
        out = repr(self.test_map)
