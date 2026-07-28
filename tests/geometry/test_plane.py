"""Tests for pancad's Plane class."""
from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
import numpy as np

from pancad.geometry.plane import Plane
from pancad.geometry.point import Point

if TYPE_CHECKING:
    from pancad.utils.pancad_types import Space3DVector

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

@pytest.mark.parametrize("ref_point, normal", [pytest.param((0, 0, 0), (1, 0, 0), id="xy_plane")])
class TestPlaneInitializationTypes:
    """Tests for initializing Plane elements with different types."""

    def test_tuples(self, ref_point: Space3DVector, normal: Space3DVector) -> None:
        """Test initialization with two tuples."""
        plane = Plane(ref_point, normal)
        assert (plane.normal, plane.reference_point.cartesian) == (normal, ref_point)

    def test_point_and_tuple(self, ref_point: Space3DVector, normal: Space3DVector) -> None:
        """Test initialization with a Point and a tuple."""
        plane = Plane(Point(ref_point), normal)
        assert (plane.normal, plane.reference_point.cartesian) == (normal, ref_point)

    def test_lists(self, ref_point: Space3DVector, normal: Space3DVector) -> None:
        """Test initialization with two lists."""
        plane = Plane(list(ref_point), list(normal))
        assert (plane.normal, plane.reference_point.cartesian) == (normal, ref_point)

    def test_numpy_1ds(self, ref_point: Space3DVector, normal: Space3DVector) -> None:
        """Test initialization with two lists."""
        plane = Plane(np.array(ref_point), np.array(normal))
        assert (plane.normal, plane.reference_point.cartesian) == (normal, ref_point)

    def test_numpy_1d_and_numpy_2d(self, ref_point: Space3DVector, normal: Space3DVector) -> None:
        """Test initialization with two lists."""
        plane = Plane(np.array(ref_point), np.array(normal).reshape(-1, 1))
        assert (plane.normal, plane.reference_point.cartesian) == (normal, ref_point)
