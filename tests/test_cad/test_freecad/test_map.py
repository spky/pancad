from math import radians
import unittest

from PanCAD import PartFile
from PanCAD.cad.freecad import App, Part, Sketcher
from PanCAD.cad.freecad.feature_mappers import FreeCADMap
from PanCAD.geometry import (LineSegment,
                             CoordinateSystem,
                             Sketch,
                             FeatureContainer,
                             Extrude,)
from PanCAD.geometry.constants import ConstraintReference

from tests.sample_pancad_objects import sample_sketches

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

class TestPanCADtoFreeCADCubeExtrudeMap(TestPanCADtoFreeCAD):
    
    def test_map_cube_extrude(self):
        container = FeatureContainer(name="TestBucket")
        cs = CoordinateSystem()
        sketch = sample_sketches.square(cs)
        extrude = Extrude.from_length(sketch, 1, name="Test Extrude")
        container.features = [cs, sketch, extrude]
        self.test_map.add_pancad_feature(container)

class TestPanCADtoFreeCADEllipseExtrude(TestPanCADtoFreeCAD):
    
    def test_map_ellipse_extrude(self):
        container = FeatureContainer(name="TestBucket")
        cs = CoordinateSystem()
        sketch = sample_sketches.ellipse(cs)
        extrude = Extrude.from_length(sketch, 1, name="Test Extrude")
        container.features = [cs, sketch, extrude]
        self.test_map.add_pancad_feature(container)
