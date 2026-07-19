"""Tests for pancad's Line class"""
from __future__ import annotations

import itertools
import math
from math import cos, sin, radians
import unittest
from typing import TYPE_CHECKING

import numpy as np
import quaternion # type: ignore # pylint: disable=unused-import
import pytest

from pancad.utils import trigonometry as trig
from pancad.geometry import spatial_relations
from pancad.geometry.point import Point
from pancad.geometry.line import Line, Axis

if TYPE_CHECKING:
    from typing import Type, Any, TypedDict, NotRequired
    from collections.abc import Callable

    from pancad.utils.pancad_types import SpaceVector, PolarVector, SphericalVector

@pytest.fixture(name="sample_lines")
def fixture_sample_lines() -> list[Line | Axis]:
                         # two_point_lines: list[Line],
                         # point_direction_lines: list[Line]) -> list[Line]:
    """Returns a list of Lines and Axes to test Line properties with. Added to by other
    fixtures.
    """
    return []
    # return two_point_lines + point_direction_lines

@pytest.fixture(name="line_vectors")
def fixture_line_data() -> list[dict[str, SpaceVector]]:
    """Returns a list of line parameters and expected values to test Line properties with. Added
    to by other fixtures.
    """
    return []

@pytest.fixture(name="two_point_lines", autouse=True)
def fixture_two_point_lines(geometry_samples: dict[str, Any],
                            sample_lines: list[Line | Axis],
                            line_vectors: list[dict[str, SpaceVector]],
                            read_vector: Callable[[Any, bool], SpaceVector]) -> None:
    """Adds a list of lines defined by two points to sample_lines."""
    for params in geometry_samples["two_point_lines"]:
        data: dict[str, SpaceVector] = {}
        for key in ("start", "end", "unique_direction", "ref_point"):
            data[key] = read_vector(params["vectors"][key], key == "unique_direction")
        if polar_spherical := params["vectors"].get("polar_spherical"):
            ps_vector = read_vector(polar_spherical, False)
            if len(ps_vector) == 2:
                r, phi = ps_vector
                data["polar_spherical"] = (r, math.radians(phi))
            else:
                r, phi, theta = ps_vector
                data["polar_spherical"] = (r, math.radians(phi), math.radians(theta))
        sample_lines.append(Line.from_two_points(data["start"], data["end"]))
        line_vectors.append(data)

@pytest.fixture(name="point_direction_lines", autouse=True)
def fixture_point_direction_lines(geometry_samples: dict[str, Any],
                                  sample_lines: list[Line | Axis],
                                  line_vectors: list[dict[str, SpaceVector]],
                                  read_vector: Callable[[Any, bool], SpaceVector]) -> None:
    """Adds a list of lines defined by a point and a direction to sample_lines."""
    for params in geometry_samples["point_direction_lines"]:
        data: dict[str, SpaceVector] = {}
        for key in ("start", "in_direction", "unique_direction", "ref_point"):
            data[key] = read_vector(params["vectors"][key], key == "unique_direction")
        sample_lines.append(Line(Point(data["start"]), data["in_direction"]))
        line_vectors.append(data)

@pytest.fixture(name="point_direction_axes", autouse=True)
def fixture_point_direction_axes(geometry_samples: dict[str, Any],
                                 sample_lines: list[Line | Axis],
                                 line_vectors: list[dict[str, SpaceVector]],
                                 read_vector: Callable[[Any, bool], SpaceVector]) -> None:
    """Adds a list of axes defined by a point and a direction to sample_lines."""
    for params in geometry_samples["point_direction_lines"]:
        data: dict[str, SpaceVector] = {}
        for key in ("start", "in_direction", "ref_point"):
            data[key] = read_vector(params["vectors"][key], False)
        data["unique_direction"] = read_vector(params["vectors"]["in_direction"], True)
        sample_lines.append(Axis(Point(data["start"]), data["in_direction"]))
        line_vectors.append(data)

