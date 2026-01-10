from itertools import combinations_with_replacement
import unittest
import pytest
from math import radians, sqrt, cos, sin

import numpy as np
import quaternion

from pancad.geometry.point import Point
from pancad.geometry.coordinate_system import CoordinateSystem, SystemParts
from pancad.geometry.line import Line
from pancad.geometry.plane import Plane
from pancad.utils.verification import assertPancadAlmostEqual
from pancad.utils.trigonometry import (
    rotation_x, rotation_y, rotation_z, rotation_2, yaw_pitch_roll
)

ROUNDING_PLACES = 10

@pytest.fixture
def parts_2d_canon():
    origin = Point(0, 0)
    return SystemParts(origin, Line(origin, (1, 0)), Line(origin, (0, 1)))

@pytest.fixture
def parts_3d_canon():
    origin = Point(0, 0, 0)
    directions = [(1, 0, 0), (0, 1, 0), (0, 0, 1)]
    lines = [Line(origin, direction) for direction in directions]
    planes = [Plane(origin, direction) for direction in reversed(directions)]
    return SystemParts(origin, *lines, *planes)

@pytest.mark.parametrize("parts", [("parts_2d_canon"), ("parts_3d_canon")])
def test_system_parts_init(parts, request):
    request.getfixturevalue(parts)

rotation_2d_tests = []
for angle in range(0, 405, 45):
    vector = (cos(radians(angle)), sin(radians(angle)))
    rotation_2d_tests.append(("parts_2d_canon", angle, vector))
del angle, vector

@pytest.mark.parametrize("parts,angle,expected_x_axis", rotation_2d_tests)
def test_system_parts_rotation_2d(parts, angle, expected_x_axis, request):
    if angle in [180, 225, 270, 315]:
        pytest.xfail("Failing due to lack of Axis vs Line implementation")
    system_parts = request.getfixturevalue(parts)
    matrix = rotation_2(radians(angle))
    assert system_parts.rotate(matrix).x.direction == expected_x_axis

rotation_3d_tests = []
for angles in combinations_with_replacement(range(0, 405, 45), 3):
    rotation_3d_tests.append(("parts_3d_canon", angles, None))
del angles

@pytest.mark.parametrize("parts,ypr_angles,expected", rotation_3d_tests)
def test_system_parts_rotation_3d(parts, ypr_angles, expected, request):
    # TODO: Add expected conditions to this test as part of Axis implementation
    system_parts = request.getfixturevalue(parts)
    matrix = yaw_pitch_roll(*map(radians, ypr_angles))
    system_parts.rotate(matrix)

class TestCSInit(unittest.TestCase):
    def test_point_init_2d(self):
        pt = Point(0, 0)
        cs = CoordinateSystem(pt)
        expected = ((1, 0), (0, 1))
        self.assertCountEqual(cs.get_axis_vectors(), expected)
    
    def test_point_init_3d(self):
        pt = Point(0, 0, 0)
        cs = CoordinateSystem(pt)
        expected = ((1, 0, 0), (0, 1, 0), (0, 0, 1))
        self.assertEqual(cs.get_axis_vectors(), expected)
    
    def test_point_angle_init_2d(self):
        pytest.xfail("Failing due to lack of Axis vs Line implementation")
        pt = Point(0, 0)
        alpha = radians(90)
        cs = CoordinateSystem(pt, alpha)
        expected = ((0, 1), (-1, 0))
        for cs_axis, exp_axis in zip(cs.get_axis_vectors(), expected):
            assertPancadAlmostEqual(self, cs_axis, exp_axis, ROUNDING_PLACES)
    
    def test_point_angle_init_3d(self):
        pt = Point(0, 0, 0)
        alpha = radians(90)
        cs = CoordinateSystem(pt, alpha)
        expected = ((0, 1, 0), (-1, 0, 0), (0, 0, 1))
        for cs_axis, exp_axis in zip(cs.get_axis_vectors(), expected):
            assertPancadAlmostEqual(self, cs_axis, exp_axis, ROUNDING_PLACES)

class TestCSStringDunders(unittest.TestCase):
    
    def setUp(self):
        pt = Point(0, 0, 0)
        self.cs = CoordinateSystem(pt)
    
    def test_str(self):
        result = str(self.cs)
    
    def test_repr(self):
        result = repr(self.cs)

class TestCSReferenceGeometry(unittest.TestCase):
    
    def setUp(self):
        self.pt = Point(0, 0, 0)
        self.cs = CoordinateSystem(self.pt)
    
    def test_axis_lines(self):
        lines = [
            self.cs.get_axis_line_x(),
            self.cs.get_axis_line_y(),
            self.cs.get_axis_line_z(),
        ]
        expected = [
            Line(self.pt, (1, 0, 0)),
            Line(self.pt, (0, 1, 0)),
            Line(self.pt, (0, 0, 1)),
        ]
        for cs_line, exp in zip(lines, expected):
            with self.subTest(coordinate_sys_line=cs_line, expected=exp):
                assertPancadAlmostEqual(self, cs_line, exp, ROUNDING_PLACES)
    
    def test_planes(self):
        planes = [
            self.cs.get_xy_plane(),
            self.cs.get_xz_plane(),
            self.cs.get_yz_plane(),
        ]
        expected = [
            Plane(self.pt, (0, 0, 1)),
            Plane(self.pt, (0, 1, 0)),
            Plane(self.pt, (1, 0, 0)),
        ]
        for cs_plane, exp in zip(planes, expected):
            with self.subTest(coordinate_sys_line=cs_plane, expected=exp):
                assertPancadAlmostEqual(self, cs_plane, exp, ROUNDING_PLACES)

class TestCSUpdate(unittest.TestCase):
    
    def test_update(self):
        cs = CoordinateSystem((0, 0, 0))
        new = CoordinateSystem((2, 2, 2), radians(45), radians(45), radians(45))
        cs.update(new)
        assertPancadAlmostEqual(self, cs, new, ROUNDING_PLACES)

class TestCSWithQuaternions(unittest.TestCase):
    
    def setUp(self):
        self.pt = Point(0, 0, 0)
        self.angle = radians(90)
        self.rotation_matrix = rotation_z(self.angle)
        self.quat = quaternion.from_rotation_matrix(self.rotation_matrix)
    
    def test_from_quaternion(self):
        cs = CoordinateSystem.from_quaternion(self.pt, self.quat)
        expected = [[0, 1, 0],
                    [-1, 0, 0],
                    [0, 0, 1]]
        np.testing.assert_allclose(cs.get_axis_vectors(), expected, atol=1e-10)
    
    def test_get_quaternion(self):
        cs = CoordinateSystem.from_quaternion(self.pt, self.quat)
        quat = cs.get_quaternion()

if __name__ == "__main__":
    unittest.main()