"""Tests for pancad's system constraint solving systems."""
from __future__ import annotations

from typing import TYPE_CHECKING

import csv
import numpy as np
import numpy.testing as nptest
import pytest
from pprint import pp

from pancad.api import (Axis, Line, Point, Plane, ThreeDSketchSystem,
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

def _sys_line_co_2_fixed_pts(ref_pt: Space3DVector, direction: SpaceVector,
                             p1: SpaceVector, p2: SpaceVector) -> ThreeDSketchSystem:
    """Generates an system of a line and two fixed points."""
    geo = [Line(Point(ref_pt), direction), Point(p1), Point(p2)]
    constraints = [
        make_constraint(SC.COINCIDENT, geo[0], geo[1]),
        make_constraint(SC.COINCIDENT, geo[0], geo[2]),
        make_constraint(SC.FIXED, geo[1]),
        make_constraint(SC.FIXED, geo[2]),
    ]
    return ThreeDSketchSystem(geo, constraints)

def _line_to_2_pts(ref_pt: SpaceVector, direct: SpaceVector, p1: SpaceVector, p2: SpaceVector
                   ) -> tuple[ThreeDSketchSystem, ThreeDSketchSystem]:
    """Generates a pair of an unsolved system with an Line coincident to two fixed points and the
    solved version of the system.
    """
    return (_sys_line_co_2_fixed_pts(ref_pt, direct, p1, p2),
            _sys_line_co_2_fixed_pts(p1, np.array(p2) - np.array(p1), p1, p2))

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
                make_constraint(SC.UNIQUE, plane),
            ]
        )
    return ThreeDSketchSystem(initial, constraints[0]), ThreeDSketchSystem(solved, constraints[1])

def _fixed_3d_system() -> tuple[ThreeDSketchSystem, ThreeDSketchSystem]:
    """Generates a fixed system containing at least one of each geometry that can be fixed."""
    initial = [
        Point(1, 1, 1),
        Axis((0, 0, 0), (1, 1, 1)),
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
                         id_: str,
                         **kwargs,
                         ) -> tuple[ParameterSet, ParameterSet]:
    """Generates two system pairs to test coincident, codirectional, and antiparallel solving
    behavior. The new axis is held Fixed while the init_axis is constrained coincident. The first
    pair has the two axes constrained codirectional and the second pair constrains them
    antiparallel.
    """
    params = []
    for direction_constraint in (SC.CODIRECTIONAL,): # , SC.ANTIPARALLEL):
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
        params.append(pytest.param(*systems, id=f"{id_}_{direction_constraint.value}", **kwargs))
    return tuple(params)

