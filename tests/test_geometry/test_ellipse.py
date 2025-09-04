import math
from numbers import Real
import unittest

import numpy as np

from PanCAD.geometry import Ellipse, Line, Point
from PanCAD.utils.verification import assertPanCADAlmostEqual

ROUNDING_PLACES = 10

class TestInit(unittest.TestCase):
    
    @staticmethod
    def focal_point(center: Point,
                    a: Real,
                    b: Real,
                    major_direction: tuple[Real],
                    plus: bool) -> Point:
        c = math.sqrt(a**2 - b**2)
        if plus:
            return Point(center + c*np.array(major_direction))
        else:
            return Point(center - c*np.array(major_direction))
    
    def check_values(self,
                     test: Ellipse,
                     center: Point,
                     semi_major_axis: Real,
                     semi_minor_axis: Real,
                     major_axis_line: Line,
                     minor_axis_line: Line=None,
                     uid: str=None):
        # Set up expected
        if minor_axis_line is None:
            minor_axis_line = Line(
                center,
                major_axis_line.direction  @ np.array([[0, 1], [-1, 0]])
            )
        
        plus_focal = self.focal_point(center,
                                      semi_major_axis,
                                      semi_minor_axis,
                                      major_axis_line.direction,
                                      True)
        
        minus_focal = self.focal_point(center,
                                       semi_major_axis,
                                       semi_minor_axis,
                                       major_axis_line.direction,
                                       False)
        
        # Real and geometry Sub-tests
        with self.subTest("center !=", expected=center, got=test.center):
            assertPanCADAlmostEqual(self, test.center, center, ROUNDING_PLACES)
        with self.subTest("major_axis_line !=",
                          expected=major_axis_line,
                          got=test.major_axis_line):
            assertPanCADAlmostEqual(self,
                                    test.major_axis_line,
                                    major_axis_line,
                                    ROUNDING_PLACES)
        with self.subTest("minor_axis_line !=",
                          expected=minor_axis_line,
                          got=test.minor_axis_line):
            assertPanCADAlmostEqual(self,
                                    test.minor_axis_line,
                                    minor_axis_line,
                                    ROUNDING_PLACES)
        with self.subTest("semi_major_axis !=",
                          expected=semi_major_axis,
                          got=test.semi_major_axis):
            self.assertAlmostEqual(test.semi_major_axis,
                                   semi_major_axis,
                                   ROUNDING_PLACES)
        with self.subTest("semi_minor_axis !=",
                          expected=semi_minor_axis,
                          got=test.semi_minor_axis):
            self.assertAlmostEqual(test.semi_minor_axis,
                                   semi_minor_axis,
                                   ROUNDING_PLACES)
        with self.subTest("plus_focal_point !=",
                          expected=plus_focal,
                          got=test.focal_point_plus):
            np.testing.assert_allclose(test.focal_point_plus.cartesian,
                                       plus_focal.cartesian)

class Test2DEllipseInitialization(TestInit):
    
    def setUp(self):
        self.uid = "test_ellipse"
    
    def test_for_nominal_init(self):
        center = (0, 0)
        a = 2
        b = 1
        major_direction = (1, 0)
        ellipse = Ellipse(center, a, b, major_direction, uid=self.uid)
        center_pt = Point(center)
        major_line = Line(center_pt, major_direction)
        self.check_values(ellipse, center_pt, a, b, major_line, uid=self.uid)
    
    def test_for_from_angle_init(self):
        center = (0, 0)
        a = 2
        b = 1
        center_pt = Point(center)
        major_angles = [0, 45]
        for degrees, angle in zip(major_angles, map(math.radians, major_angles)):
            with self.subTest(degree_definition=degrees):
                ellipse = Ellipse.from_angle(center, a, b, angle,
                                             uid=self.uid)
                major_line = Line.from_point_and_angle(center, angle)
                self.check_values(ellipse, center_pt, a, b, major_line,
                                  uid=self.uid)

class TestEllipseDunders(unittest.TestCase):
    
    def test_rich_equal_true(self):
        center = (0, 0)
        a = 2
        b = 1
        major_direction = (1, 0)
        ellipse_a = Ellipse(center, a, b, major_direction)
        ellipse_b = Ellipse(center, a, b, major_direction)
        self.assertTrue(ellipse_a == ellipse_b)
    
    def test_rich_equal_false(self):
        center = (0, 0)
        a = 2
        b = 1
        b_mismatch = 1.5
        major_direction = (1, 0)
        ellipse_a = Ellipse(center, a, b, major_direction)
        ellipse_b = Ellipse(center, a, b_mismatch, major_direction)
        self.assertFalse(ellipse_a == ellipse_b)
    
    def test_copy(self):
        center = (0, 0)
        a = 2
        b = 1
        major_direction = (1, 0)
        ellipse_a = Ellipse(center, a, b, major_direction)
        ellipse_b = ellipse_a.copy()
        self.assertTrue(ellipse_a == ellipse_b)

class Test2DEllipseChanges(TestInit):
    
    def setUp(self):
        self.center = (0, 0)
        self.center_pt = Point(self.center)
        self.a = 2
        self.b = 1
        self.major_direction = (1, 0)
        self.uid = "test_ellipse"
        self.ellipse = Ellipse(self.center,
                               self.a,
                               self.b,
                               self.major_direction,
                               uid=self.uid)
    
    def test_center_change(self):
        new_center = (1, 1)
        self.ellipse.center = new_center
        new_center_pt = Point(new_center)
        new_major_line = Line(new_center_pt, self.major_direction)
        self.check_values(self.ellipse,
                          new_center_pt,
                          self.a,
                          self.b,
                          new_major_line,
                          uid=self.uid)
    
    def test_major_axis_direction_change(self):
        new_direction = (1, 1)
        self.ellipse.major_axis_direction = new_direction
        new_major_line = Line(self.center_pt, new_direction)
        self.check_values(self.ellipse,
                          self.center_pt,
                          self.a,
                          self.b,
                          new_major_line,
                          uid=self.uid)
    
    def test_major_axis_angle_change(self):
        new_angle = math.radians(45)
        self.ellipse.major_axis_angle = new_angle
        new_major_line = Line.from_point_and_angle(self.center_pt, new_angle)
        self.check_values(self.ellipse,
                          self.center_pt,
                          self.a,
                          self.b,
                          new_major_line,
                          uid=self.uid)
    
    def test_minor_axis_angle_change(self):
        new_minor_angle = 135
        new_major_angle = math.radians(new_minor_angle - 90)
        self.ellipse.minor_axis_angle = math.radians(new_minor_angle)
        new_major_line = Line.from_point_and_angle(self.center_pt,
                                                   new_major_angle)
        self.check_values(self.ellipse,
                          self.center_pt,
                          self.a,
                          self.b,
                          new_major_line,
                          uid=self.uid)