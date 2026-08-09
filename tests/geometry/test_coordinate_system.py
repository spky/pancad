"""Tests for pancad's CoordinateSystem geometry class."""
from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from pancad.constants import ConstraintReference as CR
from pancad.geometry.coordinate_system import CoordinateSystem
from pancad.utils.trigonometry import rotation_2

if TYPE_CHECKING:
    from tests._typing import ChangeTest

@pytest.fixture(name="canon_3d_system")
def fixture_canon_3d_system() -> CoordinateSystem:
    """An unrotated 3D CoordinateSystem centered at the origin."""
    return CoordinateSystem((0, 0, 0))

class TestRotations:
    """Tests for verifying CoordinateSystem element can rotate using matrices and quaternions."""

    def test_rotate_2d_init(self, changes_csys_rotate_2d: ChangeTest) -> None:
        """Test initializing a 2D coordinate system using a rotation matrix."""
        sample, change = changes_csys_rotate_2d
        system = CoordinateSystem(sample["vectors"]["origin"],
                                  rotation_2(change["scalars"]["angle"]))
        assert system.origin.cartesian == pytest.approx(change["vectors"]["origin"])
        assert system.x_axis.direction == pytest.approx(change["vectors"]["x"])
        assert system.y_axis.direction == pytest.approx(change["vectors"]["y"])

    def test_rotate_quat(self, changes_csys_rotate_quat: ChangeTest) -> None:
        """Test initializing a 3D coordinate system using a quaternion."""
        sample, change = changes_csys_rotate_quat
        system = CoordinateSystem(sample["vectors"]["origin"], change["quats"]["rotation"])
        assert system.origin.cartesian == pytest.approx(change["vectors"]["origin"])
        assert system.x_axis.direction == pytest.approx(change["vectors"]["x"])
        assert system.y_axis.direction == pytest.approx(change["vectors"]["y"])
        assert system.z_axis.direction == pytest.approx(change["vectors"]["z"])
        assert system.yz_plane.normal == pytest.approx(change["vectors"]["x"])
        assert system.xz_plane.normal == pytest.approx(change["vectors"]["y"])
        assert system.xy_plane.normal == pytest.approx(change["vectors"]["z"])

    def test_get_quaternion(self, changes_csys_rotate_quat: ChangeTest) -> None:
        """Test whether the quaternion from get_quaternion can replicate the CoordinateSystem."""
        sample, change = changes_csys_rotate_quat
        target = CoordinateSystem(sample["vectors"]["origin"], change["quats"]["rotation"])
        start = CoordinateSystem(sample["vectors"]["origin"])
        assert start.rotate(target.get_quaternion()).is_equal(target)

class TestSpotChecks:
    """Tests for confirming basic functionality of 3D CoordinateSystem elements haven't broken."""

    def test_3d_is_equal(self, canon_3d_system: CoordinateSystem) -> None:
        """Test whether coordinate_systems can compare each other's equality."""
        assert canon_3d_system.is_equal(canon_3d_system)

    def test_3d_repr_dunder(self, canon_3d_system: CoordinateSystem) -> None:
        """Test that the CoordinateSystem repr runs and has info for 3D systems."""
        assert repr(canon_3d_system) == "<CoordinateSystem(0,0,0)X(1,0,0)Y(0,1,0)Z(0,0,1)>"

    def test_3d_move_to_point(self, canon_3d_system: CoordinateSystem) -> None:
        """Test 3D CoordinateSystems can be move to other points."""
        canon_3d_system.move_to_point((1, 1, 1))
        assert canon_3d_system.origin.cartesian == pytest.approx((1,1,1))
        axes = {CR.X: (0, 1, 1), CR.Y: (1, 0, 1), CR.Z: (1, 1, 0)}
        for ref, vec in axes.items():
            assert canon_3d_system.axes[ref].reference_point.cartesian == pytest.approx(vec)
        planes = {CR.XY: (0, 0, 1), CR.XZ: (0, 1, 0), CR.YZ: (1, 0, 0)}
        for ref, vec in planes.items():
            assert canon_3d_system.planes[ref].reference_point.cartesian == pytest.approx(vec)

    def test_3d_update(self, canon_3d_system: CoordinateSystem) -> None:
        """Test that coordinate systems can be updated to other coordinate systems"""
        new = CoordinateSystem((2,2,2))
        canon_3d_system.update(new)
        assert canon_3d_system.origin.cartesian == pytest.approx(new.origin.cartesian)

    def test_2d_repr_dunder(self) -> None:
        """Test that the CoordinateSystem repr runs and has info for 2D systems."""
        assert repr(CoordinateSystem((0, 0))) == "<CoordinateSystem(0,0)X(1,0)Y(0,1)>"
