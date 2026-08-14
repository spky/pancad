"""Tests for pancad's geometry utility functions."""
from __future__ import annotations

from typing import TYPE_CHECKING
import numpy as np
import pytest

import pancad.utils.geometry as geo_utils

if TYPE_CHECKING:
    from pancad.utils.pancad_types import SpaceVector, Space3DVector
    from tests._typing import GeometrySampleData

class TestClosestToOrigin:
    """Tests for the function getting the closest point on a line to the origin point."""

    def test_nominal(self, data_geo_util_sample_closest_to_origin: GeometrySampleData) -> None:
        """Test closest_to_origin can find the closest points that match test sample data."""
        vectors = data_geo_util_sample_closest_to_origin["vectors"]
        result = geo_utils.closest_to_origin(vectors["point"], vectors["direction"])
        np.testing.assert_array_almost_equal(result, vectors["expected"])

    @pytest.mark.parametrize(
        "point, direction",
        [[(0, 0), (0, 0)], [(0, 0, 0), (0, 0, 0)], [(1, 1), (0, 0, 0)], [(1, 1, 1), (0, 0, 0)]]
    )
    def test_zero_vector_exception(self, point: SpaceVector, direction: SpaceVector) -> None:
        """Test that closest_to_origin raises an error when it gets a zero vector line direction.
        """
        with pytest.raises(ValueError, match=r"^Got zero vector for line"):
            geo_utils.closest_to_origin(point, direction)

    @pytest.mark.parametrize("point, direction", [[(0, 0), (1, 0, 0)], [(0, 0, 0), (1, 0)]])
    def test_dimension_mismatch(self, point: SpaceVector, direction: SpaceVector) -> None:
        """Test that closest_to_origin raises an error when it mismatched vector dimensions.
        """
        with pytest.raises(ValueError, match=r"dimensions are not equal$"):
            geo_utils.closest_to_origin(point, direction)

class TestGetPerpendicular:
    """Tests for the function getting a vector perpendicular to a vector."""
    @pytest.mark.parametrize(
        "vector",
        [
            (1, 0, 0), (0, 1, 0), (0, 0, 1), (-1, 0, 0), (0, -1, 0),
            (0, 0, -1), (1, 1, 1), (-1, -1, -1),
        ]
    )
    def test_nominal(self, vector: Space3DVector) -> None:
        """Test that get_perpendicular always returns a perpendicular vector."""
        assert np.dot(vector, geo_utils.get_perpendicular(vector)) == pytest.approx(0)

    def test_zero_vector_exception(self) -> None:
        """Test the error handling of get_perpendicular."""
        with pytest.raises(ValueError, match="Expected non-zero vector"):
            geo_utils.get_perpendicular((0, 0, 0))

@pytest.mark.parametrize(
    "start, target",
    [
        pytest.param((1, 0, 0), (1, 0, 0), id="unrotated_x"),
        pytest.param((0, 1, 0), (0, 1, 0), id="unrotated_y"),
        pytest.param((0, 0, 1), (0, 0, 1), id="unrotated_z"),
        pytest.param((1, 0, 0), (-1, 0, 0), id="x_to_-x"),
        pytest.param((1, 0, 0), (0, 1, 0), id="x_to_y"),
        pytest.param((1, 0, 0), (1/np.sqrt(2), 1/np.sqrt(2), 0), id="x_to_(1,1,0)normed"),
        pytest.param((1, 0, 0), (-1/np.sqrt(2), 1/np.sqrt(2), 0), id="x_to_(-1,1,0)normed"),
        pytest.param((1, 0, 0), (-1/np.sqrt(2), -1/np.sqrt(2), 0), id="x_to_(-1,-1,0)normed"),
        pytest.param((1/np.sqrt(3), 1/np.sqrt(3), 1/np.sqrt(3)),
                     (-1/np.sqrt(3), -1/np.sqrt(3), -1/np.sqrt(3)),
                     id="(1,1,1)normed_to_(-1,-1,-1)normed"),
    ]
)
def test_get_rotation_quat(start, target):
    """Test that the quaternions returned by get_rotation_quat actually rotate
    the start vector to the target vector.
    """
    q = geo_utils.get_rotation_quat(start, target)
    rotated = q.rotate(start)
    print(f"{q} | Rotated: {rotated}")
    assert rotated == pytest.approx(target)

MUST_BE_3D_MSG = "start/target must be 3D"
START_TARGET_ZERO_MSG = "start/target cannot be zero vector"
@pytest.mark.parametrize(
    "start, target, err_type, msg",
    [
        pytest.param((1, 0), (0, 1), TypeError, MUST_BE_3D_MSG, id="2d_input"),
        pytest.param((1, 0), (0, 1, 0), TypeError, MUST_BE_3D_MSG, id="2d3d_start_target"),
        pytest.param((1, 1, 1, 1), (2, 2, 2, 2), TypeError, MUST_BE_3D_MSG, id="4d_input"),
        pytest.param((0, 0, 0), (1, 1, 1), ValueError, START_TARGET_ZERO_MSG, id="zero_start"),
        pytest.param((1, 1, 1), (0, 0, 0), ValueError, START_TARGET_ZERO_MSG, id="zero_target"),
    ]
)
def test_get_rotation_quat_excs(start, target, err_type, msg):
    """Test the error handling of get_rotation_quat."""
    with pytest.raises(err_type, match=msg):
        geo_utils.get_rotation_quat(start, target)

class TestGetUniqueVector:
    """Tests for calcuating the unique versions of vectors."""

    def test_2d_3d_tuples(self, data_geo_util_sample_unique_vector: GeometrySampleData) -> None:
        """Test that 2D and 3D vectors are converted to their unique versions."""
        vectors = data_geo_util_sample_unique_vector["vectors"]
        assert geo_utils.get_unique_vector(vectors["input"]) == vectors["result"]

    def test_numpy_array(self, data_geo_util_sample_unique_vector: GeometrySampleData) -> None:
        """Test that 2D and 3D numpy array inputs return a numpy array output."""
        vectors = data_geo_util_sample_unique_vector["vectors"]
        result = geo_utils.get_unique_vector(np.array(vectors["input"]))
        assert tuple(result) == vectors["result"] # Check correct value
        assert isinstance(result, np.ndarray) # Check that the output is actually a numpy array

    def test_1d_tuple(self) -> None:
        """Test ability to return unique 1D tuples."""
        assert geo_utils.get_unique_vector((-1,)) == (1,)
        assert geo_utils.get_unique_vector((1,)) == (1,)

    def test_0d_tuple(self) -> None:
        """Test ability to return an empty unique tuple."""
        assert geo_utils.get_unique_vector(tuple()) == tuple()
