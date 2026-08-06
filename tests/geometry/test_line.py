"""Tests for pancad's Line class"""
from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pytest

from pancad.utils import trigonometry as trig, quat
from pancad.geometry.point import Point
from pancad.geometry.line import Line, Axis

if TYPE_CHECKING:
    from collections.abc import Callable

    from pancad.utils.pancad_types import SpaceVector, Numpy2D
    from tests._typing import GeometrySampleData, ChangeTest

    LineMaker = Callable[[GeometrySampleData, pytest.FixtureRequest], Line]

@pytest.fixture(name="make_line")
def fixture_make_line() -> LineMaker:
    """Returns a function that converts GeometrySampleData into a Line based on the fixture
    request id.
    """
    def _make_line(sample: GeometrySampleData, request: pytest.FixtureRequest) -> Line:
        id_ = request.node.callspec.id
        vectors, scalars = sample["vectors"], sample["scalars"]
        if "two_point_lines" in id_:
            return Line.from_two_points(vectors["start"], vectors["end"])
        if "slope_y_intercept_lines" in id_:
            return Line.from_slope_and_y_intercept(scalars["slope"], scalars["intercept"])
        if "point_direction_lines" in id_:
            return Line(Point(vectors["start"]), vectors["in_direction"])
        if "point_angle_lines" in id_:
            return Line.from_point_and_angle(vectors["start"], scalars["phi"],
                                             scalars.get("theta"))
        raise ValueError(f"Unexpected line data group: {id_}")
    return _make_line

@pytest.fixture(name="line_sample")
def fixture_line_sample(data_line_sample: GeometrySampleData,
                        make_line: LineMaker,
                        request: pytest.FixtureRequest) -> Line:
    """Returns a sample line to test properties."""
    return make_line(data_line_sample, request)

@pytest.fixture(name="axis_sample")
def fixture_axis_sample(data_axis_sample: GeometrySampleData) -> Axis:
    """Returns a sample axis to test properties."""
    vectors = data_axis_sample["vectors"]
    return Axis(vectors["start"], vectors["direction"])

@pytest.fixture(name="slope_intercept_sample")
def fixture_slope_intercept_sample(data_line_sample_slope_y_intercept_lines: GeometrySampleData,
                                   make_line: LineMaker,
                                   request: pytest.FixtureRequest) -> Line:
    """Returns a line that was generated with a slope and y intercept."""
    return make_line(data_line_sample_slope_y_intercept_lines, request)

class TestAxisSampleProperties:
    """Tests for whether all sample Axis elements have the corresponding expected properties after
    initialization.
    """

    def test_direction(self, axis_sample: Axis, data_axis_sample: GeometrySampleData) -> None:
        """Test whether the directions of the sample axes match the expected directions."""
        assert axis_sample.direction == pytest.approx(data_axis_sample["vectors"]["direction"])

    def test_ref_point(self, axis_sample: Axis, data_axis_sample: GeometrySampleData) -> None:
        """Test whether the reference_point of the sample axes match the expected points."""
        point = data_axis_sample["vectors"]["ref_point"]
        assert axis_sample.reference_point.cartesian == pytest.approx(point)

    def test_len(self, axis_sample: Line) -> None:
        """Tests that the length of sample axes matches the dimension of its direction."""
        assert len(axis_sample) == len(axis_sample.direction)

    def test_is_equal(self, axis_sample: Line) -> None:
        """Test that all the sample axes can be found equal to themselves."""
        axis_sample.is_equal(axis_sample)

