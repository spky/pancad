"""Tests for pancad's Line class"""
from __future__ import annotations

import itertools
import math
import unittest
from typing import TYPE_CHECKING

import numpy as np
import pytest

from pancad.utils import trigonometry as trig
from pancad.geometry import spatial_relations
from pancad.geometry.point import Point
from pancad.geometry.line import Line
from pancad.utils import verification

if TYPE_CHECKING:
    from pancad.utils.pancad_types import VectorLike

ROUNDING_PLACES = 10

# Test id abbreviations:
# pt=point, vec=vector, para=parallel, perp=perpendicular, dir=direction
# cw=clockwise, ccw=counter-clockwise, ul=upper left, br=bottom_right
@pytest.mark.parametrize(
    "point, direction, expected",
    [ # Comment summarizes the expected results
        # The origin because origin is provided.
        pytest.param((0, 0), (1, 0), (0, 0), id="2d_origin"),
        pytest.param((0, 0, 0), (1, 0, 0), (0, 0, 0), id="3d_origin"),
        # The origin because the point is parallel to the direction vector
        pytest.param((2, 0), (1, 0), (0, 0), id="2d_pt_vec_para"),
        # The provided point because the point vector and direction
        # are perpendicular.
        pytest.param((1, 1), (-1, 1), (1, 1), id="2d_pt_vec_perp"),
        # Point is cw/ccw of closest point, direction is pointing ul/br:
        pytest.param((2, 0), (-1, 1), (1, 1), id="2d_cw_pt_ul_dir"),
        pytest.param((2, 0), (1, -1), (1, 1), id="2d_cw_pt_br_dir"),
        pytest.param((0, 2), (-1, 1), (1, 1), id="2d_ccw_pt_br_dir"),
        pytest.param((0, 2), (1, -1), (1, 1), id="2d_ccw_pt_br_dir"),
    ],
)
def test_closest_to_origin(point, direction, expected):
    """Test function for finding the point on a line closest to the origin."""
    result = Line.closest_to_origin(point, direction)
    np.testing.assert_array_almost_equal(np.array(result), np.array(expected))

ZERO_VEC_MSG_RE = r"^Got zero vector for line"
DIM_MISMATCH_RE = r"dimensions are not equal$"
@pytest.mark.parametrize(
    "point, direction, msg",
    [
        pytest.param((0, 0), (0, 0), ZERO_VEC_MSG_RE, id="pt0,0_zero_vec"),
        pytest.param((0, 0, 0), (0, 0, 0), ZERO_VEC_MSG_RE, id="pt0,0,0_zero_vec"),
        pytest.param((1, 1), (0, 0), ZERO_VEC_MSG_RE, id="pt1,1_zero_vec"),
        pytest.param((1, 1, 1), (0, 0, 0), ZERO_VEC_MSG_RE, id="pt1,1,1_zero_vec"),
        pytest.param((0, 0), (1, 0, 0), DIM_MISMATCH_RE, id="2d_pt_3d_vec"),
        pytest.param((0, 0, 0), (1, 0), DIM_MISMATCH_RE, id="3d_pt_2d_vec"),
    ]
)
def test_closest_to_origin_excs(point, direction, msg):
    """Test that the closest_to_origin function produces relevant exceptions."""
    with pytest.raises(ValueError, match=msg):
        Line.closest_to_origin(point, direction)

