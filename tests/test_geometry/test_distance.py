import unittest

from PanCAD.geometry import Point, Line, LineSegment, Plane
from PanCAD.geometry.constraints import (
    HorizontalDistance, VerticalDistance, Distance
)
from PanCAD.geometry.constants import ConstraintReference as CR

class test_init(unittest.TestCase):
    
    def setUp(self):
        self.uid = "test"
        self.a = Point(0, 0)
        self.b = Point(1, 1)
        self.a_3d = Point(0, 0, 0)
        self.b_3d = Point(1, 1, 1)
        self.distance = 10
    
    def test_horizontal_distance_init(self):
        # Checking whether init errors out nominally
        hd = HorizontalDistance(self.a, CR.CORE, self.b, CR.CORE,
                                self.distance, uid=self.uid)
    
    def test_distance_init_2d(self):
        # Checking whether init errors out nominally
        d = Distance(self.a, CR.CORE, self.b, CR.CORE,
                     self.distance, uid=self.uid)
    
    def test_distance_init_3d(self):
        # Checking whether init errors out nominally
        d = Distance(self.a_3d, CR.CORE, self.b_3d, CR.CORE,
                     self.distance, uid=self.uid)

class test_validation(unittest.TestCase):
    
    def setUp(self):
        self.uid = "test"
        self.a = Point(0, 0)
        self.b = Point(1, 1)
        self.a_3d = Point(0, 0, 0)
        self.b_3d = Point(1, 1, 1)
        self.distance = 10
    
    def test_3d_horizontal(self):
        with self.assertRaises(ValueError):
            hd = HorizontalDistance(self.a_3d, CR.CORE, self.b_3d, CR.CORE,
                                    self.distance, uid=self.uid)
    
    def test_mixed_dimension_distance(self):
        with self.assertRaises(ValueError):
            d = Distance(self.a_3d, CR.CORE, self.b, CR.CORE,
                         self.distance, uid=self.uid)
    
    def test_negative_value(self):
        with self.assertRaises(ValueError):
            d = Distance(self.a, CR.CORE, self.b, CR.CORE,
                         -self.distance, uid=self.uid)
    
    def test_plane_to_horizontal_distance(self):
        plane = Plane((0,0,0), (0,0,1))
        with self.assertRaises(ValueError):
            hd = HorizontalDistance(plane, CR.CORE, self.b, CR.CORE,
                                    self.distance, uid=self.uid)

class TestDunder(unittest.TestCase):
    def setUp(self):
        uid = "test"
        self.a = Point(0, 0)
        self.b = Point(0, 0)
        self.distance = 10
        self.hd = HorizontalDistance(self.a, CR.CORE, self.b, CR.CORE,
                                     self.distance, uid=uid)
        self.vd = VerticalDistance(self.a, CR.CORE, self.b, CR.CORE,
                                   self.distance, uid=uid)
    
    def test_repr_horizontal_distance(self):
        # Checks whether repr errors out
        hd_repr = repr(self.hd)
    
    def test_str__horizontal_distance(self):
        # Checks whether str errors out
        hd_str = str(self.hd)
        
    def test_repr_vertical_distance(self):
        # Checks whether repr errors out
        vd_repr = repr(self.vd)
    
    def test_str_vertical_distance(self):
        # Checks whether str errors out
        vd_str = str(self.vd)
    
    def test_eq_horizontal_distance_equal(self):
        hd_same = HorizontalDistance(self.a, CR.CORE, self.b, CR.CORE,
                                     self.distance, uid="same")
        self.assertEqual(self.hd, hd_same)

if __name__ == "__main__":
    unittest.main()