import itertools
import math
import unittest

import numpy as np
from PanCAD.geometry import Point, Line, LineSegment
from PanCAD.utils import trigonometry as trig
# from PanCAD.utils import verification
from PanCAD.utils.verification import assertPanCADAlmostEqual

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
                assertPanCADAlmostEqual(self, test, check, ROUNDING_PLACES)
    
    def test_init_two_tuples(self):
        line_seg = LineSegment(self.pt_a, self.pt_b)
        test_features = (line_seg.point_a, line_seg.point_b,
                         line_seg.get_line())
        for check, test in zip(self.check_features, test_features):
            with self.subTest(test=test, check=check):
                assertPanCADAlmostEqual(self, test, check, ROUNDING_PLACES)

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
                assertPanCADAlmostEqual(self, test, check, ROUNDING_PLACES)
    
    def test_init_two_tuples(self):
        line_seg = LineSegment(self.pt_a, self.pt_b)
        test_features = (line_seg.point_a, line_seg.point_b,
                         line_seg.get_line())
        for check, test in zip(self.check_features, test_features):
            with self.subTest(test=test, check=check):
                assertPanCADAlmostEqual(self, test, check, ROUNDING_PLACES)

class TestLineSegmentFromPointLengthAngle(unittest.TestCase):
    def test_init_polar_vector(self):
        point = (0, 0)
        polar = (2, math.radians(45))
        test_ls = LineSegment.from_point_length_angle(point, polar)
        expected_ls = LineSegment(point, (math.sqrt(2), math.sqrt(2)))
        assertPanCADAlmostEqual(self, test_ls, expected_ls, ROUNDING_PLACES)
    
    def test_init_polar_float(self):
        point = (0, 0)
        polar = (2, math.radians(45))
        test_ls = LineSegment.from_point_length_angle(point, *polar)
        expected_ls = LineSegment(point, (math.sqrt(2), math.sqrt(2)))
        assertPanCADAlmostEqual(self, test_ls, expected_ls, ROUNDING_PLACES)
    
    def test_init_spherical_vector(self):
        point = (0, 0, 0)
        spherical = (2, math.radians(45), math.radians(90))
        test_ls = LineSegment.from_point_length_angle(point, spherical)
        expected_ls = LineSegment(point, (math.sqrt(2), math.sqrt(2), 0))
        assertPanCADAlmostEqual(self, test_ls, expected_ls, ROUNDING_PLACES)
    
    def test_init_spherical_float(self):
        point = (0, 0, 0)
        spherical = (2, math.radians(45), math.radians(90))
        test_ls = LineSegment.from_point_length_angle(point, *spherical)
        expected_ls = LineSegment(point, (math.sqrt(2), math.sqrt(2), 0))
        assertPanCADAlmostEqual(self, test_ls, expected_ls, ROUNDING_PLACES)

class TestLineSegmentFromPointLengthAngleExceptions(unittest.TestCase):
    
    def setUp(self):
        self.pt2d = (0, 0)
        self.polar = (2, math.radians(45))
        self.pt3d = self.pt2d + (0,)
        self.spherical = self.polar + (math.radians(90),)
        self.length, self.phi, self.theta = self.spherical
    
    def test_polar_vector_phi(self):
        with self.assertRaises(ValueError):
            LineSegment.from_point_length_angle(self.pt2d, self.polar, 3)
    
    def test_polar_vector_phi_theta(self):
        with self.assertRaises(ValueError):
            LineSegment.from_point_length_angle(self.pt2d, self.polar, 3, 3)
    
    def test_spherical_vector_phi(self):
        with self.assertRaises(ValueError):
            LineSegment.from_point_length_angle(self.pt3d, self.spherical, 3)
    
    def test_spherical_vector_phi_theta(self):
        with self.assertRaises(ValueError):
            LineSegment.from_point_length_angle(self.pt3d, self.spherical, 3, 3)
    
    def test_length_no_phi(self):
        with self.assertRaises(ValueError):
            LineSegment.from_point_length_angle(self.pt2d, self.length)
    
    def test_dimension_mismatch_3to2(self):
        with self.assertRaises(ValueError):
            LineSegment.from_point_length_angle(self.pt3d, self.polar)
    
    def test_dimension_mismatch_2to3(self):
        with self.assertRaises(ValueError):
            LineSegment.from_point_length_angle(self.pt2d, self.spherical)

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
                assertPanCADAlmostEqual(
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

class TestLineSegmentFitBox(unittest.TestCase):
    
    def test_get_fit_box_2d(self):
        ls = LineSegment((0, 0), (1, -1))
        fitbox = ls.get_fit_box()
        expected = (Point(0, -1), Point(1, 0))
        for pt, exp in zip(fitbox, expected):
            assertPanCADAlmostEqual(self, pt, exp, ROUNDING_PLACES)
    
    def test_get_fit_box_3d(self):
        ls = LineSegment((0, 0, 0), (1, -1, 1))
        fitbox = ls.get_fit_box()
        expected = (Point(0, -1, 0), Point(1, 0, 1))
        for pt, exp in zip(fitbox, expected):
            assertPanCADAlmostEqual(self, pt, exp, ROUNDING_PLACES)

class TestLineSegmentUpdate(unittest.TestCase):
    
    def test_update(self):
        ls = LineSegment((0, 0, 0), (1, 0, 0))
        new = LineSegment((1, 1, 1), (2, 2, 2))
        ls.update(new)
        assertPanCADAlmostEqual(self, ls, new, ROUNDING_PLACES)

if __name__ == "__main__":
    unittest.main()