import unittest

from pancad.constants import ConstraintReference
from pancad.geometry.point import Point
from pancad.geometry.line import Line
from pancad.geometry.line_segment import LineSegment
from pancad.geometry.plane import Plane
from pancad.geometry.circle import Circle
from pancad.constraints.distance import (
    HorizontalDistance, VerticalDistance, Distance, Diameter, Radius, Angle
)

class TestAngleDistanceInit(unittest.TestCase):
    def test_angle_nominal_init(self):
        angle = Angle(LineSegment((0, 0), (1, 1)), LineSegment((1, 1), (1, 2)),
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
        hd = HorizontalDistance(self.a, self.b,
                                value=self.distance, uid=self.uid)
    
    def test_distance_init_2d(self):
        # Checking whether init errors out nominally
        d = Distance(self.a, self.b, value=self.distance, uid=self.uid)
    
    def test_distance_init_3d(self):
        # Checking whether init errors out nominally
        d = Distance(self.a_3d, self.b_3d, value=self.distance, uid=self.uid)

class TestCurveDimensionInit2D(unittest.TestCase):
    
    def setUp(self):
        self.uid = "test"
        self.radius_value = 5
        self.center = Point(0, 0)
        self.circle = Circle(self.center, self.radius_value)
    
    def test_radius_init_2d(self):
        r = Radius(self.circle, value=self.radius_value, uid=self.uid)
    
    def test_diameter_init_2d(self):
        d = Diameter(self.circle, value=2*self.radius_value, uid=self.uid)

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
            hd = HorizontalDistance(self.a_3d, self.b_3d,
                                    value=self.distance, uid=self.uid)
    
    def test_mixed_dimension_distance(self):
        with self.assertRaises(ValueError):
            d = Distance(self.a_3d, self.b, value=self.distance, uid=self.uid)
    
    def test_negative_value(self):
        with self.assertRaises(ValueError):
            d = Distance(self.a, self.b, value=-self.distance, uid=self.uid)
    
    def test_plane_to_horizontal_distance(self):
        plane = Plane((0,0,0), (0,0,1))
        with self.assertRaises(ValueError):
            hd = HorizontalDistance(plane, self.b,
                                    value=self.distance, uid=self.uid)

class TestDunder(unittest.TestCase):
    def setUp(self):
        uid = "test"
        self.a = Point(0, 0)
        self.b = Point(0, 0)
        self.distance = 10
        self.hd = HorizontalDistance(self.a, self.b,
                                     value=self.distance, uid=uid)
        self.vd = VerticalDistance(self.a, self.b,
                                   value=self.distance, uid=uid)
    
    def test_repr_angle(self):
        # Checks whether repr errors out
        vd_repr = repr(self.vd)
    
    def test_str_angle(self):
        # Checks whether str errors out
        vd_str = str(self.vd)

class DunderTest:
    def test_repr(self):
        result = repr(self.constraint)
    
    def test_str(self):
        result = str(self.constraint)

class TestHorizontalDistanceDunders(unittest.TestCase, DunderTest):
    def setUp(self):
        a, b = Point(0, 0), Point(10, 0)
        self.constraint = HorizontalDistance(a, b,
                                             value=10, uid="test")

class TestVerticalDistanceDunders(unittest.TestCase, DunderTest):
    def setUp(self):
        a, b = Point(0, 0), Point(10, 0)
        self.constraint = VerticalDistance(a, b,
                                           value=10, uid="test")

class TestAngleDunders(unittest.TestCase, DunderTest):
    def setUp(self):
        a, b = LineSegment((0, 0), (1, 1)), LineSegment((1, 1), (1, 2))
        self.constraint = Angle(a, b,
                                value=45, quadrant=1, uid="test")

if __name__ == "__main__":
    unittest.main()