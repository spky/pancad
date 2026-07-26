"""Tests for pancad's Line class"""
from __future__ import annotations

import itertools
from math import cos, sin, radians
from typing import TYPE_CHECKING

import numpy as np
import quaternion # type: ignore # pylint: disable=unused-import
import pytest

from pancad.utils import trigonometry as trig
from pancad.geometry.point import Point
from pancad.geometry.line import Line, Axis

if TYPE_CHECKING:
    from typing import Type, Any, TypedDict, NotRequired
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

# TODO: Replace Near Zero tests with floating point steps rather than EPS_64

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
        """Test that an 2D axis can rotate with expected reference_point and direction results."""
        sample, change = changes_axis_rotation_2d
        axis = Axis(sample["vectors"]["start"], sample["vectors"]["direction"])
        axis.rotate(trig.rotation_2(change["scalars"]["angle"]))
        assert axis.direction == pytest.approx(change["vectors"]["direction"])
        assert axis.reference_point.cartesian == pytest.approx(change["vectors"]["ref_point"])

    def test_rotation_3d_matrix(self, changes_axis_rotation_3d: ChangeTest) -> None:
        """Test that n 3D axis can rotate with expected reference_point and direction results
        using a rotation matrix.
        """
        sample, change = changes_axis_rotation_3d
        axis = Axis(sample["vectors"]["start"], sample["vectors"]["direction"])
        matrix = trig.yaw_pitch_roll(*[change["scalars"][c] for c in ("yaw", "pitch", "roll")])
        axis.rotate(matrix)
        assert axis.direction == pytest.approx(change["vectors"]["direction"])
        assert axis.reference_point.cartesian == pytest.approx(change["vectors"]["ref_point"])

# TODO: Add tests for each input type initialization method for Line and for Axis.

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

ORIGIN_2D = (0, 0) # 2D Origin Point
ORIGIN_3D = (0, 0, 0) # 3D Origin Point
X_2D = (1, 0) # 2D X Axis Vector
Y_2D = (0, 1) # 2D Y Axis Vector
X_3D = (1, 0, 0) # 3D X Axis Vector
Y_3D = (0, 1, 0) # 3D Y Axis Vector
Z_3D = (0, 0, 1) # 3D Z Axis Vector
SQ2R = 1 / np.sqrt(2) # 1 over the square root of 2
# NOTE: Manual test input angles in degrees

QUAT_ROTATIONS = [
    # Init Point, Initial Direction, Rotation Axis Vector, Rotation Angle, Expected, Id Prefix
    (ORIGIN_3D, X_3D, (0, 0, 0), 0, X_3D, "q_unrotated_x_zero_axis"),
    (ORIGIN_3D, X_3D, (1, 0, 0), 0, X_3D, "q_unrotated_x_axis"),
    (ORIGIN_3D, X_3D, (1, 0, 0), 90, X_3D, "q_rotate_x_around_x"),
    (ORIGIN_3D, X_3D, (0, 1, 0), 90, (0, 0, -1), "q_rotate_x_to_-z"),
    (ORIGIN_3D, X_3D, (0, 1, 0), -90, Z_3D, "q_rotate_x_to_+z"),
    (ORIGIN_3D, X_3D, (0, 1, 0), 270, Z_3D, "q_opposite_rotate_x_to_+z"),
    (ORIGIN_3D, X_3D, (0, 1, 0), 180, (-1, 0, 0), "q_rotate_x_to_-x"),
    (ORIGIN_3D, X_3D, (0, 1, 0), 135, (-SQ2R, 0, -SQ2R), "q_rotate_x_135_around_y"),
    (ORIGIN_3D, Z_3D, (0, 1, 0), 135, (SQ2R, 0, -SQ2R), "q_rotate_z_135_around_y"),
]

def _quaternion_params(rotations):
    """Generates the list of pytest parameters for testing quaternion rotation."""
    params = []
    for point, initial, rotation_axis, angle, expected, id_ in rotations:
        quat_w = cos(radians(angle / 2))
        quat_ijk = map(lambda x, y: x * sin(radians(y) / 2),
                       rotation_axis, itertools.repeat(angle))
        quat = quaternion.quaternion(quat_w, *quat_ijk)
        test_id = "_".join([id_, str(angle), str(rotation_axis), str(expected)])
        param = pytest.param(point, initial, quat, expected, id=test_id)
        params.append(param)
    return params

@pytest.mark.parametrize(
    "point, initial, rotation, expected",
    [
        *_quaternion_params(QUAT_ROTATIONS),
    ]
)
def test_rotate_axis(point, initial, rotation, expected) -> None:
    """Tests for Axis rotation with quaternions and rotation matrices.

    :param point: Axis definition point.
    :param initial: Initial axis direction.
    :param rotation: A quaternion or rotation matrix.
    :param expected: Expected axis direction result.
    """
    axis = Axis(point, initial)
    rotated = axis.rotate(rotation).direction
    print(axis, rotated)
    assert np.allclose(rotated, expected)

@pytest.mark.parametrize(
    "point, direction, rotation, msg",
    [
        pytest.param(ORIGIN_2D, X_2D, np.quaternion(1, 0, 0, 0), "Cannot rotate 2D", id="2d_quat"),
    ]
)
def test_rotate_axis_exceptions(point, direction, rotation, msg) -> None:
    """Tests for handling axis rotation errors."""
    axis = Axis(point, direction)
    with pytest.raises(ValueError, match=msg):
        axis.rotate(rotation)