@pytest.mark.parametrize(
    "initial, expected",
    [
        pytest.param(*_line_to_2_pts((0,0,1), (1,0,0), (0,0,0), (1,0,0)),
                     id="2-pt-coincident-Line(0,0,1)(1,0,0)-to-x-axis-aligned"),
        pytest.param(*_line_to_2_pts((0,0,1), (1,0,0), (0,0,0), (1,1,1)),
                     id="2-pt-coincident-Line(0,0,1)(1,0,0)-to-(0,0,0)(1,1,1)"),
        pytest.param(*_plane_to_3_pts((0,0,0), (0,0,1), ((0,0,1), (1,0,1), (0,1,1))),
                     id="3-pt-coincident-Plane-XY-to-Plane-XY-plus-1-z"),
        pytest.param(*_plane_to_3_pts((0,0,0), (0,0,1), ((2,0,0), (0,2,0), (0,0,2))),
                     id="3-pt-coincident-Plane-XY-to-all-2-away"),
        pytest.param(*_plane_to_3_pts((0,0,1), (0,0,1), ((0,0,0), (0,1,0), (0,0,1))),
                     id="3-pt-coincident-Plane-XY-plus-1-z-to-YZ-Plane"),
        pytest.param(*_fixed_3d_system(), id="fixed-3d-system"),
        *_coincident_axis_duo(((0,0,0), (1,0,0)), ((0,0,0), (-1,0,0)), "axes-coincident-X-to-negX"),
        *_coincident_axis_duo(((0,0,0), (1,0,0)), ((0,0,0), (1,0,0)), "axes-coincident-X-to-X"),
        *_coincident_axis_duo(((0,0,0), (1,0,0)), ((0,0,0), (0,1,0)), "axes-coincident-X-to-Y"),
        *_coincident_axis_duo(((0,0,0), (1,0,0)), ((0,0,0), (0,0,1)), "axes-coincident-X-to-Z"),
        *_coincident_axis_duo(((1,1,1), (1,0,0)), ((0,0,0), (0,1,0)), "axes-coincident-111-to-Y"),
    ]
)
def test_solve_system(initial: AbstractGeometrySystem, expected: AbstractGeometrySystem,
                      tmp_path):
    """Tests that SystemSolver can solve the constraints in the initial system and output the
    expected system.
    """
    solver = solvers.SystemSolver(initial)
    run_data = []
    titles = []
    for var in solver.get_variables():
        prefix = f"variable_{var.element}_{var.name.value}"
        titles.extend([f"{prefix}_{i}" for i in range(len(var))])
    for eq in solver.get_equations():
        prefix = f"residual_{eq.element}_{eq.name.value}"
        titles.extend([f"{prefix}_{i}" for i in range(len(eq.calc()))])
    run_data.append(titles)
    def fun_log(f: Callable[[npt.NDArray], npt.NDArray]) -> Callable[[npt.NDArray], npt.NDArray]:
        def wrap(x: npt.NDArray) -> npt.NDArray:
            result = f(x)
            run_data.append([*x, *result])
            return result
        return wrap
    try:
        solution = solver.solve(fun_wrap=fun_log)
    finally:
        with open(tmp_path / "convergence_data.csv", "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerows(run_data)
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
DEF_0_TOL = 1e-16 # Default Tolerance for zero component values

class TestSolverSetUp:
    """Tests for the ability to set up solving scenarios."""

    @pytest.mark.parametrize(
        "system, include_fixed, expected",
        [
            pytest.param(_sys_line_co_2_fixed_pts((0,0,0), (1,0,0), (0,0,0), (1,0,0)), False,
                         [0,0,0,1,0,0], id="2pt-co-line"),
            pytest.param(_sys_line_co_2_fixed_pts((0,0,0), (1,0,0), (0,0,0), (1,0,0)), True,
                         [0,0,0,1,0,0,0,0,0,1,0,0], id="2pt-co-line_with_fixed"),
        ]
    )
    def test_get_initial(self, system: AbstractGeometrySystem, include_fixed: bool,
                         expected: list[float]):
        """Tests getting the initial x vector for solving."""
        solver = solvers.SystemSolver(system)
        np.testing.assert_array_equal(solver.get_initial(include_fixed),
                                      np.array(expected, dtype=np.float64))

    @pytest.mark.parametrize(
        "system, new_x",
        [
            pytest.param(_sys_line_co_2_fixed_pts((0,0,0), (1,0,0), (0,0,0), (1,0,0)),
                         [1,2,3,4,5,6], id="2pt-co-line-1to6"),
        ]
    )
    def test_x_setter(self, system: ThreeDSketchSystem, new_x: list[float]):
        """Tests the ability to update the input x vector during the solving operation."""
        solver = solvers.SystemSolver(system)
        new_x_array = np.array(new_x, dtype=np.float64)
        solver.x = new_x_array
        np.testing.assert_array_equal(solver.x, new_x_array)

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
            pytest.param(solvers.residual_codirectional, (1,0,0), (1,0,0), (0,0,0),
                         id="cd_both_x_vectors"),
            pytest.param(solvers.residual_codirectional, (1,0,0), (-1,0,0), (2,0,0),
                         id="cd_opposite_x_vectors"),
            pytest.param(solvers.residual_antiparallel, (1,0,0), (1,0,0), (2,0,0),
                         id="ap_both_x_vectors"),
            pytest.param(solvers.residual_antiparallel, (1,0,0), (-1,0,0), (0,0,0),
                         id="ap_opposite_x_vectors"),
            pytest.param(solvers.residual_parallel, (1,0,0), (1,0,0), (0,0,0),
                         id="pa_both_x_vectors"),
            pytest.param(solvers.residual_parallel, (1,0,0), (-1,0,0), (0,0,0),
                         id="pa_opposite_x_vectors"),
            pytest.param(solvers.residual_codirectional, (1,EPS_64,0), (1,0,0), (0,EPS_64,0),
                         id="cd_x_vector_off_eps_in_y"),
            pytest.param(solvers.residual_codirectional, (1,0,0), (1,EPS_64,0), (0,-EPS_64,0),
                         id="cd_x_vector_off_eps_in_y"),
            pytest.param(solvers.residual_codirectional, (2,0,0), (2,0,0), (0,0,0),
                         id="cd_2x_vectors"),
            pytest.param(solvers.residual_codirectional, (2,0,0), (4,0,0), (0,0,0),
                         id="cd_2xand4x_vectors"),
            pytest.param(solvers.residual_codirectional, (-2,0,0), (-4,0,0), (0,0,0),
                         id="cd_-2xand-4x_vectors"),
        ]
    )
    def test_direction_residual(self,
                                func: Callable[npt.NDArray, npt.NDArray],
                                v1: SpaceVector, v2: SpaceVector,
                                expected: SpaceVector) -> None:
        """Test for calculating the residual of two vectors that must be codirectional,
        antiparallel, or parallel.
        """
        np.testing.assert_array_equal(func(np.array(v1, dtype=np.float64),
                                           np.array(v2, dtype=np.float64)),
                                      expected)

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
        "vector, atol, expected",
        [ #nu = non-unique
            # 3D Whole Numbers
            pytest.param((1,0,0), DEF_0_TOL, (0,0,0), id="3d_nominal_x"),
            pytest.param((0,1,0), DEF_0_TOL, (0,0,0), id="3d_nominal_y"),
            pytest.param((0,0,1), DEF_0_TOL, (0,0,0), id="3d_nominal_z"),
            pytest.param((-1,0,0), DEF_0_TOL, (0,0,-2), id="3d_nu_negative_x"),
            pytest.param((0,-1,0), DEF_0_TOL, (0,-2,0), id="3d_nu_negative_y"),
            pytest.param((0,0,-1), DEF_0_TOL, (-2,0,0), id="3d_nu_negative_z"),
            pytest.param((1,1,0), DEF_0_TOL, (0,0,0), id="3d_nominal_1,1,0"),
            pytest.param((-1,-1,0), DEF_0_TOL, (0,-2,0), id="3d_nu_-1,-1,0"),
            pytest.param((-1,-1,1), DEF_0_TOL, (0,0,0), id="3d_nominal_-1,-1,1"),
            pytest.param((1,1,1), DEF_0_TOL, (0,0,0), id="3d_nominal_1,1,1"),
            pytest.param((-1,-1,-1), DEF_0_TOL, (-2,0,0), id="3d_nu_-1,-1,-1"),

            # 3D Near Zeros
            pytest.param((1,DEF_0_TOL,0), DEF_0_TOL, (0,0,0), id="3d_x_with_plus_0tol_y"),
            pytest.param((1,-DEF_0_TOL,0), DEF_0_TOL, (0,-2*DEF_0_TOL,0),
                         id="3d_x_with_minus_0tol_y"),
            pytest.param((1,-DEF_0_TOL,-DEF_0_TOL), DEF_0_TOL, (-2*DEF_0_TOL,-2*DEF_0_TOL,0),
                         id="3d_x_with_minus_0tol_y_and_z"),
            pytest.param((1,1,-DEF_0_TOL), DEF_0_TOL, (-2*DEF_0_TOL,0,0),
                         id="3d_1,1,0_with_minus_0tol_z"),

            # 2D
            pytest.param((1,0), DEF_0_TOL, (0,0), id="2d_nominal_x"),
            pytest.param((0,1), DEF_0_TOL, (0,0), id="2d_nominal_y"),
            pytest.param((1,0), DEF_0_TOL, (0,0), id="2d_nominal_x"),
            pytest.param((-1,0), DEF_0_TOL, (0,-2), id="2d_nu_negative_x"),
            pytest.param((0,-1), DEF_0_TOL, (-2,0), id="2d_nu_negative_y"),

            # 2D Near Zeros
            pytest.param((1,DEF_0_TOL), DEF_0_TOL, (0,0), id="2d_x_with_plus_0tol_y"),
            pytest.param((1,-DEF_0_TOL), DEF_0_TOL, (-2*DEF_0_TOL,0),
                         id="2d_x_with_minus_0tol_y"),
        ]
    )
    def test_unique_direction(self, vector: SpaceVector, atol: float,
                              expected: tuple[Real, Real]) -> None:
        v = np.array(vector)
        exp = np.array(expected)
        atol = np.float64(atol)
        nptest.assert_array_equal(solvers.residual_unique_vector(v, zero_atol=atol), exp)
