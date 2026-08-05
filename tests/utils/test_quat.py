"""Tests for pancad's quaternion definition."""
from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
import numpy as np

from pancad.utils.quat import Quat

if TYPE_CHECKING:
    from tests._typing import GeometrySampleData, ChangeTest

    QuatCoefficients = tuple[float, float, float, float]

@pytest.fixture(name="quat_sample")
def fixture_quat_sample(data_geo_util_sample_quats: GeometrySampleData) -> Quat:
    """A quaternion generated from geometry util sample data."""
    vectors, scalars = (data_geo_util_sample_quats["vectors"],
                        data_geo_util_sample_quats["scalars"])
    if "angle" in scalars:
        return Quat.from_angle(scalars["angle"], vectors["axis"])
    raise RuntimeError(f"Missing angle from scalars: {scalars}")

@pytest.fixture(name="quat_expected")
def fixture_quat_expected(data_geo_util_sample_quats: GeometrySampleData) -> QuatCoefficients:
    """The expected vectorized quaternion generated from geometry util sample data."""
    vectors, scalars = (data_geo_util_sample_quats["vectors"],
                        data_geo_util_sample_quats["scalars"])
    return (scalars["scalar"], *vectors["vector"])

@pytest.mark.parametrize("coefficients", [(1, 2, 3, 4)])
class TestInitializationTypes:
    """Tests for all the ways to initialize a Quat with different input types."""

    def test_floats(self, coefficients: QuatCoefficients) -> None:
        """Test initializing a Quat using floats."""
        assert tuple(Quat(*coefficients)) == coefficients

    def test_tuple(self, coefficients: QuatCoefficients) -> None:
        """Test initializing a Quat using a tuple of floats."""
        assert tuple(Quat(coefficients)) == coefficients

    def test_list(self, coefficients: QuatCoefficients) -> None:
        """Test initializing a Quat using a tuple of floats."""
        assert tuple(Quat(list(coefficients))) == coefficients

    def test_numpy_array(self, coefficients: QuatCoefficients) -> None:
        """Test initializing a Quat using a 1D numpy array."""
        assert tuple(Quat(np.array(coefficients))) == coefficients

    def test_quat_in_quat(self, coefficients: QuatCoefficients) -> None:
        """Test initializing a Quat using another Quat."""
        assert tuple(Quat(Quat(coefficients))) == coefficients

@pytest.mark.parametrize("quat", [Quat(1, 2, 3, 4)])
class TestSpotChecks:
    """Test Quat functionality by spot checking with assertions."""

    def test_array(self, quat: Quat) -> None:
        """Test that Quat can be turned into a numpy array with a specified dtype."""
        np.testing.assert_array_equal(np.array(quat), np.array(quat[:]))
        np.testing.assert_array_equal(np.array(quat, dtype=np.float64), np.array(quat[:]))

    def test_vector(self, quat: Quat) -> None:
        """Test the quaternion vector gets the last 3 elements"""
        assert quat.vector == quat[1:]

    def test_conjugate(self, quat: Quat) -> None:
        """Test the conjugate returns the Quat with negative vector components."""
        assert quat.conjugate[1:] == tuple(-c for c in quat.vector)

    def test_inverse(self, quat: Quat) -> None:
        """Test the inverse returns the normalized quaternion conjugate."""
        assert tuple(quat.inverse) == tuple(quat.conjugate / np.linalg.norm(quat))

    def test_invert(self, quat: Quat) -> None:
        """Test that the invert dunder of the quaternion returns its inverse."""
        assert tuple(~quat) == tuple(quat.inverse)

    def test_negation(self, quat: Quat) -> None:
        """Test the neg dunder returns the quaternion multiplied by negative 1."""
        assert tuple(-quat) == tuple(-np.array(quat))

    def test_quat_equal(self, quat: Quat) -> None:
        """Test Quat can be equal to a new Quat and is not equal to its conjugate."""
        assert quat == Quat(quat)
        assert quat != quat.conjugate

    def test_repr(self, quat: Quat) -> None:
        """Test Quat's repr dunder labels the scalar and vector components."""
        w, x, y, z = quat
        assert repr(quat) == f"[{w}, {x}i, {y}j, {z}k]"

    def test_scalar_division(self, quat: Quat) -> None:
        """Test truediv dunder for scalar division."""
        np.testing.assert_array_equal(np.array(quat / 4), np.array(quat) / 4)

    def test_scalar_multiplication(self, quat: Quat) -> None:
        """Test truediv dunder for scalar division."""
        np.testing.assert_array_equal(np.array(quat * 4), np.array(quat) * 4)

    def test_quat_addition(self, quat: Quat) -> None:
        """Test the add dunder for quaternion addition."""
        np.testing.assert_array_equal(np.array(quat + quat), np.array(quat) + np.array(quat))

    def test_quat_subtraction(self, quat: Quat) -> None:
        """Test the sub dunder for quaternion subtraction."""
        np.testing.assert_array_equal(np.array(quat - quat), np.array(quat) - np.array(quat))

    def test_len(self, quat: Quat) -> None:
        """Test the length of the quaternion is always 4."""
        assert len(quat) == 4

class TestSamples:
    """Test initializing sample quaternions."""

    def test_vector(self, quat_sample: Quat, quat_expected: QuatCoefficients) -> None:
        """Test the sample matches the expected vector."""
        assert quat_sample.vector == pytest.approx(quat_expected[1:])

    def test_scalar(self, quat_sample: Quat, quat_expected: QuatCoefficients) -> None:
        """Test the sample matches the expected scalar."""
        assert quat_sample.scalar == pytest.approx(quat_expected[0])

    def test_coefficients(self, quat_sample: Quat, quat_expected: QuatCoefficients) -> None:
        """Test that each of the sample's single coefficient getters match the expected value."""
        w, x, y, z = quat_expected
        pairs = [(quat_sample.scalar, w), (quat_sample.w, w),
                 (quat_sample.x, x), (quat_sample.y, y), (quat_sample.z, z)]
        for quat_value, expected_value in pairs:
            assert quat_value == pytest.approx(expected_value)

class TestChanges:
    """Test changing vectors with quaternions."""

    def test_rotate(self, changes_quat_rotate: ChangeTest) -> None:
        sample, change = changes_quat_rotate
        quat = Quat.from_angle(change["scalars"]["angle"], change["vectors"]["axis"])
        assert quat.rotate(sample["vectors"]["direction"]) == change["vectors"]["new"]
