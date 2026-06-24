"""Tests for the pancad Point class."""
from __future__ import annotations

from math import radians, nan, sqrt, pi, hypot, atan, degrees
from typing import TYPE_CHECKING

import numpy as np
import pytest

from pancad.geometry.point import Point
from pancad.utils.pancad_types import PolarVector, SphericalVector

if TYPE_CHECKING:
    from typing import Type
    from collections.abc import Sequence

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

class TestPolarEdgeCases:
    """Tests for polar coordinates where setting one of the parameters impacts the other
    parameters.
    """

    @pytest.mark.parametrize(
        "initial, r, expected",
        [ # Angles in degrees here
            [(0, nan), 0, (0, nan)],
            [(1, 45), 0, (0, nan)],
            [(1, 45), 2, (2, 45)],
        ]
    )
    def test_r_nominal(self, initial: Space2DVector, r: float, expected: Space2DVector) -> None:
        """Tests for setting the radial polar coordinate where Point should not raise an
        exception but still changes (or could accidentally change) phi.
        """
        point = Point.from_polar(initial[0], radians(initial[1]))
        point.r = r
        np.testing.assert_array_almost_equal(point.polar, (expected[0], radians(expected[1])))

    @pytest.mark.parametrize(
        "initial, r, exception, match",
        [ # Angles in degrees here
            [(1, 45), -1, ValueError, "r cannot be less than zero"],
            [(0, nan), 1, ValueError, "r must be 0 if phi is NaN"],
            [(0, nan), nan, ValueError, "r cannot be NaN"],
        ]
    )
    def test_r_exceptions(self, initial: Space2DVector, r: float,
                          exception: Type[Exception], match: str) -> None:
        """Tests for setting the radial polar coordinate to a value that should raise an
        exception.
        """
        point = Point.from_polar(initial[0], radians(initial[1]))
        with pytest.raises(exception, match=match):
            point.r = r

    @pytest.mark.parametrize(
        "initial, phi, expected",
        [ # Angles in degrees here
            [(0, nan), nan, (0, nan)],
            [(1, 45), 0, (1, 0)],
        ]
    )
    def test_phi_nominal(self, initial: Space2DVector, phi: float,
                         expected: Space2DVector) -> None:
        """Tests for setting the phi polar coordinate where Point should not raise an
        exception but could accidentally change r.
        """
        point = Point.from_polar(initial[0], radians(initial[1]))
        point.phi = radians(phi)
        np.testing.assert_array_almost_equal(point.polar, (expected[0], radians(expected[1])))

    @pytest.mark.parametrize(
        "initial, phi, exception, match",
        [ # Angles in degrees here
            [(1, 45), nan, ValueError, "phi cannot be NaN if r is non-zero"],
            [(0, nan), 45, ValueError, "phi must be NaN if r is zero"],
        ]
    )
    def test_phi_exceptions(self, initial: Space2DVector, phi: float,
                            exception: Type[Exception], match: str) -> None:
        """Tests for setting the phi polar coordinate to a value that should raise an exception.
        """
        point = Point.from_polar(initial[0], radians(initial[1]))
        with pytest.raises(exception, match=match):
            point.phi = radians(phi)

