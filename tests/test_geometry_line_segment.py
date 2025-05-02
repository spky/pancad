import itertools
import math
import sys
from pathlib import Path
import unittest

import numpy as np
from PanCAD.geometry import Point, Line, LineSegment
from PanCAD.utils import trigonometry as trig
from PanCAD.utils import verification

ROUNDING_PLACES = 10

class TestLineSegmentInit2d(unittest.TestCase):
    def setUp(self):
        self.pt_a, self.pt_b = (0, 0), (1, 1)
        self.check_features = (Point(self.pt_a), Point(self.pt_b),
                               Line.from_two_points(self.pt_a, self.pt_b))
    
    def test_init_two_points(self):
        line_seg = LineSegment(Point(self.pt_a), Point(self.pt_b))
        test_features = (line_seg.point_a, line_seg.point_b,
                         line_seg.get_line())
        for check, test in zip(self.check_features, test_features):
            with self.subTest(test=test, check=check):
                verification.assertPanCADAlmostEqual(self, test, check,
                                                     ROUNDING_PLACES)
    
    def test_init_two_tuples(self):
        line_seg = LineSegment(self.pt_a, self.pt_b)
        test_features = (line_seg.point_a, line_seg.point_b,
                         line_seg.get_line())
        for check, test in zip(self.check_features, test_features):
            with self.subTest(test=test, check=check):
                verification.assertPanCADAlmostEqual(self, test, check,
                                                     ROUNDING_PLACES)

class TestLineSegmentInit3d(unittest.TestCase):
    def setUp(self):
        self.pt_a, self.pt_b = (0, 0, 0), (1, 1, 1)
        self.check_features = (Point(self.pt_a), Point(self.pt_b),
                               Line.from_two_points(self.pt_a, self.pt_b))
    
    def test_init_two_points(self):
        line_seg = LineSegment(Point(self.pt_a), Point(self.pt_b))
        test_features = (line_seg.point_a, line_seg.point_b,
                         line_seg.get_line())
        for check, test in zip(self.check_features, test_features):
            with self.subTest(test=test, check=check):
                verification.assertPanCADAlmostEqual(self, test, check,
                                                     ROUNDING_PLACES)
    
    def test_init_two_tuples(self):
        line_seg = LineSegment(self.pt_a, self.pt_b)
        test_features = (line_seg.point_a, line_seg.point_b,
                         line_seg.get_line())
        for check, test in zip(self.check_features, test_features):
            with self.subTest(test=test, check=check):
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
    
    def test_get_xyz_length(self):
        for line_segment, lengths in self.axis_length_tests:
            axis_length_funcs = [line_segment.get_x_length,
                                 line_segment.get_y_length,
                                 line_segment.get_z_length]
            for func, length in zip(axis_length_funcs, lengths):
                if length is None: continue
                with self.subTest(line_segment=line_segment,
                                  func=func.__name__, length=length):
                    self.assertAlmostEqual(func(), length)

class TestLineSegmentLineComparisons(unittest.TestCase):
    
    def setUp(self):
        # The order of these lines correspond to the truths in each test
        self.lines = [
            (((0, 0), (1, 1)), ((0, 1), (1, 2))),
            (((0, 0), (-1, -1)), ((0, 1), (1, 2))),
            (((0, 0), (1, 1)), ((0, 0), (-1, -1))),
            (((0, 0), (0, 1)), ((0, 1), (1, 2))),
            (((0, 0), (1, 0)), ((0, 1), (1, 1))),
            (((0, 0), (1, 0)), ((0, 0), (0, 1))),
            (((0, 0), (1, 1)), ((0, 0), (1, 1))),
            (((0, 0, 0), (1, 1, 1)), ((0, 0, 1), (1, 0, 1))),
        ]
        # product creates every unordered combination of line functions possible, 
        # checking for incompatibilities between any combo of Line and LineSegment
        line_funcs = [LineSegment, Line.from_two_points]
        self.line_func_perms = list(itertools.product(line_funcs, repeat=2))
    
    def zip_truths(self, truths):
        """Applies every permutation of line function to the line points and zips 
        the truth value for the test to the resulting tuple"""
        tests = []
        for (line1pts, line2pts), truth in zip(self.lines, truths):
            for func_1, func_2 in self.line_func_perms:
                tests.append(
                    (func_1(*line1pts), func_2(*line2pts), truth)
                )
        return tests
    
    def test_is_parallel(self):
        truths = [
            True,
            True,
            True,
            False,
            True,
            False,
            True,
            False,
        ]
        tests = self.zip_truths(truths)
        for line1, line2, truth in tests:
            with self.subTest(line1=line1, line2=line2, parallel=truth):
                self.assertEqual(line1.is_parallel(line2), truth)
    
    def test_is_perpendicular(self):
        truths = [
            False,
            False,
            False,
            False,
            False,
            True,
            False,
            False,
        ]
        tests = self.zip_truths(truths)
        for line1, line2, truth in tests:
            with self.subTest(line1=line1, line2=line2, perpendicular=truth):
                self.assertEqual(line1.is_perpendicular(line2), truth)
    
    def test_is_coplanar(self):
        truths = [
            True,
            True,
            True,
            True,
            True,
            True,
            True,
            False,
        ]
        tests = self.zip_truths(truths)
        for line1, line2, truth in tests:
            with self.subTest(line1=line1, line2=line2, coplanar=truth):
                self.assertEqual(line1.is_coplanar(line2), truth)
    
    def test_is_collinear(self):
        truths = [
            False,
            False,
            True,
            False,
            False,
            False,
            True,
            False,
        ]
        tests = self.zip_truths(truths)
        for line1, line2, truth in tests:
            with self.subTest(line1=line1, line2=line2, collinear=truth):
                self.assertEqual(line1.is_collinear(line2), truth)
    
    def test_is_skew(self):
        truths = [
            False,
            False,
            False,
            False,
            False,
            False,
            False,
            True,
        ]
        tests = self.zip_truths(truths)
        for line1, line2, truth in tests:
            with self.subTest(line1=line1, line2=line2, skew=truth):
                self.assertEqual(line1.is_skew(line2), truth)

class TestLineSegmentSpecificComparisons(unittest.TestCase):
    
    def setUp(self):
        lines = [
            (((0, 0), (0, 1)), ((0, 0), (0, 1))),
            (((0, 0), (0, 1)), ((1, 0), (1, 1))),
            (((0, 0), (0, 1)), ((0, 0), (0, 2))),
        ]
        self.lines = [(LineSegment(*l1), LineSegment(*l2)) for l1, l2 in lines]
    
    def test_is_equal_length(self):
        truths = [
            True,
            True,
            False,
        ]
        for (line1, line2), truth in zip(self.lines, truths):
            with self.subTest(line1=line1, line2=line2, equal=truth):
                self.assertEqual(line1.is_equal_length(line2), truth)


if __name__ == "__main__":
    with open("tests/logs/" + Path(sys.modules[__name__].__file__).stem
              +".log", "w") as f:
        f.write("finished")
    unittest.main()