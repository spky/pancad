import unittest

from PanCAD.geometry import Point, Line, LineSegment
from PanCAD.geometry.constraints import Horizontal
from PanCAD.geometry.constants import ConstraintReference as CR

class test_init(unittest.TestCase):
    
    def setUp(self):
        self.uid = "test"
    
    def test_point_point_init(self):
        # Checking whether init errors out nominally
        a = Point(0, 0)
        b = Point(0, 0)
        v = Horizontal(a, CR.CORE, b, CR.CORE, self.uid)
    
    def test_line_init(self):
        a = LineSegment((0, 0), (1, 1))
        v = Horizontal(a, CR.CORE, None, None, uid=self.uid)

class TestDunder(unittest.TestCase):
    def setUp(self):
        uid = "test"
        a = Point(0, 0)
        b = Point(0, 0)
        c = LineSegment((0, 0), (1, 1))
        self.horizontal_pt_pt = Horizontal(a, CR.CORE, b, CR.CORE, uid)
        self.horizontal_line_segment = Horizontal(c, CR.CORE, uid=uid)
    
    def test_repr_pt_pt(self):
        # Checks whether repr errors out
        horiz_repr = repr(self.horizontal_pt_pt)
    
    def test_str_pt_pt(self):
        # Checks whether str errors out
        horiz_str = str(self.horizontal_pt_pt)
    
    def test_repr_line_segment(self):
        # Checks whether repr errors out
        horiz_repr = repr(self.horizontal_line_segment)
    
    def test_str_line_segment(self):
        # Checks whether str errors out
        horiz_str = str(self.horizontal_line_segment)

if __name__ == "__main__":
    unittest.main()