# id abbreviations: uv=unit vector
@pytest.mark.parametrize(
    "direction, expected",
    [
        # Zero Vector Tests
        ## 2D Tests ##
        # Positive Unit Vector
        pytest.param((1, 0), (1, 0), id="1,0"),
        pytest.param((0, 1), (0, 1), id="0,1"),
        # Negative Unit Vector
        pytest.param((-1, 0), (1, 0), id="-1,0to1,0"),
        pytest.param((0, -1), (0, 1), id="0,-1to0,1"),
        # 2 Direction Positive and Negative
        pytest.param((1, 1), trig.get_unit_vector(np.array((1, 1))), id="1,1uv"),
        pytest.param((-1, -1), trig.get_unit_vector(np.array((1, 1))), id="-1,-1uv"),
        ## 3D Tests ##
        # Positive Unit Vector
        pytest.param((1, 0, 0), (1, 0, 0), id="1,0,0"),
        pytest.param((0, 1, 0), (0, 1, 0), id="0,1,0"),
        pytest.param((0, 0, 1), (0, 0, 1), id="0,0,1"),
        # Negative Unit Vector
        pytest.param((-1, 0, 0), (1, 0, 0), id="-1,0,0to1,0,0"),
        pytest.param((0, -1, 0), (0, 1, 0), id="0,-1,0to0,1,0"),
        pytest.param((0, 0, -1), (0, 0, 1), id="0,0,-1to0,0,1"),
        # 2 Direction Positive
        pytest.param((1, 1, 0), trig.get_unit_vector(np.array((1,1,0))), id="1,1,0uv"),
        pytest.param((0, 1, 1), trig.get_unit_vector(np.array((0,1,1))), id="0,1,1uv"),
        # 2 Direction Negative
        pytest.param((-1, -1, 0), trig.get_unit_vector(np.array((1,1,0))), id="-1,-1,0uv"),
        pytest.param((0, -1, -1), trig.get_unit_vector(np.array((0, 1, 1))), id="0,-1,-1uv"),
        # 3 Direction Positive and Negative
        pytest.param((1, 1, 1), trig.get_unit_vector(np.array((1,1,1))), id="1,1,1uv"),
        pytest.param((-1, -1, -1), trig.get_unit_vector(np.array([1,1,1])), id="-1,-1,-1uv"),
    ]
)
def test_line_unique_direction(direction, expected):
    """Test that Line's direction is correctly translated to a unique vector."""
    point = Point([0] * len(direction))
    line = Line(point, direction)
    np.testing.assert_array_almost_equal(line.direction, expected)

class TestLineInit(unittest.TestCase):

    def setUp(self):
        self.pt_a = Point((1,0,0))
        self.pt_b = Point((1,10,0))

    def test_line_init_no_arg(self):
        l = Line()

    def test_line_len_dunder(self):
        tests = [
            ((0, 0), (1, 1), 2),
            ((0, 0, 0), (1, 1, 1), 3),
        ]
        for pt_a, pt_b, length in tests:
            with self.subTest(point_a=pt_a, point_b=pt_b,
                              expected_length=length):
                point_1, point_2 = Point(pt_a), Point(pt_b)
                test_line = Line.from_two_points(point_1, point_2)
                self.assertEqual(len(test_line), length)

    def test_line_str_dunder(self):
        test = Line.from_two_points(self.pt_a, self.pt_b)
        self.assertEqual(str(test), "<Line(1,0,0)(0,1,0)>")