class TestLineSampleProperties:
    """Tests for whether all sample Lines have the corresponding expected properties after
    initialization.
    """

    def test_direction(self, line_sample: Line, data_line_sample: GeometrySampleData) -> None:
        """Test whether the directions of the sample lines match the expected directions."""
        expected = data_line_sample["vectors"]["unique_direction"]
        assert line_sample.direction == pytest.approx(expected)

    def test_ref_point(self, line_sample: Line, data_line_sample: GeometrySampleData) -> None:
        """Test whether the reference_point of the sample lines match the expected points."""
        expected = data_line_sample["vectors"]["ref_point"]
        assert line_sample.reference_point.cartesian == pytest.approx(expected)

    def test_len(self, line_sample: Line) -> None:
        """Tests that the length of sample lines matches the dimension of its direction."""
        assert len(line_sample) == len(line_sample.direction)

    def test_slope_intercept(self, slope_intercept_sample: Line,
                             data_line_sample_slope_y_intercept_lines: GeometrySampleData
                             ) -> None:
        """Test that the slopes and intercepts of the sample lines are calculated correctly. Only
        tests the line if slope and intercept are in the test data file.
        """
        expected = data_line_sample_slope_y_intercept_lines
        assert slope_intercept_sample.slope == expected["scalars"]["slope"]
        assert slope_intercept_sample.y_intercept == expected["scalars"]["intercept"]

    def test_direction_polar_spherical(self, line_sample: Line,
                                       data_line_sample: GeometrySampleData) -> None:
        """Test that any data file defined polar or spherical vectors of the sample lines match
        the calculated ones.
        """
        if isinstance(line_sample, Axis) or "polar_spherical" not in data_line_sample["vectors"]:
            return
        expected_vector = data_line_sample["vectors"]["polar_spherical"]
        if len(expected_vector) == 2:
            np.testing.assert_array_almost_equal(line_sample.direction_polar, expected_vector)
        else:
            np.testing.assert_array_almost_equal(line_sample.direction_spherical, expected_vector)

    def test_is_equal(self, line_sample: Line) -> None:
        """Test that all the sample lines can be found equal to themselves."""
        line_sample.is_equal(line_sample)

class TestLineChanges:
    """Tests for changing Line properties post-initialization."""

    def test_move_to_point(self, changes_line_move_to_point: ChangeTest) -> None:
        """Test moving a line from its initialized state to different points and orientations."""
        sample, change = changes_line_move_to_point
        line = Line(Point(sample["vectors"]["start"]), sample["vectors"]["direction"])
        line.move_to_point(change["vectors"]["point"],
                           change["scalars"].get("phi"), change["scalars"].get("theta"))
        assert line.direction == pytest.approx(change["vectors"]["direction"])
        assert line.reference_point.cartesian == pytest.approx(change["vectors"]["ref_point"])

    def test_direction_setter(self, changes_line_direction_setter: ChangeTest) -> None:
        """Test setting a line's direction and the impacts on the reference point."""
        sample, change = changes_line_direction_setter
        line = Line(Point(sample["vectors"]["start"]), sample["vectors"]["direction"])
        line.direction = change["vectors"]["vector"]
        assert line.direction == pytest.approx(change["vectors"]["direction"])
        assert line.reference_point.cartesian == pytest.approx(change["vectors"]["ref_point"])

    def test_polar_direction_setter(self, changes_line_polar_direction_setter: ChangeTest
                                    ) -> None:
        """Test setting a line's polar direction and the impacts on the reference point."""
        sample, change = changes_line_polar_direction_setter
        line = Line(Point(sample["vectors"]["start"]), sample["vectors"]["direction"])
        line.direction_polar = change["vectors"]["new"]
        assert line.direction == pytest.approx(change["vectors"]["direction"])
        assert line.reference_point.cartesian == pytest.approx(change["vectors"]["ref_point"])

    def test_spherical_direction_setter(self, changes_line_spherical_direction_setter: ChangeTest
                                        ) -> None:
        """Test setting a line's spherical direction and the impacts on the reference point."""
        sample, change = changes_line_spherical_direction_setter
        line = Line(Point(sample["vectors"]["start"]), sample["vectors"]["direction"])
        line.direction_spherical = change["vectors"]["new"]
        assert line.direction == pytest.approx(change["vectors"]["direction"])
        assert line.reference_point.cartesian == pytest.approx(change["vectors"]["ref_point"])

    def test_update(self, changes_line_update: ChangeTest) -> None:
        """Test updating a line with another line."""
        sample, change = changes_line_update
        line = Line(Point(sample["vectors"]["start"]), sample["vectors"]["direction"])
        other = Line(Point(change["vectors"]["start"]), change["vectors"]["direction"])
        line.update(other)
        assert line.is_equal(other)

