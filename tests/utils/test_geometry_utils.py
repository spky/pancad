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

class TestGetRotationQuat:
    """Tests for the function getting the quaternion to rotate a vector to point in the same
    direction as another.
    """

    def test_nominal(self, data_geo_util_sample_get_rotation_quat: GeometrySampleData) -> None:
        """Test that the returned quaternions rotate the start vector to the target vector."""
        vectors = data_geo_util_sample_get_rotation_quat["vectors"]
        start, target = vectors["start"], vectors["target"]
        assert len(start) == 3 and len(target) == 3
        quat = geo_utils.get_rotation_quat(start, target)
        assert quat.rotate(start) == pytest.approx(target)

    @pytest.mark.parametrize(
        "start, target",
        [[(1, 0), (0, 1)], [(1, 0), (0, 1, 0)], [(1, 1, 1, 1), (2, 2, 2, 2)]],
    )
    def test_non_3d_exception(self, start: SpaceVector, target: SpaceVector) -> None:
        """Test that when the function is provided non-3D input it raises a TypeError."""
        with pytest.raises(TypeError, match="start/target must be 3D"):
            geo_utils.get_rotation_quat(start, target) # type: ignore # Testing for error

    @pytest.mark.parametrize("start, target", [[(0, 0, 0), (1, 1, 1)], [(1, 1, 1), (0, 0, 0)]])
    def test_zero_vector_exception(self, start: Space3DVector, target: Space3DVector) -> None:
        """Test that a ValueError is raised when a zero vector is provided as an inputs."""
        with pytest.raises(ValueError, match="start/target cannot be zero vector"):
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