class TestLineTwoPointDefinition(unittest.TestCase):

    def setUp(self):
        # Point A, Point B, Expected Point Closest to Origin,
        # Vector in Expected Direction (subsequently converted to unit vector)
        self.tests = [
            # Set 1: Diagonal Off-Origin
            ((0, 4), (4, 0), (2, 2), (-1, 1)),
            ((0, 4), (-4, 0), (-2, 2), (1, 1)),
            ((0, -4), (-4, 0), (-2, -2), (-1, 1)),
            ((0, -4), (4, 0), (2, -2), (1, 1)),
            # Set 2: Vertical +, -, and 0
            ((2, 0), (2, 2), (2, 0), (0, 1)),
            ((-2, 0), (-2, 2), (-2, 0), (0, 1)),
            ((0, 0), (0, 2), (0, 0), (0, 1)),
            # Set 3: Horizontal +, -, and 0
            ((0, 2), (2, 2), (0, 2), (1, 0)),
            ((0, 1), (1, 1), (0, 1), (1, 0)),
            ((0, -2), (2, -2), (0, -2), (1, 0)),
            ((0, 0), (2, 0), (0, 0), (1, 0)),
            # Set 4: Diagonal On-Origin Per Quadrant
            ((1, 1), (2, 2), (0, 0), (1, 1)),
            ((-1, 1), (-2, 2), (0, 0), (-1, 1)),
            ((-1, -1), (-2, -2), (0, 0), (1, 1)),
            ((1, -1), (2, -2), (0, 0), (-1, 1)),
            # Set 5: Diagonal On-Origin Across Quadrant
            ((-1, -1), (1, 1), (0, 0), (1, 1)),
            ((-1, 1), (1, -1), (0, 0), (-1, 1)),
            # Set 6: Horizontal/Vertical On-Origin Across Quadrant
            ((-1, 0), (1, 0), (0, 0), (1, 0)),
            ((0, -1), (0, 1), (0, 0), (0, 1)),
        ]
        for i, (pt_a, pt_b, e_pt, vector) in enumerate(self.tests):
            # Convert expected direction to unit vector
            np_vector = trig.to_1d_np(vector)
            unit_vector = trig.get_unit_vector(np_vector)
            self.tests[i] = (pt_a, pt_b, e_pt, trig.to_1d_tuple(unit_vector))

    def test_from_two_points_point_closest_to_origin(self):
        for point_a, point_b, expected_point, _ in self.tests:
            with self.subTest(point_a=point_a, point_b=point_b,
                              expected_point=expected_point):
                pt_a, pt_b = Point(point_a), Point(point_b)
                e_pt = Point(expected_point)
                test_line = Line.from_two_points(pt_a, pt_b)
                verification.assertPointsAlmostEqual(
                    self, test_line._point_closest_to_origin, e_pt,
                    ROUNDING_PLACES
                )

    def test_from_two_points_point_closest_to_origin_tuple(self):
        for point_a, point_b, expected_point, _ in self.tests:
            with self.subTest(point_a=point_a, point_b=point_b,
                              expected_point=expected_point):
                e_pt = Point(expected_point)
                test_line = Line.from_two_points(point_a, point_b)
                verification.assertPointsAlmostEqual(
                    self, test_line._point_closest_to_origin, e_pt,
                    ROUNDING_PLACES
                )

    def test_from_two_points_direction(self):
        for point_a, point_b, _, expected_direction in self.tests:
            with self.subTest(point_a=point_a, point_b=point_b,
                              expected_direction=expected_direction):
                pt_a, pt_b = Point(point_a), Point(point_b)
                test_line = Line.from_two_points(pt_a, pt_b)
                verification.assertTupleAlmostEqual(
                    self, test_line.direction, expected_direction,
                    ROUNDING_PLACES
                )

    def test_from_two_points_direction_tuple(self):
        for point_a, point_b, _, expected_direction in self.tests:
            with self.subTest(point_a=point_a, point_b=point_b,
                              expected_direction=expected_direction):
                test_line = Line.from_two_points(point_a, point_b)
                verification.assertTupleAlmostEqual(
                    self, test_line.direction, expected_direction,
                    ROUNDING_PLACES
                )

    def test_from_two_points_same_point(self):
        pt_a = Point((1, 1))
        pt_b = Point((1, 1))
        with self.assertRaises(ValueError):
            test_line = Line.from_two_points(pt_a, pt_b)

class TestEquationLineDefinitions(unittest.TestCase):

    def setUp(self):
        # Slope (m), Y-Intercept (b), Expected Point, Expected Direction
        self.tests = [
            (0, 0, (0, 0), (1, 0)),
            (1, 0, (0, 0), (1, 1)),
            (-1, 0, (0, 0), (-1, 1)),
            (-1, 4, (2, 2), (-1, 1)),
        ]
        for i, (m, b, pt, direction) in enumerate(self.tests):
            self.tests[i] = (m, b, Point(pt), trig.get_unit_vector(direction))

    def test_from_slope_and_y_intercept_expected_point(self):
        for m, b, pt, direction in self.tests:
            with self.subTest(slope=m, intercept=b,
                              expected_closest_to_origin_point=pt):
                test_line = Line.from_slope_and_y_intercept(m, b)
                verification.assertPointsAlmostEqual(
                    self, test_line._point_closest_to_origin, pt,
                    ROUNDING_PLACES
                )

    def test_from_slope_and_y_intercept_expected_direction(self):
        for m, b, pt, direction in self.tests:
            with self.subTest(slope=m, intercept=b,
                              expected_direction=direction):
                test_line = Line.from_slope_and_y_intercept(m, b)
                verification.assertTupleAlmostEqual(
                    self, test_line.direction, direction, ROUNDING_PLACES
                )

    def test_slope_getter_non_nan(self):
        for m, b, pt, direction in self.tests:
            with self.subTest(slope=m, intercept=b):
                test_line = Line.from_slope_and_y_intercept(m, b)
                self.assertEqual(test_line.slope, m)

    def test_y_intercept_getter_non_nan(self):
        for m, b, pt, direction in self.tests:
            with self.subTest(slope=m, intercept=b):
                test_line = Line.from_slope_and_y_intercept(m, b)
                self.assertEqual(test_line.y_intercept, b)

