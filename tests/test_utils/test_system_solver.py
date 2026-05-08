"""Tests for pancad's system constraint solving systems."""
from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pytest
from pprint import pp

from pancad.api import (Axis, Point, Plane, ThreeDSketchSystem,
                        make_constraint, SketchConstraint as SC)
from pancad.utils import solvers

if TYPE_CHECKING:
    from numbers import Real
    from collections.abc import Callable

    from _pytest.mark.structures import ParameterSet

    import numpy.typing as npt

    from pancad.abstract import AbstractGeometrySystem
    from pancad.utils.pancad_types import SpaceVector, Space3DVector

SolveTestPair = tuple[ThreeDSketchSystem, ThreeDSketchSystem]
"""Systems to compare. The first is the test system and the second is the goal system."""

def _axis_to_2_pts(ref_pt: SpaceVector, direct: SpaceVector, p1: SpaceVector, p2: SpaceVector
                   ) -> tuple[ThreeDSketchSystem, ThreeDSketchSystem]:
    """Generates a pair of an unsolved system with an Axis coincident to two fixed points and the
    solved version of the system.
    """
    initial = [Axis(ref_pt, direct), Point(p1), Point(p2)]
    solved = [Axis(p1, np.array(p2) - np.array(p1)), Point(p1), Point(p2)]
    constraints = []
    for axis, point_1, point_2 in [initial, solved]:
        constraints.append(
            [
                make_constraint(SC.COINCIDENT, axis, point_1),
                make_constraint(SC.COINCIDENT, axis, point_2),
                make_constraint(SC.FIXED, point_1),
                make_constraint(SC.FIXED, point_2),
            ]
        )
    return ThreeDSketchSystem(initial, constraints[0]), ThreeDSketchSystem(solved, constraints[1])

def _plane_to_3_pts(ref_pt: Space3DVector, normal: Space3DVector,
                    pts: tuple[Space3DVector, Space3DVector, Space3DVector]
                    ) -> tuple[ThreeDSketchSystem, ThreeDSketchSystem]:
    """Generates a pair of an unsolved system with a Plane coincident to three fixed points and
    the solved version of the system.
    """
    initial = [Point(p) for p in pts]
    initial.append(Plane(ref_pt, normal))
    p1, p2, p3 = pts
    solved_normal = np.cross(np.array(p2) - np.array(p1), np.array(p3) - np.array(p1))
    solved = [Point(p) for p in pts]
    solved.append(Plane(p1, solved_normal))
    print(pts)
    print(solved[3].reference_axis.reference_point)
    constraints = []
    for point_1, point_2, point_3, plane in [initial, solved]:
        constraints.append(
            [
                make_constraint(SC.FIXED, point_1),
                make_constraint(SC.FIXED, point_2),
                make_constraint(SC.FIXED, point_3),
                make_constraint(SC.COINCIDENT, plane, point_1),
                make_constraint(SC.COINCIDENT, plane, point_2),
                make_constraint(SC.COINCIDENT, plane, point_3),
            ]
        )
    return ThreeDSketchSystem(initial, constraints[0]), ThreeDSketchSystem(solved, constraints[1])

def _fixed_3d_system() -> tuple[ThreeDSketchSystem, ThreeDSketchSystem]:
    """Generates a fixed system containing at least one of each geometry that can be fixed."""
    initial = [
        # Point(1, 1, 1),
        # Axis((0, 0, 0), (1, 1, 1)),
        Plane((0, 0, 0), (0, 0, 1)),
    ]
    solved = [g.copy() for g in initial]
    systems = []
    for geometry in [initial, solved]:
        constraints = [make_constraint(SC.FIXED, g) for g in geometry]
        systems.append(ThreeDSketchSystem(geometry, constraints))
    return tuple(systems)

def _coincident_axis_duo(init_axis: tuple[Space3DVector, Space3DVector],
                         new_axis: tuple[Space3DVector, Space3DVector],
                         id_: str
                         ) -> tuple[ParameterSet, ParameterSet]:
    """Generates two system pairs to test coincident, codirectional, and antiparallel solving
    behavior. The new axis is held Fixed while the init_axis is constrained coincident. The first
    pair has the two axes constrained codirectional and the second pair constrains them
    antiparallel.
    """
    params = []
    for direction_constraint in (SC.CODIRECTIONAL,): # SC.ANTIPARALLEL):
        initial = [Axis(*init_axis), Axis(*new_axis)]
        solved = [Axis(*new_axis), Axis(*new_axis)]
        systems = []
        for start, goal in [initial, solved]:
            constraints = [
                make_constraint(SC.FIXED, goal),
                make_constraint(SC.COINCIDENT, start, goal),
                make_constraint(direction_constraint, start, goal),
            ]
            systems.append(ThreeDSketchSystem([start, goal], constraints))
        params.append(pytest.param(*systems, id=f"{id_}_{direction_constraint.name}"))
    return tuple(params)

