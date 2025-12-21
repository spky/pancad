import unittest

from pancad.geometry import Point, Line, LineSegment, Plane, Circle
from pancad.geometry.constraints import (
    HorizontalDistance, VerticalDistance, Distance,
    Radius, Diameter, Angle
)
from pancad.geometry.constants import ConstraintReference

class TestAngleDistanceInit(unittest.TestCase):
    def test_angle_nominal_init(self):
        angle = Angle(LineSegment((0, 0), (1, 1)), ConstraintReference.CORE,
                      LineSegment((1, 1), (1, 2)), ConstraintReference.CORE,
                      value=45, quadrant=1, uid="test", is_radians=False)

class TestLinearDistanceInit(unittest.TestCase):
    
    def setUp(self):
        self.uid = "test"
        self.a = Point(0, 0)
        self.b = Point(1, 1)
        self.a_3d = Point(0, 0, 0)
        self.b_3d = Point(1, 1, 1)
        self.distance = 10
    
    def test_horizontal_distance_init(self):
        # Checking whether init errors out nominally
        hd = HorizontalDistance(self.a, ConstraintReference.CORE,
                                self.b, ConstraintReference.CORE,
                                value=self.distance, uid=self.uid)
    
    def test_distance_init_2d(self):
        # Checking whether init errors out nominally
        d = Distance(self.a, ConstraintReference.CORE,
                     self.b, ConstraintReference.CORE,
                     value=self.distance, uid=self.uid)
    
    def test_distance_init_3d(self):
        # Checking whether init errors out nominally
        d = Distance(self.a_3d, ConstraintReference.CORE,
                     self.b_3d, ConstraintReference.CORE,
                     value=self.distance, uid=self.uid)

class TestCurveDimensionInit2D(unittest.TestCase):
    
    def setUp(self):
        self.uid = "test"
        self.radius_value = 5
        self.center = Point(0, 0)
        self.circle = Circle(self.center, self.radius_value)
    
    def test_radius_init_2d(self):
        r = Radius(self.circle, ConstraintReference.CORE,
                   value=self.radius_value, uid=self.uid)
    
    def test_diameter_init_2d(self):
        d = Diameter(self.circle, ConstraintReference.CORE,
                     value=2*self.radius_value, uid=self.uid)

class TestValidation(unittest.TestCase):
    
    def setUp(self):
        self.uid = "test"
        self.a = Point(0, 0)
        self.b = Point(1, 1)
        self.a_3d = Point(0, 0, 0)
        self.b_3d = Point(1, 1, 1)
        self.distance = 10
    
    def test_3d_horizontal(self):
        with self.assertRaises(ValueError):
            hd = HorizontalDistance(self.a_3d, ConstraintReference.CORE,
                                    self.b_3d, ConstraintReference.CORE,
                                    value=self.distance, uid=self.uid)
    
    def test_mixed_dimension_distance(self):
        with self.assertRaises(ValueError):
            d = Distance(self.a_3d, ConstraintReference.CORE,
                         self.b, ConstraintReference.CORE,
                         value=self.distance, uid=self.uid)
    
    def test_negative_value(self):
        with self.assertRaises(ValueError):
            d = Distance(self.a, ConstraintReference.CORE,
                         self.b, ConstraintReference.CORE,
                         value=-self.distance, uid=self.uid)
    
    def test_plane_to_horizontal_distance(self):
        plane = Plane((0,0,0), (0,0,1))
        with self.assertRaises(ValueError):
            hd = HorizontalDistance(plane, ConstraintReference.CORE,
                                    self.b, ConstraintReference.CORE,
                                    value=self.distance, uid=self.uid)

class TestDunder(unittest.TestCase):
    def setUp(self):
        uid = "test"
        self.a = Point(0, 0)
        self.b = Point(0, 0)
        self.distance = 10
        self.hd = HorizontalDistance(self.a, ConstraintReference.CORE,
                                     self.b, ConstraintReference.CORE,
                                     value=self.distance, uid=uid)
        self.vd = VerticalDistance(self.a, ConstraintReference.CORE,
                                   self.b, ConstraintReference.CORE,
                                   value=self.distance, uid=uid)
    
    def test_repr_angle(self):
        # Checks whether repr errors out
        vd_repr = repr(self.vd)
    
    def test_str_angle(self):
        # Checks whether str errors out
        vd_str = str(self.vd)
    
    def test_eq_horizontal_distance_equal(self):
        hd_same = HorizontalDistance(self.a, ConstraintReference.CORE,
                                     self.b, ConstraintReference.CORE,
                                     value=self.distance, uid="same")
        self.assertEqual(self.hd, hd_same)

class DunderTest:
    def test_repr(self):
        result = repr(self.constraint)
    
    def test_str(self):
        result = str(self.constraint)

class TestHorizontalDistanceDunders(unittest.TestCase, DunderTest):
    def setUp(self):
        a, b = Point(0, 0), Point(10, 0)
        self.constraint = HorizontalDistance(a, ConstraintReference.CORE,
                                             b, ConstraintReference.CORE,
                                             value=10, uid="test")

class TestVerticalDistanceDunders(unittest.TestCase, DunderTest):
    def setUp(self):
        a, b = Point(0, 0), Point(10, 0)
        self.constraint = VerticalDistance(a, ConstraintReference.CORE,
                                           b, ConstraintReference.CORE,
                                           value=10, uid="test")

class TestAngleDunders(unittest.TestCase, DunderTest):
    def setUp(self):
        a, b = LineSegment((0, 0), (1, 1)), LineSegment((1, 1), (1, 2))
        self.constraint = Angle(a, ConstraintReference.CORE,
                                b, ConstraintReference.CORE,
                                value=45, quadrant=1, uid="test")

if __name__ == "__main__":
    unittest.main()