class TestLineCoordinateSystemConversion(unittest.TestCase):

    def setUp(self):
        """
        Test Order:
            Point A, Point B, Phi (Azimuth) Angle, Theta (Inclination) Angle
        Angles get converted to radians prior to test
        r separately defined for legibility since for line direction unit
        vectors it will always be 1.
        """
        tests = [
            ((0, 0, 0), (1, 0, 0), (1, 0, 90)),
            ((0, 0, 0), (0, 1, 0), (1, 90, 90)),
            ((0, 0, 0), (0, 0, 1), (1, math.nan, 0)),
        ]
        self.tests_2d, self.tests_3d = [], []
        for pt_a, pt_b, (r, phi, theta) in tests:
            self.tests_3d.append(
                (
                    Point(pt_a), Point(pt_b),
                    (r, math.radians(phi), math.radians(theta)),
                )
            )
            if pt_a[:2] != pt_b[:2]: # To deal with when x = y = 0 and z != 0
                self.tests_2d.append(
                    (Point(pt_a[:2]), Point(pt_b[:2]), (r, math.radians(phi)))
                )

    def test_direction_polar(self):
        for pt_a, pt_b, (r, phi) in self.tests_2d:
            with self.subTest(
                        point_a=tuple(pt_a), point_b=tuple(pt_b),
                        expected_phi=(f"Radians: {phi},"
                                     + f" Degrees: {math.degrees(phi)}")
                    ):
                test_line = Line.from_two_points(pt_a, pt_b)
                verification.assertTupleAlmostEqual(
                    self, test_line.direction_polar, (r, phi),
                    ROUNDING_PLACES
                )

    def test_direction_spherical(self):
        for pt_a, pt_b, (r, phi, theta) in self.tests_3d:
            with self.subTest(
                    point_a=tuple(pt_a), point_b=tuple(pt_b),
                    expected_phi=(f"Radians: {phi},"
                                 + f" Degrees: {math.degrees(phi)}"),
                    expected_theta=(f"Radians: {theta},"
                                    + f" Degrees: {math.degrees(theta)}")
                    ):
                test_line = Line.from_two_points(pt_a, pt_b)
                verification.assertTupleAlmostEqual(
                    self, test_line.direction_spherical, (r, phi, theta),
                    ROUNDING_PLACES
                )

    def test_direction_polar_setter(self):
        for pt_a, pt_b, polar_vector in self.tests_2d:
            with self.subTest(
                        point_a=tuple(pt_a), point_b=tuple(pt_b),
                        polar_vector=polar_vector
                    ):
                test_line = Line.from_two_points(pt_a, pt_b)
                before_direction = test_line.direction
                test_line.direction_polar = polar_vector
                verification.assertTupleAlmostEqual(
                    self, before_direction, test_line.direction,
                    ROUNDING_PLACES
                )

    def test_direction_spherical_setter(self):
        for pt_a, pt_b, spherical_vector in self.tests_3d:
            with self.subTest(
                        point_a=tuple(pt_a), point_b=tuple(pt_b),
                        spherical_vector=spherical_vector
                    ):
                test_line = Line.from_two_points(pt_a, pt_b)
                before_direction = test_line.direction
                test_line.direction_spherical = spherical_vector
                verification.assertTupleAlmostEqual(
                    self, before_direction, test_line.direction,
                    ROUNDING_PLACES
                )

