import unittest

from PanCAD.geometry import Point
from PanCAD.geometry.constraints import Coincident
from PanCAD.geometry.constants import ConstraintReference as CR

class test_init(unittest.TestCase):
    
    def setUp(self):
        self.a = Point(0, 0)
        self.b = Point(0, 0)
        self.uid = "test"
    
    def test_point_init(self):
        # Checking whether init errors out nominally
        c = Coincident(self.a, CR.CORE, self.b, CR.CORE, self.uid)
    
    def test_point_change(self):
        # Check whether updating the point updates the value in coincident
        c = Coincident(self.a, CR.CORE, self.b, CR.CORE, self.uid)
        original_a = self.a.copy()
        new_a = Point(1, 1)
        self.a.update(new_a)
        self.assertEqual(c.get_a(), new_a)

class test_check(unittest.TestCase):
    
    def test_points_coincident(self):
        a = Point(0, 0)
        b = Point(0, 0)
        c = Coincident(a, CR.CORE, b, CR.CORE, "test")
        self.assertTrue(c.check())
    
    def test_points_not_coincident(self):
        a = Point(0, 0)
        b = Point(1, 1)
        c = Coincident(a, CR.CORE, b, CR.CORE, "test")
        self.assertFalse(c.check())
    

if __name__ == "__main__":
    unittest.main()