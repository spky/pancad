"""Tests for pancad's geometry utility functions."""
from __future__ import annotations

import numpy as np
import quaternion
import pytest

import pancad.utils.geometry as geo_utils

# Test id abbreviations:
# pt=point, vec=vector, para=parallel, perp=perpendicular, dir=direction
# cw=clockwise, ccw=counter-clockwise, ul=upper left, br=bottom_right
@pytest.mark.parametrize(
    "point, direction, expected",
    [ # Comment summarizes the expected results
        # The origin because origin is provided.
        pytest.param((0, 0), (1, 0), (0, 0), id="2d_origin"),
        pytest.param((0, 0, 0), (1, 0, 0), (0, 0, 0), id="3d_origin"),
        # The origin because the point is parallel to the direction vector
        pytest.param((2, 0), (1, 0), (0, 0), id="2d_pt_vec_para"),
        # The provided point because the point vector and direction
        # are perpendicular.
        pytest.param((1, 1), (-1, 1), (1, 1), id="2d_pt_vec_perp"),
        # Point is cw/ccw of closest point, direction is pointing ul/br:
        pytest.param((2, 0), (-1, 1), (1, 1), id="2d_cw_pt_ul_dir"),
        pytest.param((2, 0), (1, -1), (1, 1), id="2d_cw_pt_br_dir"),
        pytest.param((0, 2), (-1, 1), (1, 1), id="2d_ccw_pt_br_dir"),
        pytest.param((0, 2), (1, -1), (1, 1), id="2d_ccw_pt_br_dir"),
    ],
)
def test_closest_to_origin(point, direction, expected):
    """Test function for finding the point on a line closest to the origin."""
    result = geo_utils.closest_to_origin(point, direction)
    np.testing.assert_array_almost_equal(result, np.array(expected))

ZERO_VEC_MSG_RE = r"^Got zero vector for line"
DIM_MISMATCH_RE = r"dimensions are not equal$"
@pytest.mark.parametrize(
    "point, direction, msg",
    [
        pytest.param((0, 0), (0, 0), ZERO_VEC_MSG_RE, id="pt0,0_zero_vec"),
        pytest.param((0, 0, 0), (0, 0, 0), ZERO_VEC_MSG_RE, id="pt0,0,0_zero_vec"),
        pytest.param((1, 1), (0, 0), ZERO_VEC_MSG_RE, id="pt1,1_zero_vec"),
        pytest.param((1, 1, 1), (0, 0, 0), ZERO_VEC_MSG_RE, id="pt1,1,1_zero_vec"),
        pytest.param((0, 0), (1, 0, 0), DIM_MISMATCH_RE, id="2d_pt_3d_vec"),
        pytest.param((0, 0, 0), (1, 0), DIM_MISMATCH_RE, id="3d_pt_2d_vec"),
    ]
)
def test_closest_to_origin_excs(point, direction, msg):
    """Test that the closest_to_origin function produces relevant exceptions."""
    with pytest.raises(ValueError, match=msg):
        geo_utils.closest_to_origin(point, direction)

@pytest.mark.parametrize(
    "vector",
    [
        (1, 0, 0), (0, 1, 0), (0, 0, 1),
        (-1, 0, 0), (0, -1, 0), (0, 0, -1),
        (1, 1, 1), (-1, -1, -1),
    ]
)
def test_get_perpendicular(vector):
    """Test that get_perpendicular always returns a perpendicular vector."""
    perp = geo_utils.get_perpendicular(vector)
    assert np.dot(vector, perp) == pytest.approx(0)

@pytest.mark.parametrize(
    "vector, err_type, msg",
    [
        pytest.param((0, 0, 0), ValueError, "Expected non-zero vector", id="zero_input"),
        pytest.param((1, 1), TypeError, "only supports 3D vectors", id="2d_input"),
        pytest.param((1, 1, 1, 1), TypeError, "only supports 3D vectors", id="4d_input"),
    ]
)
def test_get_perpendicular_excs(vector, err_type, msg):
    """Test the error handling of get_perpendicular."""
    with pytest.raises(err_type, match=msg):
        geo_utils.get_perpendicular(vector)

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
    rotated = quaternion.rotate_vectors(q, start)
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