@pytest.fixture(name="slope_y_intercept_lines", autouse=True)
def fixture_slope_y_intercept_lines(geometry_samples: dict[str, Any],
                                    sample_lines: list[Line | Axis],
                                    line_vectors: list[dict[str, SpaceVector]],
                                    read_vector: Callable[[Any, bool], SpaceVector]
                                    ) -> tuple[list[Line], list[dict[str, float]]]:
    """Adds a list of lines defined by a slope and y intercept to sample_lines."""
    vectors: list[dict[str, SpaceVector]] = []
    lines: list[Line] = []
    line_constants: list[dict[str, float]] = []
    for params in geometry_samples["slope_y_intercept_lines"]:
        vectors.append(
            {
                "ref_point": read_vector(params["vectors"]["ref_point"], False),
                "unique_direction": read_vector(params["vectors"]["unique_direction"], True),
            }
        )
        constants = {k: float(params["scalars"][k]) for k in ("slope", "intercept")}
        lines.append(Line.from_slope_and_y_intercept(constants["slope"], constants["intercept"]))
        line_constants.append(constants)
    line_vectors.extend(vectors)
    sample_lines.extend(lines)
    return lines, line_constants

@pytest.fixture(name="point_angle_lines", autouse=True)
def fixture_point_angle_lines(geometry_samples: dict[str, Any],
                              sample_lines: list[Line | Axis],
                              line_vectors: list[dict[str, SpaceVector]],
                              read_vector: Callable[[Any, bool], SpaceVector]) -> None:
    """Adds a list of lines defined by a point and 1 (or 2 if 3D) angles to sample_lines. Also
    adds the expected polar_spherical vector since it's how the line is defined.
    """
    for params in geometry_samples["point_angle_lines"]:
        data: dict[str, SpaceVector] = {}
        for key in ("start", "ref_point"):
            data[key] = read_vector(params["vectors"][key], False)
        data["unique_direction"] = read_vector(params["vectors"]["unique_direction"], True)
        if polar_spherical := params["vectors"].get("polar_spherical"):
            ps_vector = read_vector(polar_spherical, False)
            if len(ps_vector) == 2:
                r, expected_phi = ps_vector
                data["polar_spherical"] = (r, math.radians(expected_phi))
            else:
                r, expected_phi, expected_theta = ps_vector
                data["polar_spherical"] = (r, math.radians(expected_phi),
                                           math.radians(expected_theta))
        phi = math.radians(params["scalars"]["phi"])
        if "theta" in params["scalars"]:
            theta = math.radians(params["scalars"]["theta"])
            sample_lines.append(Line.from_point_and_angle(data["start"], phi, theta))
        else:
            sample_lines.append(Line.from_point_and_angle(data["start"], phi))
        line_vectors.append(data)

class TestSampleProperties:
    """Tests for whether all sample Lines have the corresponding expected properties after
    initialization.
    """

    def test_direction(self, sample_lines: list[Line | Axis],
                       line_vectors: list[dict[str, SpaceVector]]) -> None:
        """Test whether the directions of the sample lines match the expected directions."""
        for line, expected in zip(sample_lines, line_vectors, strict=True):
            # TODO: Check why the float values aren't coming out exactly the same.
            np.testing.assert_array_almost_equal(line.direction, expected["unique_direction"])

    def test_ref_point(self, sample_lines: list[Line | Axis],
                       line_vectors: list[dict[str, SpaceVector]]) -> None:
        """Test whether the reference_point of the sample lines match the expected points."""
        for line, expected in zip(sample_lines, line_vectors, strict=True):
            # TODO: Check why the float values aren't coming out exactly the same.
            np.testing.assert_array_almost_equal(line.reference_point.cartesian,
                                                 expected["ref_point"])

    def test_len(self, sample_lines: list[Line | Axis]) -> None:
        """Tests that the length of sample lines matches the dimension of its direction."""
        for line in sample_lines:
            assert len(line) == len(line.direction)

    def test_slope_intercept(self,
                             slope_y_intercept_lines: tuple[list[Line], list[dict[str, float]]]
                             ) -> None:
        """Test that the slopes and intercepts of the sample lines are calculated correctly."""
        for line, constants in zip(*slope_y_intercept_lines):
            assert line.slope == constants["slope"]
            assert line.y_intercept == constants["intercept"]

    def test_direction_polar_spherical(self, sample_lines: list[Line | Axis],
                                       line_vectors: list[dict[str, SpaceVector]]) -> None:
        """Test that any defined polar or spherical vectors of the sample lines match the
        calculated ones.
        """
        for line, expected in zip(sample_lines, line_vectors, strict=True):
            if isinstance(line, Axis):
                continue
            if not (expected_vector := expected.get("polar_spherical")):
                # Any entry without polar spherical doesn't need to be tested.
                continue
            line_vector: SphericalVector | PolarVector
            if len(expected_vector) == 2:
                line_vector = line.direction_polar
            else:
                line_vector = line.direction_spherical
            # TODO: Check why the float values aren't coming out exactly the same.
            np.testing.assert_array_almost_equal(line_vector, expected_vector)

