"""Tests for pancad's Plane class."""
from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
import numpy as np

from pancad.geometry.plane import Plane
from pancad.geometry.point import Point

if TYPE_CHECKING:
    from typing import Callable

    from pancad.utils.pancad_types import Space3DVector

    from tests._typing import GeometrySampleData, ChangeTest

    PlaneMaker = Callable[[GeometrySampleData, pytest.FixtureRequest], Plane]

@pytest.fixture(name="make_plane")
def fixture_make_plane() -> PlaneMaker:
    """Returns a function that converts GeometrySampleData into a Plane based on the request id"""
    def _make_plane(sample: GeometrySampleData, request: pytest.FixtureRequest) -> Plane:
        id_ = request.node.callspec.id
        vectors, scalars = sample["vectors"], sample["scalars"]
        if "point_normal" in id_:
            return Plane(vectors["in_point"], vectors["in_normal"])
        if "point_angles" in id_:
            return Plane.from_point_and_angles(vectors["in_point"],
                                               scalars["phi"], scalars["theta"])
        raise ValueError(f"Unexpected Plane data group: {id_}")
    return _make_plane

@pytest.fixture(name="plane_sample")
def fixture_plane_sample(data_plane_sample: GeometrySampleData,
                         make_plane: PlaneMaker,
                         request: pytest.FixtureRequest) -> Plane:
    """Returns a sample plane to test properties."""
    return make_plane(data_plane_sample, request)

class TestPlaneSampleProperties:
    """Tests whether all sample Plane eleemnts have the expected properties post-initialization"""

    def test_normal(self, plane_sample: Plane, data_plane_sample: GeometrySampleData) -> None:
        """Test sample Plane normal vectors match the expected data file value."""
        assert plane_sample.normal == pytest.approx(data_plane_sample["vectors"]["normal"])

    def test_ref_point(self, plane_sample: Plane, data_plane_sample: GeometrySampleData) -> None:
        """Test sample Plane reference points match the expected data file value."""
        vectors = data_plane_sample["vectors"]
        assert plane_sample.reference_point.cartesian == pytest.approx(vectors["ref_point"])

    def test_len(self, plane_sample: Plane) -> None:
        """Test that all sample planes are 3 dimensional."""
        assert len(plane_sample) == 3

    def test_is_equal(self, plane_sample: Plane) -> None:
        """Test that all the sample Planes can be found equal to themselves."""
        plane_sample.is_equal(plane_sample)

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