class TestAxisChanges:
    """Tests for changing Axis properties post-initialization."""

    def test_direction_setter(self, changes_axis_direction_setter: ChangeTest) -> None:
        """Test setting an axis' direction and the impacts on the reference point."""
        sample, change = changes_axis_direction_setter
        axis = Axis(sample["vectors"]["start"], sample["vectors"]["direction"])
        axis.direction = change["vectors"]["direction"]
        assert axis.direction == pytest.approx(change["vectors"]["direction"])
        assert axis.reference_point.cartesian == pytest.approx(change["vectors"]["ref_point"])

    def test_rotation_2d(self, changes_axis_rotation_2d: ChangeTest) -> None:
        """Test that a 2D axis can rotate with expected reference_point and direction results."""
        sample, change = changes_axis_rotation_2d
        axis = Axis(sample["vectors"]["start"], sample["vectors"]["direction"])
        axis.rotate(trig.rotation_2(change["scalars"]["angle"]))
        assert axis.direction == pytest.approx(change["vectors"]["direction"])
        assert axis.reference_point.cartesian == pytest.approx(change["vectors"]["ref_point"])

    def test_rotation_3d_matrix(self, changes_axis_rotation_3d: ChangeTest) -> None:
        """Test that a 3D axis can rotate with expected reference_point and direction results
        using a rotation matrix.
        """
        sample, change = changes_axis_rotation_3d
        axis = Axis(sample["vectors"]["start"], sample["vectors"]["direction"])
        matrix = trig.yaw_pitch_roll(*[change["scalars"][c] for c in ("yaw", "pitch", "roll")])
        axis.rotate(matrix)
        assert axis.direction == pytest.approx(change["vectors"]["direction"])
        assert axis.reference_point.cartesian == pytest.approx(change["vectors"]["ref_point"])

    def test_rotation_quat(self, changes_axis_rotation_quat: ChangeTest) -> None:
        """Test that a 3D axis can rotate with expected reference_point and direction results
        using a quaternion.
        """
        sample, change = changes_axis_rotation_quat
        axis = Axis(sample["vectors"]["start"], sample["vectors"]["direction"])
        axis.rotate(change["quats"]["rotation"])
        assert axis.direction == pytest.approx(change["vectors"]["direction"])
        assert axis.reference_point.cartesian == pytest.approx(change["vectors"]["ref_point"])

@pytest.mark.parametrize(
    "ref_point, direction",
    [pytest.param((0, 0), (1, 0), id="2d"), pytest.param((0, 0, 0), (1, 0, 0), id="3d")],
)
class TestLineInitializationTypes:
    """Tests for initializing Line elements with different types."""

    def test_point_space_vector(self, ref_point: SpaceVector, direction: SpaceVector) -> None:
        """Test that Line can be initialized by a Point and a SpaceVector."""
        line = Line(Point(ref_point), direction)
        assert line.direction == direction
        assert line.reference_point.cartesian == ref_point

    def test_point_list(self, ref_point: SpaceVector, direction: SpaceVector) -> None:
        """Test that Line can be initialized by a Point and a list of floats."""
        line = Line(Point(ref_point), list(direction))
        assert line.direction == direction
        assert line.reference_point.cartesian == ref_point

    def test_point_numpy_1d(self, ref_point: SpaceVector, direction: SpaceVector) -> None:
        """Test that Line can be initialized by a Point and a 1D numpy array."""
        line = Line(Point(ref_point), np.array(direction))
        assert line.direction == direction
        assert line.reference_point.cartesian == ref_point

    def test_point_numpy_2d(self, ref_point: SpaceVector, direction: SpaceVector) -> None:
        """Test that Line can be initialized by a Point and a 1D numpy array."""
        line = Line(Point(ref_point), np.array(direction).reshape(-1, 1))
        assert line.direction == direction
        assert line.reference_point.cartesian == ref_point