class TestLineRichComparison(unittest.TestCase):

    def setUp(self):
        self.tests = [
            ((0, 0), (1, 1), (0, 0), (1, 1), True),
            ((1, 0), (1, 1), (0, 0), (1, 1), False),
            ((0, 0, 0), (1, 1, 1), (0, 0, 0), (1, 1, 1), True),
            ((1, 0, 0), (1, 1, 0), (0, 0, 0), (1, 1, 0), False),
        ]
        for i, (pt1a, pt1b, pt2a, pt2b, equality) in enumerate(self.tests):
            self.tests[i] = (Point(pt1a), Point(pt1b),
                             Point(pt2a), Point(pt2b),
                             equality)

    def test_line_equality(self):
        for pt1a, pt1b, pt2a, pt2b, expected_equality in self.tests:
            with self.subTest(point1a=tuple(pt1a), point1b=tuple(pt1b),
                              point2a=tuple(pt2a), point2b=tuple(pt2b),
                              expected_equality=expected_equality):
                line1 = Line.from_two_points(pt1a, pt1b)
                line2 = Line.from_two_points(pt2a, pt2b)
                self.assertEqual(line1 == line2, expected_equality)

    def test_line_inequality(self):
        for pt1a, pt1b, pt2a, pt2b, expected_equality in self.tests:
            with self.subTest(point1a=tuple(pt1a), point1b=tuple(pt1b),
                              point2a=tuple(pt2a), point2b=tuple(pt2b),
                              expected_equality= not expected_equality):
                line1 = Line.from_two_points(pt1a, pt1b)
                line2 = Line.from_two_points(pt2a, pt2b)
                self.assertEqual(line1 != line2, not expected_equality)

class TestLinePointMovers2D(unittest.TestCase):

    def setUp(self):
        lines = [
            ((0, 1), (1, 1)),
            ((0, 1), (1, 1)),
            ((-4, 0), (0, 4)),
        ]
        self.lines = [Line.from_two_points(p1, p2) for p1, p2 in lines]
        new_points = [
            (0, 2),
            (3, 3),
        ]
        self.new_points = list(map(Point, new_points))
        self.line_to_pts = []
        for line in self.lines:
            line_cases = zip(itertools.repeat(line, len(self.new_points)),
                             self.new_points)
            self.line_to_pts.extend(list(line_cases))

        phis = [
            0,
            45,
            90,
            135,
            -90,
            -135,
            180,
            -180,
        ]
        self.phis = list(map(math.radians, phis))
        self.line_pts_to_phi = []
        for line in self.line_to_pts:
            cases = zip(itertools.repeat(line, len(self.phis)),
                        self.phis)
            self.line_pts_to_phi.extend(list(cases))

    def test_move_to_point(self):
        for line, new_pt in self.line_to_pts:
            with self.subTest(line=line, point=new_pt):
                test_line = line.copy()
                test_line.move_to_point(new_pt)
                results = [
                    spatial_relations.coincident(test_line, new_pt),
                    spatial_relations.parallel(test_line, line)
                ]
                self.assertTrue(all(results))

    def test_move_to_point_phi(self):
        for (line, new_pt), new_phi in self.line_pts_to_phi:
            with self.subTest(line=line, point=new_pt,
                              phi=(f"Radians: {new_phi}, "
                                   + f"Degrees: {math.degrees(new_phi)}")):
                expected_direction = trig.polar_to_cartesian((1, new_phi))
                expected_line = Line(new_pt, expected_direction)
                line.move_to_point(new_pt, new_phi)
                self.assertEqual(expected_line, line)

    def test_from_point_and_angle(self):
        for (_, pt), phi in self.line_pts_to_phi:
            with self.subTest(point=pt,
                              phi=(f"Radians: {phi}, "
                              + f"Degrees: {math.degrees(phi)}")):
                expected_direction = trig.polar_to_cartesian((1, phi))
                expected_line = Line(pt, expected_direction)
                line = Line.from_point_and_angle(pt, phi)
                self.assertEqual(expected_line, line)

class TestLineUpdate(unittest.TestCase):

    def test_update(self):
        line = Line(Point(0, 0, 0), (1, 0, 0))
        new = Line(Point(1, 1, 0), (1, 1, 1))
        line.update(new)
        verification.assertPancadAlmostEqual(self, line, new, ROUNDING_PLACES)

if __name__ == "__main__":
    unittest.main()
