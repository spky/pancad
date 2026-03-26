"""Tests for pancad's CoordinateSystem geometry class."""
from __future__ import annotations

from itertools import repeat
from math import radians, sqrt, cos, sin
from typing import TYPE_CHECKING
from pprint import pp

import pytest
import numpy as np
import quaternion # pylint: disable=unused-import

from pancad.constants import ConstraintReference as CR
from pancad.geometry.coordinate_system import CoordinateSystem
from pancad.utils.trigonometry import rotation_2, to_1d_tuple

if TYPE_CHECKING:
    from numbers import Real
    from pancad.utils.pancad_types import (
        SpaceVector, Space3DVector, Space2DVector
    )

PLANE_REFS = (CR.XY, CR.XZ, CR.YZ)
AXIS_REFS = (CR.X, CR.Y, CR.Z)

# Canonical Axes
X_3D = np.array([1, 0, 0])
Y_3D = np.array([0, 1, 0])
Z_3D = np.array([0, 0, 1])

def _rotate_2d_params(origin: Space2DVector):
    """Return parameters for testing 2D coordinate system rotation during
    initialization.

    :param origin: The origin point of the coordinate system.
    """
    params = []
    x_axis = (1, 0)
    y_axis = to_1d_tuple(x_axis @ rotation_2(radians(-90)))
    init_axes = {CR.X: x_axis, CR.Y: y_axis}
    for angle in range(0, 405, 45):
        rotation = rotation_2(radians(angle))
        expected = {ref: rotation @ v for ref, v in init_axes.items()}
        expected[CR.ORIGIN] = origin
        id_ = f"2d_Origin{origin}_X{x_axis}_Y{y_axis}_Rot{angle}deg"
        params.append(pytest.param(origin, rotation, expected, id=id_))
    params.append( # Add case for when the rotation is set to None
        pytest.param(origin, None, {CR.ORIGIN: origin, **init_axes},
                     id=f"2d_Origin{origin}_RotNone_unrotated")
    )
    return params

# The quaternion inputs are split into two dicts to make it slightly easier to read:
# one for the rotation axis and the angle to rotate around, and one for the
# expected axes per test. The dicts share the test id as their keys.

QUAT_INIT_ROTATIONS = {
    # Rotation axis, right-hand (thumb aligned with axis) rotation angle (in degrees)
    "no_rotate_around_zero_axis": [(0, 0, 0), 0],
    "full_rotate_around_x_axis": [X_3D, 360],
    "full_rotate_around_y_axis": [X_3D, 360],
    "full_rotate_around_z_axis": [X_3D, 360],
    "rotate_x_to_-x_around_y": [Y_3D, 180],
    "rotate_x_to_-x_around_z": [Z_3D, 180],
    "rotate_y_to_-y_around_x": [X_3D, 180],
    "rotate_y_to_-y_around_z": [Z_3D, 180],
    "rotate_z_to_-z_around_x": [X_3D, 180],
    "rotate_z_to_-z_around_y": [Y_3D, 180],
    "rotate_x_to_z_around_y": [Y_3D, -90],
    "rotate_x_to_y_around_z": [Z_3D, 90],
    "rotate_x_45_around_z": [Z_3D, 45],
    "rotate_x_135_around_z": [Z_3D, 135],
    "rotate_x_225_around_z": [Z_3D, 225],
    "rotate_x_315_around_z": [Z_3D, 315],
    "rotate_x_45_around_y": [Y_3D, 45],
    "rotate_x_135_around_y": [Y_3D, 135],
    "rotate_x_225_around_y": [Y_3D, 225],
    "rotate_x_315_around_y": [Y_3D, 315],
    "rotate_z_45_around_x": [X_3D, 45],
    "rotate_z_135_around_x": [X_3D, 135],
    "rotate_z_225_around_x": [X_3D, 225],
    "rotate_z_315_around_x": [X_3D, 315],
}

