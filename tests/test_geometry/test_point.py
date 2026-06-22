"""Tests for the pancad Point class."""
from __future__ import annotations

import unittest
import math
from math import radians, nan, sqrt, pi, hypot, atan, degrees
from typing import TYPE_CHECKING

import numpy as np
import pytest

from pancad.geometry.point import Point
from pancad.utils.pancad_types import PolarVector, SphericalVector

if TYPE_CHECKING:
    from pancad.utils.pancad_types import SpaceVector, Numpy1D, Space2DVector, Space3DVector

@pytest.mark.parametrize("coordinate", [(0, 0, 0), (1, 1, 1), (1, 1)])
class TestPointInitialization:
    """Tests for initializing a Point and all basic functionality that can be tested with no
    further changes right after initialization.
    """

    def test_tuple_init(self, coordinate: SpaceVector) -> None:
        """Tests Point can initialize with a tuple."""
        assert Point(coordinate).cartesian == coordinate

    def test_list_init(self, coordinate: SpaceVector) -> None:
        """Tests Point can initialize with a list."""
        assert Point(list(coordinate)).cartesian == coordinate

    def test_component_init(self, coordinate: SpaceVector) -> None:
        """Tests Point can initialize with individual components."""
        assert Point(*coordinate).cartesian == coordinate

    def test_numpy_init(self, coordinate: SpaceVector) -> None:
        """Tests Point can initialize with a numpy vector."""
        assert Point(np.array(coordinate, dtype=np.float64)).cartesian == coordinate

    def test_tuple_iter(self, coordinate: SpaceVector) -> None:
        """Test Point can be turned into a tuple of its components."""
        assert tuple(Point(coordinate)) == coordinate

    def test_numpy_array(self, coordinate: SpaceVector) -> None:
        """Test Point can be turned into a numpy array of its components."""
        np.testing.assert_array_equal(np.array(Point(coordinate)), coordinate)

    def test_len_dunder(self, coordinate: SpaceVector) -> None:
        """Test Point length matches the length of the vector used to initialize it."""
        assert len(Point(coordinate)) == len(coordinate)

    def test_str_dunder(self, coordinate: SpaceVector) -> None:
        """Test Point string dunder correctly reports the point location."""
        coord_str = ",".join(map(str, coordinate))
        assert str(Point(coordinate)) == f"<Point({coord_str})>"

    def test_cartesian_getters(self, coordinate: SpaceVector) -> None:
        """Test Point x, y, and z properties match the coordinate's x, y, and z components."""
        point = Point(coordinate)
        if len(coordinate) == 2:
            assert (point.x, point.y) == coordinate
        else:
            assert (point.x, point.y, point.z) == coordinate

    def test_getitem(self, coordinate: SpaceVector) -> None:
        """Test Point x, y, and z properties match the coordinate's x, y, and z components."""
        point = Point(coordinate)
        if len(coordinate) == 2:
            assert (point[0], point[1]) == coordinate
        else:
            assert (point[0], point[1], point[2]) == coordinate

    def test_horizontal_vector(self, coordinate: SpaceVector) -> None:
        """Test that Point can return a horizontal numpy array."""
        point = Point(coordinate)
        np.testing.assert_array_equal(point.vector(False), np.array(coordinate))

    def test_vertical_vector(self, coordinate: SpaceVector) -> None:
        """Test that Point can return a vertical numpy array."""
        point = Point(coordinate)
        np.testing.assert_array_equal(point.vector(True),
                                      np.array(coordinate).reshape(len(coordinate), 1))

@pytest.mark.parametrize("polar_coordinate", [(1, 0), (1, 45)])
class TestPolarPointInitialization:
    """Tests for how Point handles being initialized by a polar vector."""

    def test_from_polar_tuple(self, polar_coordinate: Space2DVector) -> None:
        """Test that a point can initialize from a polar vector as a tuple."""
        radius, phi = polar_coordinate
        coordinate_radians = (radius, radians(phi))
        assert Point.from_polar(coordinate_radians).polar == coordinate_radians

    def test_from_polar_polar_vector(self, polar_coordinate: Space2DVector) -> None:
        """Test that a point can initialize from a polar vector as a PolarVector."""
        radius, phi = polar_coordinate
        coordinate_radians = (radius, radians(phi))
        polar_vector = PolarVector(coordinate_radians)
        assert Point.from_polar(polar_vector).polar == coordinate_radians

    def test_from_polar_components(self, polar_coordinate: Space2DVector) -> None:
        """Test that a point can initialize from a polar vector as individual components."""
        radius, phi = polar_coordinate
        coordinate_radians = (radius, radians(phi))
        assert Point.from_polar(*coordinate_radians).polar == coordinate_radians

