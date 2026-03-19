"""Tests for pancad's Plane class."""
import itertools
from math import cos, sin, radians

import numpy as np
import pytest

from pancad.geometry.point import Point
from pancad.geometry.plane import Plane
from pancad.geometry import conversion

ROUNDING_PLACES = 10

ORIGIN = (0, 0, 0)
X_3D = (1, 0, 0)
Y_3D = (0, 1, 0)
Z_3D = (0, 0, 1)

XY_PARAM = (ORIGIN, Z_3D)
XZ_PARAM = (ORIGIN, Y_3D)

# id abbreviations: trans=translate, [xyz][+-]1= Add/subtract 1 from component.
# xy=XY-Plane, xz=XZ-Plane, yz=YZ-Plane, - indicates normal is antiparallel.
@pytest.mark.parametrize(
    "plane_init, point, normal, expected",
    [
        pytest.param(XY_PARAM, ORIGIN, Z_3D, XY_PARAM, id="xy_unrotated"),
        pytest.param((ORIGIN, (0, 0, -1)),
                     ORIGIN, (0, 0, -1),
                     (ORIGIN, (0, 0, -1)),
                     id="-xy_unrotated"),
        pytest.param(XY_PARAM,
                     (0, 0, 1), None,
                     ((0, 0, 1), Z_3D),
                     id="xy_trans_z+1"),
        pytest.param(XY_PARAM,
                     (1, 1, 1), None,
                     ((0, 0, 1), Z_3D),
                     id="xy_trans_x+1y+1z+1"),
        pytest.param(XY_PARAM, ORIGIN, Y_3D, XZ_PARAM, id="xy_normal_set_to_xz"),
        pytest.param(XY_PARAM,
                     (0, 1, 0), Y_3D,
                     ((0, 1, 0), Y_3D),
                     id="xy_normal_set_to_xz,y+1"),
        pytest.param(XY_PARAM,
                     (1, 1, 1), Y_3D,
                     ((0, 1, 0), Y_3D),
                     id="xy_normal_set_to_xz,x+1y+1z+1"),
    ]
)
def test_move_to_point(plane_init, point, normal, expected):
    """Tests plane movement to a new point and normal against known values."""
    init_point, init_normal = plane_init
    exp_point, exp_normal = expected
    plane = Plane(init_point, init_normal)
    plane.move_to_point(point, normal)
    result_pt = np.array(plane.reference_point)
    print(plane.reference_point, result_pt, plane.normal)
    np.testing.assert_array_almost_equal(result_pt, exp_point)
    np.testing.assert_array_almost_equal(plane.normal, exp_normal)

QUAT_ROTATIONS = [
    # Init Point, Initial Direction, Rotation Axis Vector, Rotation Angle,
    # Expected Closest Point, Expected Normal, Id Prefix
    (ORIGIN, Z_3D, (0, 0, 0), 0, ORIGIN, Z_3D, "q_xy_unrotated_zero_axis"),
    (ORIGIN, Z_3D, Z_3D, 0, ORIGIN, Z_3D, "q_xy_unrotated_around_z_axis"),
    (ORIGIN, Z_3D, Z_3D, 90, ORIGIN, Z_3D, "q_xy_rotate_z_around_z"),
    (ORIGIN, Z_3D, Y_3D, 90, ORIGIN, X_3D, "q_xy_rotate_to_yz"),
    ((1, 1, 1), Z_3D, Y_3D, 90, (0, 0, 1), X_3D, "q_1,1,1_znorm_rotate_around_y"),
]

def _quaternion_rotate_params(rotations):
    """Generates the list of pytest parameters for testing quaternion plane rotation."""
    params = []
    for point, normal, rotation_axis, angle, exp_closest, exp_normal, id_ in rotations:
        quat_w = cos(radians(angle / 2))
        quat_ijk = map(lambda x, y: x * sin(radians(y) / 2),
                       rotation_axis, itertools.repeat(angle))
        quat = np.quaternion(quat_w, *quat_ijk)
        test_id = "_".join(
            [id_, str(angle), str(rotation_axis), str(exp_closest), str(exp_normal)],
        )
        param = pytest.param(point, normal, quat, exp_closest, exp_normal, id=test_id)
        params.append(param)
    return params

@pytest.mark.parametrize(
    "init_point, init_normal, rotation, exp_point, exp_normal",
    [
        *_quaternion_rotate_params(QUAT_ROTATIONS),
    ]
)
def test_rotate(init_point, init_normal, rotation, exp_point, exp_normal):
    """Tests plane rotation to a new closest point and normal behavior against
    known values.
    """
    plane = Plane(init_point, init_normal)
    plane.rotate(rotation)
    np.testing.assert_array_almost_equal(plane.normal, exp_normal)
    np.testing.assert_array_almost_equal(np.array(plane.reference_point),
                                         exp_point)

def test_update():
    """Tests Plane's ability to update to match another Plane."""
    plane = Plane((0, 0, 0), (0, 0, 1))
    other = Plane((1, 1, 1), (1, 0, 0))
    plane.update(other)
    np.testing.assert_array_almost_equal(plane.normal, other.normal)
    np.testing.assert_array_almost_equal(tuple(plane.reference_point),
                                         tuple(other.reference_point))

def test_get_3_points_on_plane():
    """Test ability to get 3 unique points on a plane."""
    pt = Point(0, 0, 0)
    normal = (0, 0, 1)
    pln = Plane(pt, normal)
    points = conversion.get_3_points_on_plane(pln)
    dot_products = list(map(lambda p : np.dot(tuple(p), pln.normal), points))
    np.testing.assert_array_almost_equal(dot_products, (0, 0, 0))
