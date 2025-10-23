import unittest
from uuid import UUID
from math import sin, cos, radians, degrees

from numpy import array
from numpy.testing import assert_allclose

from pancad.geometry import CircularArc, Point

class InitAndChangeTest(unittest.TestCase):
    
    def check_values(self,
                     test: CircularArc,
                     center,
                     radius,
                     start_vector,
                     end_vector,
                     is_clockwise,
                     normal_vector=None):
        
        start = array(center) + (radius * array(start_vector))
        end = array(center) + (radius * array(end_vector))
        
        tests = [
            ("center", Point(center), test.center),
            ("radius", radius, test.radius),
            ("start_vector", start_vector, test.start_vector),
            ("start", Point(start), test.start),
            ("end_vector", end_vector, test.end_vector),
            ("end", Point(end), test.end),
            ("is_clockwise", is_clockwise, test.is_clockwise),
            ("normal_vector", normal_vector, test.normal_vector),
        ]
        # for name, expected, result in tests: print(name, expected, result)
        # print("uid", test.uid)
        for name, expected, result in tests:
            with self.subTest(name=name, expected=expected, result=result):
                self.assertEqual(result, expected)
        with self.subTest(expected="uid is a UUID"):
            self.assertTrue(isinstance(test.uid, UUID))
    
    def setUp(self):
        self.center = (0, 0)
        self.radius = 1
        self.start_vector = (1, 0)
        self.end_vector = (0, 1)
        self.is_clockwise = False
        self.test = CircularArc(
            self.center,
            self.radius,
            self.start_vector,
            self.end_vector,
            self.is_clockwise
        )
    
    def test_2d_unit_arc(self):
        self.check_values(
            self.test, self.center, self.radius, self.start_vector,
            self.end_vector, self.is_clockwise,
        )
    
    def test_str(self):
        string = str(self.test)
        # print(string)
    
    def test_change_center(self):
        new_center = (1, 1)
        self.test.center = new_center
        self.check_values(
            self.test,
            new_center,
            self.radius, self.start_vector, self.end_vector, self.is_clockwise,
        )
    
    def test_change_start_vector(self):
        new_vector = (-1, 0)
        self.test.start_vector = new_vector
        self.check_values(
            self.test, self.center, self.radius,
            new_vector,
            self.end_vector, self.is_clockwise,
        )
    
    def test_change_end_vector(self):
        new_vector = (-1, 0)
        self.test.end_vector = new_vector
        self.check_values(
            self.test, self.center, self.radius, self.start_vector,
            new_vector,
            self.is_clockwise,
        )
    
    def test_change_radius(self):
        new_radius = self.radius + 1
        self.test.radius = new_radius
        self.check_values(
            self.test, self.center, new_radius, self.start_vector,
            self.end_vector,
            self.is_clockwise,
        )

class AngleTests(unittest.TestCase):
    
    def test_angle_sweep(self):
        center = (0, 0)
        radius = 1
        
        angles = [0, 30, 45, 60, 90, 120, 135, 150, 180,]
        angles.extend([-a for a in angles])
        end_vector = (1, 0)
        is_clockwise = False
        for angle in map(radians, angles):
            start_vector = (cos(angle), sin(angle))
            test = CircularArc(
                center, radius, start_vector, end_vector, is_clockwise
            )
            with self.subTest(expected=angle, expected_degrees=degrees(angle)):
                # print("result: ", test.start_angle, "expected: ", angle)
                self.assertAlmostEqual(test.start_angle, angle)
    
    def test_from_angles(self):
        center = (0, 0)
        radius = 1
        start_angle = 0
        end_angle = radians(90)
        is_clockwise = False
        
        start_vector = (1, 0)
        end_vector = (0, 1)
        test = CircularArc.from_angles(center,
                                       radius,
                                       start_angle,
                                       end_angle,
                                       is_clockwise)
        with self.subTest(name="start_vector"):
            assert_allclose(test.start_vector, start_vector, atol=1e-9)
        with self.subTest(name="end_vector"):
            assert_allclose(test.end_vector, end_vector, atol=1e-9)