INIT_ROTATION_AXIS_RESULTS = {
    "full_rotate_around_x_axis": [X_3D, Y_3D, Z_3D],
    "full_rotate_around_y_axis": [X_3D, Y_3D, Z_3D],
    "full_rotate_around_z_axis": [X_3D, Y_3D, Z_3D],
    "no_rotate_around_zero_axis": [X_3D, Y_3D, Z_3D],
    "rotate_x_to_-x_around_y": [-X_3D, Y_3D, -Z_3D],
    "rotate_x_to_-x_around_z": [-X_3D, -Y_3D, Z_3D],
    "rotate_y_to_-y_around_x": [X_3D, -Y_3D, -Z_3D],
    "rotate_y_to_-y_around_z": [-X_3D, -Y_3D, Z_3D],
    "rotate_z_to_-z_around_x": [X_3D, -Y_3D, -Z_3D],
    "rotate_z_to_-z_around_y": [-X_3D, Y_3D, -Z_3D],
    "rotate_x_to_z_around_y": [Z_3D, Y_3D, -X_3D],
    "rotate_x_to_y_around_z": [Y_3D, -X_3D, Z_3D],
    "rotate_x_45_around_z": [(1/sqrt(2), 1/sqrt(2), 0), (-1/sqrt(2), 1/sqrt(2), 0), Z_3D],
    "rotate_x_135_around_z": [(-1/sqrt(2), 1/sqrt(2), 0), (-1/sqrt(2), -1/sqrt(2), 0), Z_3D],
    "rotate_x_225_around_z": [(-1/sqrt(2), -1/sqrt(2), 0), (1/sqrt(2), -1/sqrt(2), 0), Z_3D],
    "rotate_x_315_around_z": [(1/sqrt(2), -1/sqrt(2), 0), (1/sqrt(2), 1/sqrt(2), 0), Z_3D],
    "rotate_x_45_around_y": [(1/sqrt(2), 0, -1/sqrt(2)), Y_3D, (1/sqrt(2), 0, 1/sqrt(2))],
    "rotate_x_135_around_y": [(-1/sqrt(2), 0, -1/sqrt(2)), Y_3D, (1/sqrt(2), 0, -1/sqrt(2))],
    "rotate_x_225_around_y": [(-1/sqrt(2), 0, 1/sqrt(2)), Y_3D, (-1/sqrt(2), 0, -1/sqrt(2))],
    "rotate_x_315_around_y": [(1/sqrt(2), 0, 1/sqrt(2)), Y_3D, (-1/sqrt(2), 0, 1/sqrt(2))],
    "rotate_z_45_around_x": [X_3D, (0, 1/sqrt(2), 1/sqrt(2)), (0, -1/sqrt(2), 1/sqrt(2))],
    "rotate_z_135_around_x": [X_3D, (0, -1/sqrt(2), 1/sqrt(2)), (0, -1/sqrt(2), -1/sqrt(2))],
    "rotate_z_225_around_x": [X_3D, (0, -1/sqrt(2), -1/sqrt(2)), (0, 1/sqrt(2), -1/sqrt(2))],
    "rotate_z_315_around_x": [X_3D, (0, 1/sqrt(2), -1/sqrt(2)), (0, 1/sqrt(2), 1/sqrt(2))],
}

def _rotate_3d_quaternion_params(origin: Space3DVector):
    """Return parameters for testing 3D coordinate system rotation using
    quaternions during initialization.

    :param origin: The origin point of the coordinate system.
    """
    params = []
    for id_, (rotation_axis, angle) in QUAT_INIT_ROTATIONS.items():
        quat_w = cos(radians(angle / 2))
        quat_ijk = map(lambda a, b: a * sin(radians(b) / 2),
                       rotation_axis, repeat(angle))
        quat = np.quaternion(quat_w, *quat_ijk)
        x_vec, y_vec, z_vec = INIT_ROTATION_AXIS_RESULTS[id_]
        expected = {
            CR.ORIGIN: origin,
            CR.X: x_vec, CR.Y: y_vec, CR.Z: z_vec,
            CR.XY: z_vec, CR.XZ: y_vec, CR.YZ: x_vec,
        }
        test_id = f"Origin{origin}_{id_}"
        params.append(pytest.param(origin, quat, expected, id=test_id))
    return params