@pytest.mark.parametrize(
    "initial, expected",
    [
        pytest.param(*_axis_to_2_pts((0,0,1), (1,0,0), (0,0,0), (1,0,0)),
                     id="2-pt-coincident-Axis(0,0,1)(1,0,0)-to-x-axis-aligned"),
        pytest.param(*_axis_to_2_pts((0,0,1), (1,0,0), (0,0,0), (1,1,1)),
                     id="2-pt-coincident-Axis(0,0,1)(1,0,0)-to-(0,0,0)(1,1,1)"),
        pytest.param(*_plane_to_3_pts((0,0,0), (0,0,1), ((0,0,1), (1,0,1), (0,1,1))),
                     id="3-pt-coincident-Plane-XY-to-Plane-XY-plus-1-z"),
        pytest.param(*_plane_to_3_pts((0,0,0), (0,0,1), ((2,0,0), (0,2,0), (0,0,2))),
                     id="3-pt-coincident-Plane-XY-to-all-2-away"),
        pytest.param(*_plane_to_3_pts((0,0,1), (0,0,1), ((0,0,0), (0,1,0), (0,0,1))),
                     id="3-pt-coincident-Plane-XY-plus-1-z-to-YZ-Plane"),
        pytest.param(*_fixed_3d_system(), id="fixed-3d-system"),
        *_coincident_axis_duo(((0,0,0), (1,0,0)), ((0,0,0), (0,1,0)), "axes-coincident-X-to-Y"),
    ]
)
def test_solve_system(initial: AbstractGeometrySystem, expected: AbstractGeometrySystem):
    """Tests that SystemSolver can solve the constraints in the initial system and output the
    expected system.
    """
    solver = solvers.SystemSolver(initial)
    print()
    solution = solver.solve()
    debugs = {
        "Initial Input Vector": solver.label_x(solver.get_initial()),
        "Initial Residuals": solver.label_fun(solver.fun(solver.get_initial())),
    }
    solver.update(solution.x)
    debugs.update(
        {
            "Solution Vector": solver.label_x(solution.x),
            "Solution Residuals": solver.label_fun(solver.fun(solution.x)),
            "Test System Geometry": initial.geometry,
            "Goal System Geometry": expected.geometry,
            "Solution": solution,
        }
    )
    for title, value in debugs.items():
        print(title)
        print(value)
    assert initial.is_equal(expected)

EPS_64 = np.finfo(np.float64).eps
MAX_64 = np.finfo(np.float64).max

