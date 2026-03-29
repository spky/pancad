"""Tests for pancad's Line class"""
from __future__ import annotations

import itertools
import math
from math import cos, sin, radians
import unittest

import numpy as np
import quaternion # pylint: disable=unused-import
import pytest

from pancad.utils import trigonometry as trig
from pancad.geometry import spatial_relations
from pancad.geometry.point import Point
from pancad.geometry.line import Line, Axis
from pancad.utils import verification

ROUNDING_PLACES = 10

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
                self.assertTrue(line.is_equal(expected_line))

    def test_from_point_and_angle(self):
        for (_, pt), phi in self.line_pts_to_phi:
            with self.subTest(point=pt,
                              phi=(f"Radians: {phi}, "
                              + f"Degrees: {math.degrees(phi)}")):
                expected_direction = trig.polar_to_cartesian((1, phi))
                expected_line = Line(pt, expected_direction)
                line = Line.from_point_and_angle(pt, phi)
                self.assertTrue(line.is_equal(expected_line))

class TestLineUpdate(unittest.TestCase):

    def test_update(self):
        line = Line(Point(0, 0, 0), (1, 0, 0))
        new = Line(Point(1, 1, 0), (1, 1, 1))
        line.update(new)
        self.assertTrue(line.is_equal(new))

ORIGIN_2D = (0, 0) # 2D Origin Point
ORIGIN_3D = (0, 0, 0) # 3D Origin Point
X_2D = (1, 0) # 2D X Axis Vector
Y_2D = (0, 1) # 2D Y Axis Vector
X_3D = (1, 0, 0) # 3D X Axis Vector
Y_3D = (0, 1, 0) # 3D Y Axis Vector
Z_3D = (0, 0, 1) # 3D Z Axis Vector
SQ2R = 1 / np.sqrt(2) # 1 over the square root of 2
# NOTE: Manual test input angles in degrees

QUAT_ROTATIONS = [
    # Init Point, Initial Direction, Rotation Axis Vector, Rotation Angle, Expected, Id Prefix
    (ORIGIN_3D, X_3D, (0, 0, 0), 0, X_3D, "q_unrotated_x_zero_axis"),
    (ORIGIN_3D, X_3D, (1, 0, 0), 0, X_3D, "q_unrotated_x_axis"),
    (ORIGIN_3D, X_3D, (1, 0, 0), 90, X_3D, "q_rotate_x_around_x"),
    (ORIGIN_3D, X_3D, (0, 1, 0), 90, (0, 0, -1), "q_rotate_x_to_-z"),
    (ORIGIN_3D, X_3D, (0, 1, 0), -90, Z_3D, "q_rotate_x_to_+z"),
    (ORIGIN_3D, X_3D, (0, 1, 0), 270, Z_3D, "q_opposite_rotate_x_to_+z"),
    (ORIGIN_3D, X_3D, (0, 1, 0), 180, (-1, 0, 0), "q_rotate_x_to_-x"),
    (ORIGIN_3D, X_3D, (0, 1, 0), 135, (-SQ2R, 0, -SQ2R), "q_rotate_x_135_around_y"),
    (ORIGIN_3D, Z_3D, (0, 1, 0), 135, (SQ2R, 0, -SQ2R), "q_rotate_z_135_around_y"),
]

MATRIX_2D_ROTATIONS = [
    # Init Point, Initial Direction, Rotation Angle
    (ORIGIN_2D, X_2D, 0, X_2D, "rm2_unrotated_x_axis"),
    (ORIGIN_2D, X_2D, 90, Y_2D, "rm2_rotate_x_to_+y"),
    (ORIGIN_2D, X_2D, 180, (-1, 0), "rm2_rotate_x_to_-x"),
]

MATRIX_3D_ROTATIONS = [
    # Init Point, Initial Direction, (Yaw (Z), Pitch (X), Roll (Y)), expected, Id Prefix
    (ORIGIN_3D, X_3D, (0, 0, 0), (1, 0, 0), "rm3_unrotated_x_axis"),
    (ORIGIN_3D, X_3D, (90, 0, 0), Y_3D, "rm3_rotate_x_to_+y"),
]

def _quaternion_params(rotations):
    """Generates the list of pytest parameters for testing quaternion rotation."""
    params = []
    for point, initial, rotation_axis, angle, expected, id_ in rotations:
        quat_w = cos(radians(angle / 2))
        quat_ijk = map(lambda x, y: x * sin(radians(y) / 2),
                       rotation_axis, itertools.repeat(angle))
        quat = np.quaternion(quat_w, *quat_ijk)
        test_id = "_".join([id_, str(angle), str(rotation_axis), str(expected)])
        param = pytest.param(point, initial, quat, expected, id=test_id)
        params.append(param)
    return params

def _2d_rotation_params(rotations):
    """Generates the list of pytest parameters for testing 2D rotation matrix rotations."""
    params = []
    for point, initial, angle, expected, id_ in rotations:
        matrix = trig.rotation_2(radians(angle))
        test_id = "_".join([id_, str(angle), str(expected)])
        param = pytest.param(point, initial, matrix, expected, id=test_id)
        params.append(param)
    return params

def _3d_rotation_params(rotations):
    """Generates the list of pytest parameters for testing 3D rotation matrix rotations."""
    params = []
    for point, initial, angles, expected, id_ in rotations:
        matrix = trig.yaw_pitch_roll(*map(radians, angles))
        test_id = "_".join([id_, str(angles), str(expected)])
        param = pytest.param(point, initial, matrix, expected, id=test_id)
        params.append(param)
    return params

@pytest.mark.parametrize(
    "point, initial, rotation, expected",
    [
        *_quaternion_params(QUAT_ROTATIONS),
        *_3d_rotation_params(MATRIX_3D_ROTATIONS),
        *_2d_rotation_params(MATRIX_2D_ROTATIONS),
    ]
)
def test_rotate_axis(point, initial, rotation, expected):
    """Tests for Axis rotation with quaternions and rotation matrices.

    :param point: Axis definition point.
    :param initial: Initial axis direction.
    :param rotation: A quaternion or rotation matrix.
    :param expected: Expected axis direction result.
    """
    axis = Axis(point, initial)
    rotated = axis.rotate(rotation).direction
    print(axis, rotated)
    assert np.allclose(rotated, expected)

@pytest.mark.parametrize(
    "point, direction, rotation, msg",
    [
        pytest.param(ORIGIN_2D, X_2D, np.quaternion(1, 0, 0, 0), "Cannot rotate 2D", id="2d_quat"),
        pytest.param(ORIGIN_2D, X_2D, np.identity(3), "D Axis with ", id="2d@3d_matrix"),
        pytest.param(ORIGIN_3D, X_3D, np.identity(2), "D Axis with ", id="3d@2d_matrix"),
    ]
)
def test_rotate_axis_exceptions(point, direction, rotation, msg):
    """Tests for handling axis rotation errors."""
    axis = Axis(point, direction)
    with pytest.raises(ValueError, match=msg):
        axis.rotate(rotation)

if __name__ == "__main__":
    unittest.main()
