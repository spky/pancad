from numbers import Real
import unittest

import numpy as np

from PanCAD.geometry import Ellipse, Line, Point
from PanCAD.utils.verification import assertPanCADAlmostEqual

ROUNDING_PLACES = 10

class TestInit(unittest.TestCase):
    
    def check_values(self,
                     test: Ellipse,
                     center: Point,
                     semi_major_axis: Real,
                     semi_minor_axis: Real,
                     major_axis_line: Line,
                     minor_axis_line: Line=None,
                     uid: str=None):
        # Set up expected
        if uid is None:
            center_uid = None
            major_axis_uid = None
            minor_axis_uid = None
        else:
            center_uid = test.CENTER_UID_FORMAT.format(uid=uid)
            major_axis_uid = test.MAJOR_AXIS_UID_FORMAT.format(uid=uid)
            minor_axis_uid = test.MINOR_AXIS_UID_FORMAT.format(uid=uid)
        
        if minor_axis_line is None:
            minor_axis_line = Line(
                center,
                major_axis_line.direction  @ np.array([[0, 1], [-1, 0]])
            )
        
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
        
        # uid Sub-tests
        with self.subTest("ellipse uid !=", expected=uid, got=test.uid):
            self.assertEqual(test.uid, test.uid)
            
        with self.subTest("center uid !=",
                          expected=center_uid,
                          got=test.center.uid):
            self.assertEqual(test.center.uid, center_uid)
        with self.subTest("major_axis_line uid !=",
                          expected=major_axis_uid,
                          got=test.major_axis_line.uid):
            self.assertEqual(test.major_axis_line.uid, major_axis_uid)
        with self.subTest("minor_axis_line uid !=",
                          expected=minor_axis_uid,
                          got=test.minor_axis_line.uid):
            self.assertEqual(test.minor_axis_line.uid, minor_axis_uid)

class Test2DEllipse(TestInit):
    
    def setUp(self):
        self.uid = "test_ellipse"
    
    def test_for_nominal_error(self):
        center = (0, 0)
        a = 2
        b = 1
        major_direction = (1, 0)
        ellipse = Ellipse(center, a, b, major_direction, uid=self.uid)
        center_pt = Point(center)
        major_line = Line(center_pt, major_direction)
        self.check_values(ellipse, center_pt, a, b, major_line, uid=self.uid)
