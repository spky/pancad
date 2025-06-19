import unittest

from PanCAD.geometry import Point, Line, LineSegment
from PanCAD.geometry.constraints import Vertical
from PanCAD.geometry.constants import ConstraintReference as CR

class test_init(unittest.TestCase):
    
    def setUp(self):
        self.uid = "test"
    
    def test_point_point_init(self):
        # Checking whether init errors out nominally
        a = Point(0, 0)
        b = Point(0, 0)
        v = Vertical(a, CR.CORE, b, CR.CORE, self.uid)
    
    def test_line_init(self):
        a = LineSegment((0, 0), (1, 1))
        v = Vertical(a, CR.CORE, None, None, uid=self.uid)

class TestDunder(unittest.TestCase):
    def setUp(self):
        uid = "test"
        a = Point(0, 0)
        b = Point(0, 0)
        c = LineSegment((0, 0), (1, 1))
        self.vertical_pt_pt = Vertical(a, CR.CORE, b, CR.CORE, uid)
        self.vertical_line_segment = Vertical(c, CR.CORE, uid=uid)
    
    def test_repr_pt_pt(self):
        # Checks whether repr errors out
        vert_repr = repr(self.vertical_pt_pt)
    
    def test_str_pt_pt(self):
        # Checks whether str errors out
        vert_str = str(self.vertical_pt_pt)
    
    def test_repr_line_segment(self):
        # Checks whether repr errors out
        vert_repr = repr(self.vertical_line_segment)
    
    def test_str_line_segment(self):
        # Checks whether str errors out
        vert_str = str(self.vertical_line_segment)

if __name__ == "__main__":
    unittest.main()