@pytest.mark.parametrize("spherical_coordinate", [(1, nan, 0), (1, 45, 90)])
class TestSphericalPointInitialization:
    """Tests for how Point handles being initialized by a spherical vector."""

    def test_from_spherical_tuple(self, spherical_coordinate: Space3DVector) -> None:
        """Test that a point can initialize from a spherical vector as a tuple."""
        radius, phi, theta = spherical_coordinate
        coordinate_radians = (radius, radians(phi), radians(theta))
        np.testing.assert_array_equal(Point.from_spherical(coordinate_radians).spherical,
                                      coordinate_radians)

    def test_from_spherical_spherical_vector(self, spherical_coordinate: Space3DVector) -> None:
        """Test that a point can initialize from a spherical vector as a SphericalVector."""
        radius, phi, theta = spherical_coordinate
        coordinate_radians = (radius, radians(phi), radians(theta))
        spherical_vector = SphericalVector(coordinate_radians)
        np.testing.assert_array_equal(Point.from_spherical(spherical_vector).spherical,
                                      coordinate_radians)

    def test_from_spherical_components(self, spherical_coordinate: Space3DVector) -> None:
        """Test that a point can initialize from a spherical vector as individual components."""
        radius, phi, theta = spherical_coordinate
        coordinate_radians = (radius, radians(phi), radians(theta))
        np.testing.assert_array_equal(Point.from_spherical(*coordinate_radians).spherical,
                                      coordinate_radians)

@pytest.mark.parametrize(
    "original, new",
    [
        ((0, 0), (0, 0)),
        ((0, 0), (1, 1)),
        ((0, 0, 0), (0, 0, 0)),
        ((0, 0, 0), (1, 1, 1)),
        ((1, 1, 1), (0, 0, 0)),
        ((0, 0, 0), (-1, -1, -1)),
        ((-1, -1, -1), (0, 0, 0)),
    ]
)
class TestPointCartesianUpdate:
    """Tests for updating a Point using a cartesian coordinate."""

    def test_with_tuple(self, original: SpaceVector, new: SpaceVector) -> None:
        """Test that Point's cartesian can be set with a tuple."""
        point = Point(original)
        point.cartesian = new
        assert point.cartesian == new

    def test_with_list(self, original: SpaceVector, new: SpaceVector) -> None:
        """Test that Point's cartesian can be set with a list."""
        point = Point(original)
        point.cartesian = list(new)
        assert point.cartesian == new

    def test_with_numpy(self, original: SpaceVector, new: SpaceVector) -> None:
        """Test that Point's cartesian can be set with a numpy array."""
        point = Point(original)
        point.cartesian = np.array(new)
        assert point.cartesian == new

    def test_with_components(self, original: SpaceVector, new: SpaceVector) -> None:
        """Test that each Point component can be set individually."""
        point = Point(original)
        point.x, point.y = new[0], new[1]
        if len(new) == 3:
            point.z = new[2]
        assert point.cartesian == new

    def test_with_other_point(self, original: SpaceVector, new: SpaceVector) -> None:
        """Test that Points can be updated using another point."""
        original_point, new_point = Point(original), Point(new)
        original_point.update(new_point)
        assert original_point.cartesian == new

@pytest.mark.parametrize(
    "cartesian, polar",
    [
        # Angles in degrees here
        ((0, 0), (0, nan)),
        ((1, 1), (sqrt(2), 45)),
        ((-1, 1), (sqrt(2), 135)),
        ((-1, -1), (sqrt(2), -135)),
        ((1, -1), (sqrt(2), -45)),
        ((1, 0), (1, 0)),
        ((0, 1), (1, 90)),
        ((-1, 0), (1, 180)),
        ((0, -1), (1, -90)),
    ]
)
class TestPointCartesianToPolarConversions:
    """Tests for Point converting cartesian coordinates to polar coordinates."""

    def test_polar_conversion(self, cartesian: Space2DVector, polar: Space2DVector) -> None:
        """Test Point can convert its cartesian components into polar components."""
        np.testing.assert_array_equal(Point(cartesian).polar, (polar[0], radians(polar[1])))

    def test_r_getter(self, cartesian: Space2DVector, polar: Space2DVector) -> None:
        """Test Point can return the radial Polar component."""
        assert Point(cartesian).r == polar[0]

    def test_phi_getter(self, cartesian: Space2DVector, polar: Space2DVector) -> None:
        """Test Point can return the phi (azimuth) Polar component."""
        np.testing.assert_equal(Point(cartesian).phi, radians(polar[1]))

    def test_polar_setter(self, cartesian: Space2DVector, polar: Space2DVector) -> None:
        """Test Point can update its cartesian parameters to match the polar components."""
        point = Point(cartesian)
        point.cartesian = (-10, -10) # First set it to a point that's not in the parameters
        polar_vector = (polar[0], radians(polar[1]))
        point.polar = polar_vector
        np.testing.assert_array_almost_equal(point.polar, polar_vector)
        np.testing.assert_array_almost_equal(point.cartesian, cartesian)

