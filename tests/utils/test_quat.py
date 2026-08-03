"""Tests for pancad's quaternion definition."""
from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
import numpy as np

from pancad.utils.quat import Quat

if TYPE_CHECKING:
    QuatCoefficients = tuple[float, float, float, float]

@pytest.mark.parametrize("coefficients", [(1, 1, 1, 1)])
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
