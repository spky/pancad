import unittest
from math import radians

import numpy as np
import quaternion

from PanCAD.geometry import CoordinateSystem, Point, Line, Plane
from PanCAD.utils.verification import assertPanCADAlmostEqual
from PanCAD.utils.trigonometry import rotation_x, rotation_y, rotation_z

ROUNDING_PLACES = 10

class TestCSInit(unittest.TestCase):
    def test_point_init_2d(self):
        pt = Point(0, 0)
        cs = CoordinateSystem(pt)
        expected = ((1, 0), (0, 1))
        self.assertEqual(cs.get_axis_vectors(), expected)
    
    def test_point_init_3d(self):
        pt = Point(0, 0, 0)
        cs = CoordinateSystem(pt)
        expected = ((1, 0, 0), (0, 1, 0), (0, 0, 1))
        self.assertEqual(cs.get_axis_vectors(), expected)
    
    def test_point_angle_init_2d(self):
        pt = Point(0, 0)
        alpha = radians(90)
        cs = CoordinateSystem(pt, alpha)
        expected = ((0, 1), (-1, 0))
        for cs_axis, exp_axis in zip(cs.get_axis_vectors(), expected):
            assertPanCADAlmostEqual(self, cs_axis, exp_axis, ROUNDING_PLACES)
    
    def test_point_angle_init_3d(self):
        pt = Point(0, 0, 0)
        alpha = radians(90)
        cs = CoordinateSystem(pt, alpha)
        expected = ((0, 1, 0), (-1, 0, 0), (0, 0, 1))
        for cs_axis, exp_axis in zip(cs.get_axis_vectors(), expected):
            assertPanCADAlmostEqual(self, cs_axis, exp_axis, ROUNDING_PLACES)

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
                assertPanCADAlmostEqual(self, cs_line, exp, ROUNDING_PLACES)
    
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
                assertPanCADAlmostEqual(self, cs_plane, exp, ROUNDING_PLACES)

class TestCSUpdate(unittest.TestCase):
    
    def test_update(self):
        cs = CoordinateSystem((0, 0, 0))
        new = CoordinateSystem((2, 2, 2), radians(45), radians(45), radians(45))
        cs.update(new)
        assertPanCADAlmostEqual(self, cs, new, ROUNDING_PLACES)

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
        print(self.quat)
        np.testing.assert_allclose(cs.get_axis_vectors(), expected, atol=1e-10)
    
    def test_get_quaternion(self):
        cs = CoordinateSystem.from_quaternion(self.pt, self.quat)
        quat = cs.get_quaternion()
        print(quat)

if __name__ == "__main__":
    unittest.main()