class TestSphericalSetting:
    """Tests for spherical coordinates where setting one of the parameters can impact the other
    parameters.
    """

    @pytest.mark.parametrize(
        "initial, r, expected",
        [ # Angles in degrees here
            [(0, nan, nan), 0, (0, nan, nan)],
            [(1, 45, 45), 0, (0, nan, nan)],
            [(1, 45, 45), 2, (2, 45, 45)],
        ]
    )
    def test_r_nominal(self, initial: Space3DVector, r: float, expected: Space3DVector) -> None:
        """Tests for setting the radial spherical coordinate where Point should not raise an
        exception but still changes (or could accidentally change) phi and theta.
        """
        point = Point.from_spherical(initial[0], radians(initial[1]), radians(initial[2]))
        point.r = r
        np.testing.assert_array_almost_equal(
            point.spherical, (expected[0], radians(expected[1]), radians(expected[2]))
        )

    @pytest.mark.parametrize(
        "initial, r, exception, match",
        [ # Angles in degrees here
            [(1, 45, 45), -1, ValueError, "r cannot be less than zero"],
            [(0, nan, nan), 1, ValueError, "r must be 0 if phi and theta are NaN"],
            [(0, nan, nan), nan, ValueError, "r cannot be NaN"],
        ]
    )
    def test_r_exceptions(self, initial: Space3DVector, r: float,
                          exception: Type[Exception], match: str) -> None:
        """Tests for setting the radial spherical coordinate to a value that should raise an
        exception.
        """
        point = Point.from_spherical(initial[0], radians(initial[1]), radians(initial[2]))
        with pytest.raises(exception, match=match):
            point.r = r

    @pytest.mark.parametrize(
        "initial, phi, expected",
        [ # Angles in degrees here
            [(0, nan, nan), nan, (0, nan, nan)],
            [(1, 45, 45), 0, (1, 0, 45)],
        ]
    )
    def test_phi_nominal(self, initial: Space3DVector, phi: float,
                         expected: Space3DVector) -> None:
        """Tests for setting the phi spherical coordinate where Point should not raise an
        exception but still changes (or could accidentally change) r and theta.
        """
        point = Point.from_spherical(initial[0], radians(initial[1]), radians(initial[2]))
        point.phi = radians(phi)
        np.testing.assert_array_almost_equal(
            point.spherical, (expected[0], radians(expected[1]), radians(expected[2]))
        )

    @pytest.mark.parametrize(
        "initial, phi, exception, match",
        [ # Angles in degrees here
            [(1, 45, 45), nan, ValueError, "If phi is NaN, theta must be pi/2 or NaN"],
            [(1, 45, 135), nan, ValueError, "If phi is NaN, theta must be pi/2 or NaN"],
            [(0, nan, nan), 45, ValueError, "phi can only be set to NaN if theta is already NaN"],
        ]
    )
    def test_phi_exceptions(self, initial: Space3DVector, phi: float,
                            exception: Type[Exception], match: str) -> None:
        """Tests for setting the phi spherical coordinate to a value that should raise an
        exception.
        """
        point = Point.from_spherical(initial[0], radians(initial[1]), radians(initial[2]))
        with pytest.raises(exception, match=match):
            point.phi = radians(phi)

    @pytest.mark.parametrize(
        "initial, theta, expected",
        [
            [(0, nan, nan), nan, (0, nan, nan)],
            [(1, nan, 0), 0, (1, nan, 0)],
            [(1, nan, 180), 180, (1, nan, 180)],
            [(1, 45, 45), 90, (1, 45, 90)],
        ]
    )
    def test_theta_nominal(self, initial: Space3DVector, theta: float,
                           expected: Space3DVector) -> None:
        """Tests for setting the theta spherical coordinate where Point should not raise an
        exception but still changes (or could accidentally change) r and phi.
        """
        point = Point.from_spherical(initial[0], radians(initial[1]), radians(initial[2]))
        point.theta = radians(theta)
        np.testing.assert_array_almost_equal(
            point.spherical, (expected[0], radians(expected[1]), radians(expected[2]))
        )

    @pytest.mark.parametrize(
        "initial, theta, exception, match",
        [ # Angles in degrees here
            [(1, 45, 45), nan, ValueError, "Theta cannot be NaN if r is non-zero"],
            [(0, nan, nan), 1, ValueError, "theta must be NaN, 0, or pi if phi is NaN"],
        ]
    )
    def test_theta_exceptions(self, initial: Space3DVector, theta: float,
                              exception: Type[Exception], match: str) -> None:
        """Tests for setting the theta spherical coordinate to a value that should raise an
        exception.
        """
        point = Point.from_spherical(initial[0], radians(initial[1]), radians(initial[2]))
        with pytest.raises(exception, match=match):
            point.theta = radians(theta)

@pytest.mark.parametrize(
    "point, vector",
    [
        [(0, 0), (0, 0)],
        [(1, 1), (0, 0)],
        [(0, 0, 0), (0, 0, 0)],
        [(1, 1, 1), (0, 0, 0)],
        [(0, 0, 0), (1.2, 2.3, 1.2)],
    ]
)
class TestPointOperatorDunders:
    """Tests for the dunders allowing Point to interact with other types using +, -, etc."""

    def test_add_sequence(self, point: SpaceVector, vector: Sequence[float]) -> None:
        """Test for adding point to a sequence from the left and right."""
        for seq in [tuple(vector), list(vector)]:
            # add
            np.testing.assert_array_equal(Point(point) + seq, # add
                                          np.array(point) + np.array(seq))
            # radd
            np.testing.assert_array_equal(vector + Point(point), # radd
                                           np.array(seq) + np.array(point))

    def test_add_horizontal_numpy_array(self, point: SpaceVector,
                                        vector: Sequence[float]) -> None:
        """Test for adding point to a horizontal numpy array from the left and right."""
        np.testing.assert_array_equal(Point(point) + np.array(vector), # add
                                      np.array(point) + np.array(vector))
        np.testing.assert_array_equal(np.array(vector) + Point(point), # radd
                                      np.array(vector) + np.array(point))

    def test_add_vertical_numpy_array(self, point: SpaceVector, vector: Sequence[float]) -> None:
        """Test for adding point to a vertical numpy array from the left and right."""
        # add, actually uses the numpy implementation and returns a 2x2 or 3x3 matrix
        np.testing.assert_array_equal(
            Point(point) + np.array(vector).reshape(len(vector), 1),
            np.array(point) + np.array(vector).reshape(len(vector), 1),
        )
        # radd, actually uses the numpy implementation and returns a 2x2 or 3x3 matrix.
        np.testing.assert_array_equal(
            np.array(vector).reshape(len(vector), 1) + Point(point),
            np.array(vector).reshape(len(vector), 1) + np.array(point)
        )
    def test_sub_sequence(self, point: SpaceVector, vector: Sequence[float]) -> None:
        """Test for subtracting a point to/from a sequence from the left and right."""
        for seq in [tuple(vector), list(vector)]:
            np.testing.assert_array_equal(Point(point) - seq, # sub
                                          np.array(point) - np.array(seq))
            np.testing.assert_array_equal(seq - Point(point), # rsub
                                          np.array(seq) - np.array(point))

    def test_sub_horizontal_numpy_array(self, point: SpaceVector,
                                        vector: Sequence[float]) -> None:
        """Test for subtracting a point to/from a horizontal numpy array from the left and right.
        """
        np.testing.assert_array_equal(Point(point) - np.array(vector), # sub
                                      np.array(point) - np.array(vector))
        np.testing.assert_array_equal(np.array(vector) - Point(point), # rsub
                                      np.array(vector) - np.array(point))
