"""Tests for pancad's quaternion definition."""
from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
import numpy as np

from pancad.utils.quat import Quat

if TYPE_CHECKING:
    QuatCoefficients = tuple[float, float, float, float]

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

    def test_quat_equal(self, quat: Quat) -> None:
        """Test Quat can be equal to a new Quat and is not equal to its conjugate."""
        assert quat == Quat(quat)
        assert quat != quat.conjugate

    def test_repr(self, quat: Quat) -> None:
        """Test Quat's repr dunder labels the scalar and vector components."""
        w, x, y, z = quat
        assert repr(quat) == f"[{w}, {x}i, {y}j, {z}k]"
