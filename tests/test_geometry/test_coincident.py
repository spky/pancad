import unittest

from pancad.geometry import Point, LineSegment, Circle
from pancad.geometry.constraints import Coincident
from pancad.geometry.constants import ConstraintReference

class TestInit(unittest.TestCase):
    
    def setUp(self):
        self.a = Point(0, 0)
        self.b = Point(0, 0)
        self.uid = "test"
    
    def test_point_init(self):
        # Checking whether init errors out nominally
        c = Coincident(self.a, ConstraintReference.CORE,
                       self.b, ConstraintReference.CORE, uid=self.uid)
    
    def test_point_change(self):
        # Check whether updating the point updates the value in coincident
        c = Coincident(self.a, ConstraintReference.CORE,
                       self.b, ConstraintReference.CORE, uid=self.uid)
        original_a = self.a.copy()
        new_a = Point(1, 1)
        self.a.update(new_a)
        self.assertEqual(c.get_constrained()[0], new_a)

class TestValidation(unittest.TestCase):
    def test_combination_validation_line_circle_edges(self):
        a = LineSegment((0, 0), (1, 1))
        b = Circle((0, 0), 1)
        with self.assertRaises(TypeError):
            c = Coincident(a, ConstraintReference.CORE,
                           b, ConstraintReference.CORE)
    
    def test_combination_validation_line_circle_edges_reversec(self):
        a = LineSegment((0, 0), (1, 1))
        b = Circle((0, 0), 1)
        with self.assertRaises(TypeError):
            c = Coincident(b, ConstraintReference.CORE,
                           a, ConstraintReference.CORE)
    

if __name__ == "__main__":
    unittest.main()