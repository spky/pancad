"""Tests for pancad's geometry utility functions."""
from __future__ import annotations

import numpy as np
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
