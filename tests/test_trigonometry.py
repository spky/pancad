"""A file containing unit tests for the pancad.utils.trigonometry module."""
from __future__ import annotations

from math import radians, cos, sin, tau as TAU
from typing import TYPE_CHECKING

import numpy as np
import pytest

from pancad.utils import trigonometry as trig
from pancad.constants import AngleConvention as AC

if TYPE_CHECKING:
    from typing import Type

    from pancad.utils.pancad_types import SpaceVector

class TestVectors:
    """Tests for vector operation helpers"""

    @pytest.mark.parametrize(
        "vector, expected",
        [
            ((1, 0, 0), (1, 0, 0)),
            ((0, 1, 0), (0, 1, 0)),
            ((0, 0, 1), (0, 0, 1)),
            ((0, 0, 3), (0, 0, 1)),
            ((1, 0), (1, 0)),
            ((0, 1), (0, 1)),
            ((0, 3), (0, 1)),
        ]
    )
    def test_get_unit_vector(self, vector: SpaceVector, expected: SpaceVector) -> None:
        """Test trigonometry.get_unit_vector can return the expected unit vector with the same
        shape it was provided. Tests horizontal and vertical vectors.
        """
        length = int(len(vector))
        for shape in [(length,), (length, 1)]:
            result_vector = trig.get_unit_vector(np.array(vector, dtype=np.float64).reshape(shape))
            expected_vector = np.array(expected).reshape(shape)
            np.testing.assert_array_equal(result_vector, expected_vector)
            assert result_vector.shape == expected_vector.shape

    @pytest.mark.parametrize(
        "vector, exception",
        [
            ([[1, 1], [1, 1]], TypeError),
            ((0,0), ValueError),
            ((0,0,0), ValueError),
        ]
    )
    def test_get_unit_vector_exceptions(self, vector: list[list[float]] | SpaceVector,
                                        exception: Type[BaseException]) -> None:
        """Test that get_unit_vector errors when provided an invalid shape."""
        with pytest.raises(exception):
            trig.get_unit_vector(vector) # type: ignore

class TestVectorUtilities:
    """Tests for functions providing common vector information."""

    def test_to_1d_tuple(self) -> None:
        """Test the to_1d_tuple can take all the expected types and return a 1d tuple."""
        expected = (0, 1, 2)
        for vector in (expected, expected[0:2]):
            results = [
                trig.to_1d_tuple(list(vector)),
                trig.to_1d_tuple(vector),
                trig.to_1d_tuple(np.array(vector)),
                trig.to_1d_tuple(np.array(vector).reshape(len(vector), 1)),
            ]
            for result in results:
                assert result == vector

    def test_to_1d_np(self) -> None:
        """Test the to_1d_np can take all the expected types and return a 1d numpy array."""
        original = (0, 1, 2)
        for vector in (original, original[0:2]):
            expected = np.array(vector, dtype=np.float64)
            results = [
                trig.to_1d_np(vector),
                trig.to_1d_np(list(vector)),
                trig.to_1d_np(np.array(vector)),
                trig.to_1d_np(np.array(vector).reshape(len(vector), 1))
            ]
            for result in results:
                np.testing.assert_array_equal(result, expected)

    def test_is_clockwise_2d(self) -> None:
        """Test that is_clockwise can read whether a vector is clockwise and counterclockwise by
        switching two vectors.
        """
        v1 = (1, 0)
        v2 = (0, 1)
        assert not trig.is_clockwise(v1, v2)
        assert trig.is_clockwise(v2, v1)

    @pytest.mark.parametrize("phi", list(range(0, 360, 45)))
    def test_get_angle_between_2d_vectors_tau(self, phi: float) -> None:
        """Tests the ability for get_vector_angle to get the angle between 2D vectors."""
        v1 = (1, 0)
        v2 = trig.polar_to_cartesian((1, radians(phi)))
        convention_results = [
            # Convention, is_opposite, expected_angle
            (AC.PLUS_TAU, False, radians(phi)),
            (AC.PLUS_TAU, True, TAU - radians(phi)),
        ]
        for convention, is_opposite, expected_angle in convention_results:
            angle = trig.get_vector_angle(v1, v2, opposite=is_opposite, convention=convention)
            assert angle == pytest.approx(expected_angle)

    @pytest.mark.parametrize("phi", list(range(0, 180+1, 45)))
    def test_get_angle_between_3d_vectors_pi(self, phi: float) -> None:
        """Tests the ability for get_vector_angle to get the angle between 3D vectors."""
        theta = 90
        v1 = trig.spherical_to_cartesian((1, 0, radians(theta)))
        v2 = trig.spherical_to_cartesian((1, radians(phi), radians(theta)))
        angle = trig.get_vector_angle(v1, v2)
        assert angle == pytest.approx(radians(phi))

class TestRotationMatrices:
    """Tests for rotation matrices created by trigonometry."""

    def test_x(self) -> None:
        """Test rotating around the x axis."""
        angle = radians(45)
        cost, sint = cos(angle), sin(angle)
        matrix = trig.rotation(angle, (1, 0, 0))
        expected = [[1, 0, 0], [0, cost, -sint], [0, sint, cost]]
        np.testing.assert_array_equal(matrix, expected)

    def test_y(self) -> None:
        """Test rotating around the y axis."""
        angle = radians(45)
        cost, sint = cos(angle), sin(angle)
        matrix = trig.rotation(angle, (0, 1, 0))
        expected = [[cost, 0, sint], [0, 1, 0], [-sint, 0, cost]]
        np.testing.assert_array_equal(matrix, expected)

    def test_z(self) -> None:
        """Test rotating around the z axis."""
        angle = radians(45)
        cost, sint = cos(angle), sin(angle)
        matrix = trig.rotation(angle, (0, 0, 1))
        expected = [[cost, -sint, 0], [sint, cost, 0], [0, 0, 1]]
        np.testing.assert_array_equal(matrix, expected)

    def test_2(self) -> None:
        """Test rotating around the origin in 2D."""
        angle = radians(45)
        cost, sint = cos(angle), sin(angle)
        matrix = trig.rotation(angle, "2")
        expected = [[cost, -sint], [sint, cost]]
        np.testing.assert_array_equal(matrix, expected)

    def test_arbitrary_negative_z(self) -> None:
        """Test that axis direction changes the rotation direction."""
        angle = radians(45)
        matrix = trig.rotation(angle, (0, 0, -1))
        expected = trig.rotation(-angle, (0, 0, 1))
        np.testing.assert_array_equal(matrix, expected)

    def test_multi_rotation(self) -> None:
        """Test that multi_rotation can create the same matrix as a normal z rotation."""
        angle = radians(90)
        matrix = trig.multi_rotation("xyz", 0, 0, angle)
        expected = trig.rotation_z(angle)
        np.testing.assert_array_equal(matrix, expected)