class TestResiduals:
    """Tests for calculating residual values in isolation from the rest of the solvers."""

    @pytest.mark.parametrize(
        "v, expected",
        [
            pytest.param((0,0,0), -1.0, id="3d_zero_vector"),
            pytest.param((0,0), -1.0, id="2d_zero_vector"),
            pytest.param((1,0,0), 0.0, id="3d_x_vector"),
            pytest.param((-1,0,0), 0.0, id="-3d_x_vector"),
            pytest.param((1,0), 0.0, id="2d_x_vector"),
            pytest.param((-1,0), 0.0, id="-2d_x_vector"),
            pytest.param((10,0,0), 9.0, id="10_3d_x_vector"),
            pytest.param((-10,0,0), 9.0, id="-10_3d_x_vector"),
            pytest.param((0.5,0,0), -0.5, id="0.5_3d_x_vector"),
            pytest.param((-0.5,0,0), -0.5, id="-0.5_3d_x_vector"),
            pytest.param((1,1e-8,0), 0.0, id="1e-8_y_3d_x_vector_roundoff")
            # Demonstrates rounding at small numbers
        ]
    )
    def test_unit_vector(self, v: SpaceVector, expected: float) -> None:
        """Test for calculating the residual of a vector that must be a unit vector."""
        assert solvers.residual_unit_vector(np.array(v)) == expected

    @pytest.mark.parametrize(
        "func, v1, v2, expected",
        [
            pytest.param(solvers.residual_codirectional, (1,0,0), (1,0,0), 0.0,
                         id="cd_both_x_vectors"),
            pytest.param(solvers.residual_codirectional, (1,0,0), (-1,0,0), 2.0,
                         id="cd_opposite_x_vectors"),
            pytest.param(solvers.residual_antiparallel, (1,0,0), (1,0,0), 2.0,
                         id="ap_both_x_vectors"),
            pytest.param(solvers.residual_antiparallel, (1,0,0), (-1,0,0), 0.0,
                         id="ap_opposite_x_vectors"),
            pytest.param(solvers.residual_parallel, (1,0,0), (1,0,0), 0.0,
                         id="pa_both_x_vectors"),
            pytest.param(solvers.residual_parallel, (1,0,0), (-1,0,0), 0.0,
                         id="pa_opposite_x_vectors"),
            pytest.param(solvers.residual_codirectional, (1,EPS_64,0), (1,0,0), EPS_64,
                         id="cd_x_vector_off_eps_in_y"),
            pytest.param(solvers.residual_codirectional, (1,0,0), (1,EPS_64,0), -EPS_64,
                         id="cd_x_vector_off_eps_in_y"),
            pytest.param(solvers.residual_codirectional, (2,0,0), (2,0,0), 0,
                         id="cd_2x_vectors"),
            pytest.param(solvers.residual_codirectional, (2,0,0), (4,0,0), 0,
                         id="cd_2xand4x_vectors"),
            pytest.param(solvers.residual_codirectional, (-2,0,0), (-4,0,0), 0,
                         id="cd_-2xand-4x_vectors"),
        ]
    )
    def test_direction_residual(self,
                                func: Callable[npt.NDArray, npt.NDArray],
                                v1: SpaceVector, v2: SpaceVector,
                                expected: float) -> None:
        """Test for calculating the residual of two vectors that must be codirectional,
        antiparallel, or parallel.
        """
        assert func(np.array(v1, dtype=np.float64), np.array(v2, dtype=np.float64)) == expected

    @pytest.mark.parametrize(
        "func, v1, v2, atol",
        [
            pytest.param(solvers.residual_codirectional, (0,0,0), (1,0,0), 1e-8,
                         id="cd_v1-0_atol-1e-8"),
            pytest.param(solvers.residual_codirectional, (1e-16,0,0), (1,0,0), 1e-16,
                         id="cd_v1-1e-16_atol-1e-16"),
            pytest.param(solvers.residual_codirectional, (-1e-16,0,0), (1,0,0), 1e-16,
                         id="cd_v1-neg1e-16_atol-1e-16"),
            pytest.param(solvers.residual_codirectional, (1,0,0), (0,0,0), 1e-8,
                         id="cd_v2-0_atol-1e-8"),
            pytest.param(solvers.residual_codirectional, (1,0,0), (1e-16,0,0), 1e-16,
                         id="cd_v2-1e-16_atol-1e-16"),
        ]
    )
    def test_direction_residual_excs(self, func: Callable[npt.NDArray, npt.NDArray],
                                     v1: npt.NDArray, v2: npt.NDArray,
                                     atol: np.float64) -> None:
        """Tests for whether the residual error checking detects zero vectors"""
        with pytest.raises(ValueError, match="^Cannot check whether a zero vector"):
            func(np.array(v1, dtype=np.float64), np.array(v2, dtype=np.float64),
                 zero_atol=np.float64(atol))

    @pytest.mark.parametrize(
        "v1, v2, expected",
        [
            pytest.param((1,0,0), (0,1,0), 0.0, id="3d-x-and-y"),
            pytest.param((1,0,0), (0,-1,0), 0.0, id="3d-x-and-negative-y"),
            pytest.param((1,0,0), (EPS_64,1,0), EPS_64, id="3d-x-and-y-off-to-x-by-eps"),
            pytest.param((np.sqrt(MAX_64),0,0), (EPS_64,1,0), EPS_64,
                         id="3d-x-max-and-y-off-to-x-by-eps"),
            # Must use the square root of the max to avoid overflow during normalization squaring
            pytest.param((2,0,0), (EPS_64,2,0), EPS_64/2, id="3d-2x-and-2y-off-to-x-by-eps"),
        ]
    )
    def test_perpendicular(self, v1: SpaceVector, v2: SpaceVector, expected: float) -> None:
        """Test for calculating the residual of two vectors that must be perpendicular."""
        assert solvers.residual_perpendicular(np.array(v1, dtype=np.float64),
                                              np.array(v2, dtype=np.float64)) == expected

    @pytest.mark.parametrize(
        "normal, pt, expected",
        [
            pytest.param((0,0,1), (0,0,0), 0, id="xy-plane_nominal"),
            pytest.param((0,EPS_64,1), (0,0,1), EPS_64, id="xy-plane-p1z_y-eps-off"),
            # pytest.param((0,EPS_64,1), (0,0,-1), EPS_64, id="xy-plane-m1z_y-eps-off"),
        ]
    )
    def test_plane_ref_point(self, normal: Space3DVector, pt: Space3DVector,
                             expected: float) -> None:
        assert solvers.residual_plane_ref_point(np.array(normal,dtype=np.float64),
                                                np.array(pt, dtype=np.float64)) == expected