@pytest.mark.parametrize(
    "ref_point, direction",
    [pytest.param((0, 0), (1, 0), id="2d"), pytest.param((0, 0, 0), (1, 0, 0), id="3d")],
)
class TestAxisInitializationTypes:
    """Tests for initializing Axis elements with different types."""

    def test_tuples(self, ref_point: SpaceVector, direction: SpaceVector) -> None:
        """Test that Axis can be initialized by two tuples."""
        axis = Axis(ref_point, direction)
        assert axis.direction == direction
        assert axis.reference_point.cartesian == ref_point

    def test_point_and_tuple(self, ref_point: SpaceVector, direction: SpaceVector) -> None:
        """Test that Axis can be initialized by a Point and a tuple."""
        axis = Axis(Point(ref_point), direction)
        assert axis.direction == direction
        assert axis.reference_point.cartesian == ref_point

    def test_tuple_and_list(self, ref_point: SpaceVector, direction: SpaceVector) -> None:
        """Test that Axis can be initialized by a tuple and a list of floats."""
        axis = Axis(ref_point, list(direction))
        assert axis.direction == direction
        assert axis.reference_point.cartesian == ref_point

    def test_numpy_1ds(self, ref_point: SpaceVector, direction: SpaceVector) -> None:
        """Test that Axis can be initialized by two 1D numpy arrays."""
        axis = Axis(np.array(ref_point), np.array(direction))
        assert axis.direction == direction
        assert axis.reference_point.cartesian == ref_point

    def test_numpy_1d_and_numpy_2d(self, ref_point: SpaceVector, direction: SpaceVector) -> None:
        """Test that Axis can be initialized by two 1D numpy arrays."""
        axis = Axis(np.array(ref_point), np.array(direction).reshape(-1, 1))
        assert axis.direction == direction
        assert axis.reference_point.cartesian == ref_point

class TestSpotChecks:
    """Test the initialization of Line/Axis properties hasn't unexpectedly changed. These tests
    just spot check dunders and exceptions to catch if a basic function has accidentally been
    broken.
    """

    def test_line_str_dunder(self) -> None:
        """Test that the string dunder for one line is maintained and doesn't change."""
        test = Line.from_two_points((1,0,0), (1,10,0))
        assert str(test) == "<Line(1,0,0)d(0,1,0)>"

    def test_from_two_points_same_point(self) -> None:
        """Test that initializing a Line with two of the same point raises a ValueError."""
        with pytest.raises(ValueError):
            Line.from_two_points((1, 1), (1, 1))

    @pytest.mark.parametrize(
        "point, direction, rotation, msg",
        [
            pytest.param((0, 0), (1, 0), np.identity(3), "2D Axis with", id="2d_with_3d"),
            pytest.param((0, 0, 0), (1, 0, 0), np.identity(2), "3D Axis with", id="3d_with_2d"),
        ]
    )
    def test_rotate_matrix_dimension_mismatch(self, point: SpaceVector, direction: SpaceVector,
                                              rotation: Numpy2D, msg: str) -> None:
        """Tests that rotating 2D/3D Axis with a 3D/2D rotation matrix raises a ValueError."""
        axis = Axis(point, direction)
        with pytest.raises(ValueError, match=msg):
            axis.rotate(rotation)

    def test_rotate_quaternion_dimension_mismatch(self) -> None:
        """Tests that rotating 2D Axis with a quaternion raises a ValueError."""
        axis = Axis((0, 0), (1, 0))
        with pytest.raises(ValueError, match="2D Axis with"):
            axis.rotate(quat.Quat(1, 0, 0, 0))

class TestDirectionAroundOrigin:
    """Tests for ensuring the validity of the Line direction behavior around the origin point."""

    def test_smallest_direction(self, min_full_precision_squareable: float) -> None:
        """Test the ability to initialize Line's direction using a vector with the smallest
        possible float that can still be squared on the system.
        """
        assert Line(Point(0, 0, 0), (min_full_precision_squareable, 0, 0)).direction == (1, 0, 0)

    def test_smallest_unique_direction(self, min_full_precision_squareable: float) -> None:
        """Test the ability to make the direction vector unique even when the input components are
        very close to 0.
        """
        assert Line(Point(0, 0, 0), (0, 0, -min_full_precision_squareable)).direction == (0, 0, 1)

    def test_two_smallest_components(self, min_full_precision_squareable: float) -> None:
        """Test Line direction initialization with two components starting as close to 0 as
        possible.
        """
        expected = tuple(np.array((1, 1, 0)) / np.linalg.norm((1, 1, 0)))
        in_direction = (min_full_precision_squareable, min_full_precision_squareable, 0)
        assert Line(Point(0, 0, 0), in_direction).direction == expected

    def test_subnormal_direction(self, min_squareable: float) -> None:
        """Test that the direction raises a ValueError if the vector is so small that roundoff
        makes the results unreliable.
        """
        with pytest.raises(ValueError, match="^Normalization failed"):
            assert Line(Point(0, 0, 0), (min_squareable, 0, 0)).direction == (1, 0, 0)