@pytest.mark.parametrize(
    "cartesian, spherical",
    [
        # Angles in degrees here
        # Polar-like tests first
        ((0, 0, 0), (0, nan, nan)),
        ((1, 1, 0), (sqrt(2), 45, 90)),
        ((-1, 1, 0), (sqrt(2), 135, 90)),
        ((-1, -1, 0), (sqrt(2), -135, 90)),
        ((1, -1, 0), (sqrt(2), -45, 90)),
        ((1, 0, 0), (1, 0, 90)),
        ((0, 1, 0), (1, 90, 90)),
        ((-1, 0, 0), (1, 180, 90)),
        ((0, -1, 0), (1, -90, 90)),
        # Non polar-like tests start here
        ((0, 0, -1), (1, nan, degrees(pi + atan(hypot(0, 0) / -1)))),
        ((1, 1, 1), (sqrt(3), 45, degrees(atan(hypot(1, 1) / 1)))),
        ((1, 1, -1), (sqrt(3), 45, degrees(pi + atan(hypot(1, 1) / -1)))),
    ]
)
class TestPointCartesianToSphericalConversions:
    """Tests for Point converting cartesian coordinates to spherical coordinates."""

    def test_conversion(self, cartesian: Space3DVector, spherical: Space3DVector) -> None:
        """Test Point can convert its cartesian components into spherical components."""
        np.testing.assert_array_equal(
            Point(cartesian).spherical,
            (spherical[0], radians(spherical[1]), radians(spherical[2]))
        )

    def test_r_getter(self, cartesian: Space3DVector, spherical: Space3DVector) -> None:
        """Test Point can return the radial Spherical component."""
        assert Point(cartesian).r == spherical[0]

    def test_phi_getter(self, cartesian: Space3DVector, spherical: Space3DVector) -> None:
        """Test Point can return the phi (azimuth) Spherical component."""
        np.testing.assert_equal(Point(cartesian).phi, radians(spherical[1]))

    def test_theta_getter(self, cartesian: Space3DVector, spherical: Space3DVector) -> None:
        """Test Point can return the theta (elevation) Spherical component."""
        np.testing.assert_equal(Point(cartesian).theta, radians(spherical[2]))

    def test_spherical_setter(self, cartesian: Space3DVector, spherical: Space3DVector) -> None:
        """Test Point can update its cartesian parameters to match the spherical components."""
        point = Point(cartesian)
        point.cartesian = (-10, -10, -10) # First set it to a point that's not in the parameters
        spherical_vector = (spherical[0], radians(spherical[1]), radians(spherical[2]))
        point.spherical = spherical_vector
        np.testing.assert_array_almost_equal(point.spherical, spherical_vector)
        np.testing.assert_array_almost_equal(point.cartesian, cartesian)

class TestRSetterSphericalEdgeCases(unittest.TestCase):
    """Tests whether the r setter in Point correctly updates the point's position
    and identifies when it cannot with errors in spherical coordinates"""
    def setUp(self) -> None:
        self.pt = Point(-10, -10, -10)

        # tests: initial spherical, new r, expected new spherical
        self.change_tests = [
            (
                (0, math.nan, math.nan), 0,
                (0, math.nan, math.nan)
            ),
            (
                (1, math.radians(45), math.radians(45)), 0,
                (0, math.nan, math.nan)
            ),
            (
                (1, math.radians(45), math.radians(45)), 2,
                (2, math.radians(45), math.radians(45)),
            ),
            (
                (1, math.radians(45), math.radians(45)), -1,
                ValueError
            ),
            (
                (0, math.nan, math.nan), 1,
                ValueError
            ),
            (
                (0, math.nan, math.nan), math.nan,
                ValueError
            ),
        ]

    def test_nominal_r_setter(self) -> None:
        for initial_spherical, r, expected_spherical in self.change_tests:
            if isinstance(expected_spherical, tuple):
                with self.subTest(initial_spherical=initial_spherical, r=r,
                                  expected_polar=expected_spherical):
                    self.pt.spherical = initial_spherical
                    self.pt.r = r
                    np.testing.assert_allclose(self.pt.spherical, expected_spherical, atol=1e-15)

    def test_exceptions_r_setter(self) -> None:
        for initial_spherical, r, expected_spherical in self.change_tests:
            if not isinstance(expected_spherical, tuple):
                with self.subTest(initial_spherical=initial_spherical, r=r,
                                  expected_error_type=expected_spherical):
                    self.pt.spherical = initial_spherical
                    with self.assertRaises(expected_spherical):
                        self.pt.r = r