# TODO: Replace Near Zero tests with floating point steps rather than EPS_64

class TestLineChanges:
    """Tests for changing Line properties after initialization."""

    def test_move_to_point(self, property_changes: dict[str, Any],
                           read_vector: Callable[[Any, bool], SpaceVector]) -> None:
        """Test moving a line from its initialized position to different points and orientations.
        """
        for data in property_changes["lines"]["move_to_point"]:
            line = Line(Point(read_vector(data["start"], False)),
                        read_vector(data["direction"], False))
            for change in data["changes"]:
                phi = math.radians(float(change["phi"])) if "phi" in change else None
                theta = math.radians(float(change["theta"])) if "theta" in change else None
                line.move_to_point(read_vector(change["point"], False), phi, theta)
                # TODO: Check why the float values aren't coming out exactly the same.
                assert line.direction == pytest.approx(read_vector(change["direction"], True))
                # TODO: Check why the float values aren't coming out exactly the same.
                expected_ref = read_vector(change["ref_point"], False)
                assert line.reference_point.cartesian == pytest.approx(expected_ref)

    def test_direction_setter(self, property_changes: dict[str, Any],
                              read_vector: Callable[[Any, bool], SpaceVector]) -> None:
        """Test setting a line's direction and the resulting impacts on the reference point."""
        for data in property_changes["lines"]["direction_setter"]:
            line = Line(Point(read_vector(data["start"], False)),
                        read_vector(data["direction"], False))
            for change in data["changes"]:
                line.direction = read_vector(change["vector"], False)
                assert line.direction == read_vector(change["direction"], True)
                assert line.reference_point.cartesian == read_vector(change["ref_point"], False)

# TODO: Add tests for each input type initialization method for Line and for Axis.
# TODO: Add Axis direction setting test
# TODO: Add tests for is_equal for Line and Axis.

class TestLineInit(unittest.TestCase):

    def setUp(self) -> None:
        self.pt_a = Point((1,0,0))
        self.pt_b = Point((1,10,0))

    def test_line_str_dunder(self) -> None:
        test = Line.from_two_points(self.pt_a, self.pt_b)
        self.assertEqual(str(test), "<Line(1,0,0)d(0,1,0)>")

class TestExceptions:
    """Test Line and Axis ability to raise exceptions."""

    def test_from_two_points_same_point(self) -> None:
        """Test that initializing a Line with two of the same point raises a ValueError."""
        with pytest.raises(ValueError):
            test_line = Line.from_two_points((1, 1), (1, 1))

class TestLineCoordinateSystemConversion(unittest.TestCase):

    def setUp(self) -> None:
        """
        Test Order:
            Point A, Point B, Phi (Azimuth) Angle, Theta (Inclination) Angle
        Angles get converted to radians prior to test
        r separately defined for legibility since for line direction unit
        vectors it will always be 1.
        """
        tests = [
            ((0, 0, 0), (1, 0, 0), (1, 0, 90)),
            ((0, 0, 0), (0, 1, 0), (1, 90, 90)),
            ((0, 0, 0), (0, 0, 1), (1, math.nan, 0)),
        ]
        self.tests_2d, self.tests_3d = [], []
        for pt_a, pt_b, (r, phi, theta) in tests:
            self.tests_3d.append(
                (
                    Point(pt_a), Point(pt_b),
                    (r, math.radians(phi), math.radians(theta)),
                )
            )
            if pt_a[:2] != pt_b[:2]: # To deal with when x = y = 0 and z != 0
                self.tests_2d.append(
                    (Point(pt_a[:2]), Point(pt_b[:2]), (r, math.radians(phi)))
                )

    def test_direction_polar_setter(self) -> None:
        for pt_a, pt_b, polar_vector in self.tests_2d:
            with self.subTest(
                        point_a=tuple(pt_a), point_b=tuple(pt_b),
                        polar_vector=polar_vector
                    ):
                test_line = Line.from_two_points(pt_a, pt_b)
                before_direction = test_line.direction
                test_line.direction_polar = polar_vector
                np.testing.assert_allclose(test_line.direction, before_direction, atol=1e-15)

    def test_direction_spherical_setter(self) -> None:
        for pt_a, pt_b, spherical_vector in self.tests_3d:
            with self.subTest(
                        point_a=tuple(pt_a), point_b=tuple(pt_b),
                        spherical_vector=spherical_vector
                    ):
                test_line = Line.from_two_points(pt_a, pt_b)
                before_direction = test_line.direction
                test_line.direction_spherical = spherical_vector
                np.testing.assert_allclose(test_line.direction, before_direction, atol=1e-15)