@pytest.mark.parametrize(
    "origin, rotation, expected",
    [
        *_rotate_2d_params((0, 0)),
        *_rotate_2d_params((1, 1)), # set of 2D tests offset from origin
        *_rotate_3d_quaternion_params((0, 0, 0)),
        *_rotate_3d_quaternion_params((1, 1, 1)),
    ]
)
def test_init_with_rotations(origin, rotation, expected):
    """Tests initializing CoordinateSystems at different origin points and
    orientations.
    """
    cs = CoordinateSystem(origin, rotation)
    pp(expected)
    for ref, geometry in cs.children.items():
        if ref == CR.ORIGIN:
            print(geometry.self_reference, geometry, expected[ref])
            assert geometry.cartesian == pytest.approx(expected[ref])
        if ref in AXIS_REFS:
            print(geometry.self_reference, geometry, expected[ref])
            assert geometry.direction == pytest.approx(expected[ref])
        if ref in PLANE_REFS:
            print(geometry.self_reference, geometry, expected[ref])
            assert geometry.normal == pytest.approx(expected[ref])

@pytest.mark.parametrize(
    "origin, rotation, _",
    [*_rotate_3d_quaternion_params((0, 0, 0))]
)
def test_get_quaternion(origin, rotation, _):
    """Test that the quaternions from get_quaternion actually rotate canon
    coordinate systems to match the target coordinate systems.
    """
    target_cs = CoordinateSystem(origin, rotation)
    quat = target_cs.get_quaternion()
    start_cs = CoordinateSystem((0, 0, 0))
    start_cs.rotate(quat)
    assert start_cs.is_equal(target_cs)

@pytest.fixture(name="canon_3d_system")
def fixture_canon_3d_system():
    """An unrotated 3D CoordinateSystem centered at the origin."""
    return CoordinateSystem((0, 0, 0))

def test_is_equal_3d(canon_3d_system):
    """Test whether coordinate_systems can compare each other's equality."""
    assert canon_3d_system.is_equal(canon_3d_system)

def test_2d_repr_dunder():
    """Test that the CoordinateSystem repr runs and has info for 2D systems."""
    assert repr(CoordinateSystem((0, 0))) == "<CoordinateSystem(0,0)X(1,0)Y(0,1)>"

def test_3d_repr_dunder(canon_3d_system):
    """Test that the CoordinateSystem repr runs and has info for 3D systems."""
    assert repr(canon_3d_system) == "<CoordinateSystem(0,0,0)X(1,0,0)Y(0,1,0)Z(0,0,1)>"

def test_3d_move_to_point(canon_3d_system):
    """Test 3d CoordinateSystems can be move to other points."""
    canon_3d_system.move_to_point((1, 1, 1))
    assert canon_3d_system.origin.cartesian == pytest.approx((1,1,1))
    axes = {CR.X: (0, 1, 1), CR.Y: (1, 0, 1), CR.Z: (1, 1, 0)}
    for ref, vec in axes.items():
        axis = canon_3d_system.get_reference(ref)
        assert axis.reference_point.cartesian == pytest.approx(vec)
    planes = {CR.XY: (0, 0, 1), CR.XZ: (0, 1, 0), CR.YZ: (1, 0, 0)}
    for ref, vec in planes.items():
        plane = canon_3d_system.get_reference(ref)
        assert plane.reference_point.cartesian == pytest.approx(vec)

def test_update(canon_3d_system):
    """Test that coordinate systems can be updated to other coordinate systems"""
    new = CoordinateSystem((2,2,2))
    canon_3d_system.update(new)
    assert canon_3d_system.origin.cartesian == pytest.approx(new.origin.cartesian)
