import math
import sys
from pathlib import Path
import unittest

import numpy as np
from PanCAD.geometry.point import Point
from PanCAD.geometry.line import Line
from PanCAD.geometry.line_segment import LineSegment
from PanCAD.utils import trigonometry as trig
from PanCAD.utils import verification

ROUNDING_PLACES = 10

class TestLineSegmentInit(unittest.TestCase):
    
    def test_init_two_points_2d(self):
        pt_a, pt_b = (Point(0, 0), Point(1, 1))
        check_line = Line.from_two_points(pt_a, pt_b)
        
        check_features = (pt_a.copy(), pt_b.copy(), check_line.copy())
        
        test_line_segment = LineSegment(pt_a, pt_b)
        test_features = (test_line_segment.point_a,
                         test_line_segment.point_b,
                         test_line_segment.get_line())
        for check, test in zip(check_features, test_features):
            with self.subTest(test=test, check=check):
                verification.assertPanCADAlmostEqual(self, test, check,
                                                     ROUNDING_PLACES)
    
    def test_init_two_tuples_2d(self):
        pt_a, pt_b = ((0, 0), (1, 1))
        check_line = Line.from_two_points(pt_a, pt_b)
        
        check_features = (Point(pt_a).copy(),
                          Point(pt_b).copy(),
                          check_line.copy())
        test_line_segment = LineSegment(pt_a, pt_b)
        test_features = (test_line_segment.point_a,
                         test_line_segment.point_b,
                         test_line_segment.get_line())
        for check, test in zip(check_features, test_features):
            with self.subTest(test=test, check=check):
                verification.assertPanCADAlmostEqual(self, test, check,
                                                     ROUNDING_PLACES)
    
    def test_init_two_points_3d(self):
        pt_a, pt_b = (Point(0, 0, 0), Point(1, 1, 1))
        check_line = Line.from_two_points(pt_a, pt_b)
        
        check_features = (pt_a,
                          pt_b,
                          check_line.copy())
        test_line_segment = LineSegment(pt_a, pt_b)
        test_features = (test_line_segment.point_a,
                         test_line_segment.point_b,
                         test_line_segment.get_line())
        for check, test in zip(check_features, test_features):
            with self.subTest(test=test, check=check):
                verification.assertPanCADAlmostEqual(self, test, check,
                                                     ROUNDING_PLACES)
    
    def test_init_two_tuples_3d(self):
        pt_a, pt_b = ((0, 0, 0), (1, 1, 1))
        check_line = Line.from_two_points(pt_a, pt_b)
        
        check_features = (Point(pt_a),
                          Point(pt_b),
                          check_line.copy())
        test_line_segment = LineSegment(pt_a, pt_b)
        test_features = (test_line_segment.point_a,
                         test_line_segment.point_b,
                         test_line_segment.get_line())
        for check, test in zip(check_features, test_features):
            with self.subTest(test=test_line_segment, check=check_features):
                verification.assertPanCADAlmostEqual(self, test, check,
                                                     ROUNDING_PLACES)

class TestLineSegmentGetters(unittest.TestCase):
    
    def setUp(self):
        lines = [
            ((0, 0), (1, 1)),
            ((0, 1), (1, 2)),
            ((0, 0, 0), (1, 1, 1)),
        ]
        test_lines = [LineSegment(*line) for line in lines]
        directions = [
            (1, 1),
            (1, 1),
            (1, 1, 1),
        ]
        directions = [
            trig.to_1D_tuple(trig.get_unit_vector(d)) for d in directions
        ]
        lengths = [
            math.hypot(1, 1),
            math.hypot(1, 1),
            math.hypot(1, 1, 1),
        ]
        axis_lengths = [
            (1, 1, None),
            (1, 1, None),
            (1, 1, 1),
        ]
        self.direction_tests = list(zip(test_lines, directions))
        self.length_tests = list(zip(test_lines, lengths))
        self.axis_length_tests = list(zip(test_lines, axis_lengths))
    
    def test_direction_getter(self):
        for line_segment, direction in self.direction_tests:
            with self.subTest(line_segment=line_segment, direction=direction):
                verification.assertPanCADAlmostEqual(
                    self, line_segment.direction, direction, ROUNDING_PLACES
                )
    
    def test_length_getter(self):
        for line_segment, length in self.length_tests:
            with self.subTest(line_segment=line_segment, length=length):
                self.assertAlmostEqual(line_segment.length, length)
    
    def test_get_x_length(self):
        for line_segment, (x_length, _, _) in self.axis_length_tests:
            with self.subTest(line_segment=line_segment, x_length=x_length):
                result = line_segment.get_x_length()
                self.assertAlmostEqual(result, x_length)


if __name__ == "__main__":
    with open("tests/logs/" + Path(sys.modules[__name__].__file__).stem
              +".log", "w") as f:
        f.write("finished")
    unittest.main()