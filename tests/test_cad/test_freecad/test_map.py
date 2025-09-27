from os.path import join
from math import radians
import unittest

from PanCAD import PartFile
from PanCAD.cad.freecad import App, Part, Sketcher
from PanCAD.cad.freecad.feature_mappers import (FreeCADMap,
                                                FeatureID,
                                                SubFeatureID,
                                                SketchElementID,
                                                SketchSubGeometryID,)
from PanCAD.cad.freecad.constants import ListName
from PanCAD.geometry import (LineSegment,
                             CoordinateSystem,
                             Sketch,
                             FeatureContainer,
                             Extrude,)
from PanCAD.geometry.constants import ConstraintReference

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

class TestPanCADtoFreeCAD(unittest.TestCase):
    
    def setUp(self):
        self.file = PartFile("Testing Mapping")
        self.document = App.newDocument()
        self.test_map = FreeCADMap(self.document)
    
    def test_nominal_init(self):
        mapping = FreeCADMap(self.document)
    
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

class TestFreeCADtoPanCADCube1x1x1(unittest.TestCase):
    
    def setUp(self):
        sample_dir = sample_freecad.__path__[0]
        filename = "cube_1x1x1.FCStd"
        filepath = join(sample_dir, filename)
        self.document = App.open(filepath)
        self.test_map = FreeCADMap(self.document)
    
    def test_add_cube_body(self):
        pass
        