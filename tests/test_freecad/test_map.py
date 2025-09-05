import unittest

from PanCAD import PartFile
from PanCAD.cad.freecad import App, Part, Sketcher
from PanCAD.cad.freecad.constants import ObjectType
from PanCAD.cad.freecad.feature_mappers import FreeCADMap
from PanCAD.cad.freecad.sketch_geometry import get_freecad_sketch_geometry
from PanCAD.geometry import LineSegment, CoordinateSystem, Sketch
from PanCAD.geometry.constants import ConstraintReference

class TestPanCADtoFreeCAD(unittest.TestCase):
    
    def setUp(self):
        self.document = App.newDocument()
        self.mapping = FreeCADMap()
    
    def test_nominal_init(self):
        mapping = FreeCADMap()
    
    def test_map_line_segment(self):
        pancad_line_1 = LineSegment((0, 0), (1, 1))
        pancad_line_2 = LineSegment((-1, 0), (1, 0))
        freecad_line = get_freecad_sketch_geometry(pancad_line_1)
        self.mapping[pancad_line_1] = freecad_line
    
    def test_map_coordinate_system(self):
        root = self.document.addObject(ObjectType.BODY, "Body")
        cs = CoordinateSystem()
        self.mapping[cs] = root.Origin
    
    def test_map_sketch_with_line(self):
        file = PartFile("Testing Mapping")
        line = LineSegment((0, 0), (1, 1))
        pancad_sketch = Sketch(name="Test Mapping Sketch",
                               geometry=[line])
        file.add_feature(pancad_sketch)
        freecad_body = self.document.addObject(ObjectType.BODY, "Body")
        
        self.mapping[file.get_coordinate_system()] = freecad_body.Origin
        freecad_sketch = self.document.addObject(ObjectType.SKETCH, "Sketch")
        self.mapping[pancad_sketch] = freecad_sketch
        print(self.mapping[pancad_sketch].getParent().Label)
