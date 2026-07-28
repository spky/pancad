"""Tests for pancad's Plane class."""
from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from pancad.geometry.plane import Plane

if TYPE_CHECKING:
    from tests._typing import ChangeTest

class TestPlaneChanges:
    """Tests for changing Plane properties post-initialization."""

    def test_move_to_point(self, changes_plane_move_to_point: ChangeTest) -> None:
        """Test moving a Plane from its initialized state to different points and orientations."""
        sample, change = changes_plane_move_to_point
        plane = Plane(sample["vectors"]["point"], sample["vectors"]["normal"])
        plane.move_to_point(change["vectors"]["in_point"], change["vectors"].get("in_normal"))
        assert plane.reference_point.cartesian == change["vectors"]["ref_point"]
        assert plane.normal == change["vectors"]["normal"]

    def test_rotation_quat(self, changes_plane_rotation_quat: ChangeTest) -> None:
        """Test that a Plane can rotate with expected reference_point and direction results
        using a quaternion.
        """
        sample, change = changes_plane_rotation_quat
        plane = Plane(sample["vectors"]["point"], sample["vectors"]["normal"])
        plane.rotate(change["quats"]["rotation"])
        assert plane.reference_point.cartesian == pytest.approx(change["vectors"]["ref_point"])
        assert plane.normal == pytest.approx(change["vectors"]["normal"])

    def test_update(self, changes_plane_update: ChangeTest) -> None:
        """Test Plane's ability to update to match another Plane."""
        sample, change = changes_plane_update
        plane = Plane(sample["vectors"]["point"], sample["vectors"]["normal"])
        other = Plane(change["vectors"]["in_point"], change["vectors"]["in_normal"])
        plane.update(other)
        assert plane.reference_point.cartesian == pytest.approx(change["vectors"]["ref_point"])
        assert plane.normal == pytest.approx(change["vectors"]["normal"])