class TestRSetterPolarEdgeCases(unittest.TestCase):
    """Tests whether the r setter in Point correctly updates the point's position
    and identifies when it cannot with errors in polar coordinates"""
    def setUp(self) -> None:
        self.pt = Point(-10, -10, -10)

        # tests: initial spherical, new r, expected new spherical
        self.change_tests = [
            (
                (0, math.nan), 0,
                (0, math.nan)
            ),
            (
                (1, math.radians(45)), 0,
                (0, math.nan)
            ),
            (
                (1, math.radians(45)), 2,
                (2, math.radians(45)),
            ),
            (
                (1, math.radians(45)), -1,
                ValueError
            ),
            (
                (0, math.nan), 1,
                ValueError
            ),
            (
                (0, math.nan), math.nan,
                ValueError
            ),
        ]

    def test_nominal_r_setter(self) -> None:
        for initial_polar, r, expected_polar in self.change_tests:
            if isinstance(expected_polar, tuple):
                with self.subTest(initial_polar=initial_polar, r=r,
                                  expected_polar=expected_polar):
                    self.pt.polar = initial_polar
                    self.pt.r = r
                    np.testing.assert_allclose(self.pt.polar, expected_polar, atol=1e-15)

    def test_exceptions_r_setter(self) -> None:
        for initial_polar, r, expected_polar in self.change_tests:
            if not isinstance(expected_polar, tuple):
                with self.subTest(initial_polar=initial_polar, r=r,
                                  expected_error_type=expected_polar):
                    self.pt.polar = initial_polar
                    with self.assertRaises(expected_polar):
                        self.pt.r = r

class TestPhiSetterSphericalEdgeCases(unittest.TestCase):
    """Tests whether the phi setter in Point correctly updates the point's
    position and identifies when it cannot with errors in spherical coordinates"""
    def setUp(self) -> None:
        self.pt = Point(-10, -10, -10)

        # tests: initial spherical, new r, expected new spherical
        self.change_tests = [
            (
                (0, math.nan, math.nan), math.nan,
                (0, math.nan, math.nan)
            ),
            (
                (1, math.radians(45), math.radians(45)), math.nan,
                ValueError
            ),
            (
                (1, math.radians(45), math.radians(135)), math.nan,
                ValueError
            ),
            (
                (1, math.radians(45), math.radians(45)), math.radians(0),
                (1, math.radians(0), math.radians(45)),
            ),
            (
                (0, math.nan, math.nan), 1,
                ValueError
            ),
        ]

    def test_nominal_phi_setter(self) -> None:
        for initial_spherical, phi, expected_spherical in self.change_tests:
            if isinstance(expected_spherical, tuple):
                with self.subTest(initial_spherical=initial_spherical, phi=phi,
                                  expected_spherical=expected_spherical):
                    self.pt.spherical = initial_spherical
                    self.pt.phi = phi
                    np.testing.assert_allclose(self.pt.spherical, expected_spherical, atol=1e-15)

    def test_exceptions_phi_setter(self) -> None:
        for initial_spherical, phi, expected_spherical in self.change_tests:
            if not isinstance(expected_spherical, tuple):
                with self.subTest(initial_spherical=initial_spherical, phi=phi,
                                  expected_error_type=expected_spherical):
                    self.pt.spherical = initial_spherical
                    with self.assertRaises(expected_spherical):
                        self.pt.phi = phi