class TestLineUpdate(unittest.TestCase):

    def test_update(self) -> None:
        line = Line(Point(0, 0, 0), (1, 0, 0))
        new = Line(Point(1, 1, 0), (1, 1, 1))
        line.update(new)
        self.assertTrue(line.is_equal(new))

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

MATRIX_2D_ROTATIONS = [
    # Init Point, Initial Direction, Rotation Angle
    (ORIGIN_2D, X_2D, 0, X_2D, "rm2_unrotated_x_axis"),
    (ORIGIN_2D, X_2D, 90, Y_2D, "rm2_rotate_x_to_+y"),
    (ORIGIN_2D, X_2D, 180, (-1, 0), "rm2_rotate_x_to_-x"),
]

MATRIX_3D_ROTATIONS = [
    # Init Point, Initial Direction, (Yaw (Z), Pitch (X), Roll (Y)), expected, Id Prefix
    (ORIGIN_3D, X_3D, (0, 0, 0), (1, 0, 0), "rm3_unrotated_x_axis"),
    (ORIGIN_3D, X_3D, (90, 0, 0), Y_3D, "rm3_rotate_x_to_+y"),
]

def _quaternion_params(rotations):
    """Generates the list of pytest parameters for testing quaternion rotation."""
    params = []
    for point, initial, rotation_axis, angle, expected, id_ in rotations:
        quat_w = cos(radians(angle / 2))
        quat_ijk = map(lambda x, y: x * sin(radians(y) / 2),
                       rotation_axis, itertools.repeat(angle))
        quat = np.quaternion(quat_w, *quat_ijk)
        test_id = "_".join([id_, str(angle), str(rotation_axis), str(expected)])
        param = pytest.param(point, initial, quat, expected, id=test_id)
        params.append(param)
    return params

def _2d_rotation_params(rotations):
    """Generates the list of pytest parameters for testing 2D rotation matrix rotations."""
    params = []
    for point, initial, angle, expected, id_ in rotations:
        matrix = trig.rotation_2(radians(angle))
        test_id = "_".join([id_, str(angle), str(expected)])
        param = pytest.param(point, initial, matrix, expected, id=test_id)
        params.append(param)
    return params

def _3d_rotation_params(rotations):
    """Generates the list of pytest parameters for testing 3D rotation matrix rotations."""
    params = []
    for point, initial, angles, expected, id_ in rotations:
        matrix = trig.yaw_pitch_roll(*map(radians, angles))
        test_id = "_".join([id_, str(angles), str(expected)])
        param = pytest.param(point, initial, matrix, expected, id=test_id)
        params.append(param)
    return params

@pytest.mark.parametrize(
    "point, initial, rotation, expected",
    [
        *_quaternion_params(QUAT_ROTATIONS),
        *_3d_rotation_params(MATRIX_3D_ROTATIONS),
        *_2d_rotation_params(MATRIX_2D_ROTATIONS),
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
        pytest.param(ORIGIN_2D, X_2D, np.identity(3), "D Axis with ", id="2d@3d_matrix"),
        pytest.param(ORIGIN_3D, X_3D, np.identity(2), "D Axis with ", id="3d@2d_matrix"),
    ]
)
def test_rotate_axis_exceptions(point, direction, rotation, msg) -> None:
    """Tests for handling axis rotation errors."""
    axis = Axis(point, direction)
    with pytest.raises(ValueError, match=msg):
        axis.rotate(rotation)

if __name__ == "__main__":
    unittest.main()
