import unittest

from PanCAD.cad.freecad import App, Part, Sketcher
from PanCAD.cad.freecad.constants import ObjectType
from PanCAD.cad.freecad.feature_mappers import FreeCADMap
from PanCAD.cad.freecad.sketch_geometry import get_freecad_sketch_geometry
from PanCAD.geometry import LineSegment, CoordinateSystem
from PanCAD.geometry.constants import ConstraintReference

class TestPanCADtoFreeCAD(unittest.TestCase):
    
    def setUp(self):
        self.mapping = FreeCADMap()
    
    def test_nominal_init(self):
        mapping = FreeCADMap()
    
    def test_map_line_segment(self):
        pancad_line_1 = LineSegment((0, 0), (1, 1))
        pancad_line_2 = LineSegment((-1, 0), (1, 0))
        freecad_line = get_freecad_sketch_geometry(pancad_line_1)
        self.mapping[pancad_line_1] = freecad_line
    
    def test_map_coordinate_system(self):
        document = App.newDocument()
        root = document.addObject(ObjectType.BODY, "Body")
        cs = CoordinateSystem()
        self.mapping[cs] = root.Origin
        print(self.mapping[cs, ConstraintReference.X].Label)
    