class TestPhiSetterPolarEdgeCases(unittest.TestCase):
    """Tests whether the phi setter in Point correctly updates the point's
    position and identifies when it cannot with errors in polar coordinates"""
    def setUp(self) -> None:
        self.pt = Point(-10, -10, -10)

        # tests: initial polar, new r, expected new polar
        self.change_tests = [
            (
                (0, math.nan), math.nan,
                (0, math.nan)
            ),
            (
                (1, math.radians(45)), math.nan,
                ValueError
            ),
            (
                (1, math.radians(45)), math.nan,
                ValueError
            ),
            (
                (1, math.radians(45)), math.radians(0),
                (1, math.radians(0)),
            ),
            (
                (0, math.nan), 1,
                ValueError
            ),
        ]

    def test_nominal_phi_setter(self) -> None:
        for initial_polar, phi, expected_polar in self.change_tests:
            if isinstance(expected_polar, tuple):
                with self.subTest(initial_polar=initial_polar, phi=phi,
                                  expected_polar=expected_polar):
                    self.pt.polar = initial_polar
                    self.pt.phi = phi
                    np.testing.assert_allclose(self.pt.polar, expected_polar, atol=1e-15)

    def test_exceptions_phi_setter(self):
        for initial_polar, phi, expected_polar in self.change_tests:
            if not isinstance(expected_polar, tuple):
                with self.subTest(initial_polar=initial_polar, phi=phi,
                                  expected_error_type=expected_polar):
                    self.pt.polar = initial_polar
                    with self.assertRaises(expected_polar):
                        self.pt.phi = phi

class TestThetaSetterSphericalEdgeCases(unittest.TestCase):
    """Tests whether the theta setter in Point correctly updates the point's
    position and identifies when it cannot with errors in spherical coordinates"""
    def setUp(self) -> None:
        self.pt = Point(-10, -10, -10)

        # tests: initial spherical, new r, expected new spherical
        self.change_tests = [
            (
                (0, math.nan, math.nan), math.nan,
                (0, math.nan, math.nan)
            ),
            (
                (1, math.radians(45), math.radians(45)), math.nan,
                ValueError
            ),
            (
                (1, math.nan, math.radians(0)), math.radians(0),
                (1, math.nan, math.radians(0))
            ),
            (
                (1, math.nan, math.pi), math.pi,
                (1, math.nan, math.pi)
            ),
            (
                (1, math.radians(45), math.radians(45)), math.radians(90),
                (1, math.radians(45), math.radians(90)),
            ),
            (
                (0, math.nan, math.nan), 1,
                ValueError
            ),
        ]

    def test_nominal_theta_setter(self) -> None:
        for initial_spherical, theta, expected_spherical in self.change_tests:
            if isinstance(expected_spherical, tuple):
                with self.subTest(initial_spherical=initial_spherical, theta=theta,
                                  expected_spherical=expected_spherical):
                    self.pt.spherical = initial_spherical
                    self.pt.theta = theta
                    np.testing.assert_allclose(self.pt.spherical, expected_spherical, atol=1e-15)

    def test_exceptions_theta_setter(self) -> None:
        for initial_spherical, theta, expected_spherical in self.change_tests:
            if not isinstance(expected_spherical, tuple):
                with self.subTest(initial_spherical=initial_spherical, theta=theta,
                                  expected_error_type=expected_spherical):
                    self.pt.spherical = initial_spherical
                    with self.assertRaises(expected_spherical):
                        self.pt.theta = theta

class TestPointNumericDunders(unittest.TestCase):
    def setUp(self) -> None:
        self.coordinates = [
            [(0, 0), (0, 0)],
            [(1, 1), (0, 0)],
            [(0, 0, 0), (0, 0, 0)],
            [(1, 1, 1), (0, 0, 0)],
            [(0, 0, 0), (0, 0)],
            [(0, 0, 0), (1.2, 2.3, 1.2)],
        ]

    def test_add(self) -> None:
        coords = list(filter(lambda x: len(x[0]) == len(x[1]), self.coordinates))
        results = map(
            lambda x : tuple(map(lambda x: x.item(), np.array(x[0]) + np.array(x[1]))),
            coords
        )
        pts = [[Point(a), Point(b)] for a, b in coords]
        for (pt1, pt2), result in zip(pts, results):
            with self.subTest(point1=pt1, point2=pt2, result=result):
                np.testing.assert_allclose(pt1 + pt2, result, atol=1e-15)

    def test_sub(self) -> None:
        coords = list(filter(lambda x: len(x[0]) == len(x[1]), self.coordinates))
        results = map(
            lambda x : tuple(map(lambda x: x.item(), np.array(x[0]) - np.array(x[1]))),
            coords
        )
        pts = [[Point(a), Point(b)] for a, b in coords]
        for (pt1, pt2), result in zip(pts, results):
            with self.subTest(point1=pt1, point2=pt2, result=result):
                np.testing.assert_allclose(pt1 - pt2, result, atol=1e-15)


if __name__ == "__main__":
    unittest.main()
