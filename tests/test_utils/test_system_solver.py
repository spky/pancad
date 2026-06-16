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
from pancad.utils import solvers, solver_residuals as pcres

if TYPE_CHECKING:
    from numbers import Real
    from collections.abc import Callable

    from _pytest.mark.structures import ParameterSet

    import numpy.typing as npt

    from pancad.abstract import AbstractGeometrySystem, AbstractGeometry
    from pancad.utils.pancad_types import SpaceVector, Space3DVector

    # Constraints in a system defined here by listing the SketchConstraint and geometry indices.
    ConstraintDef = tuple[SC, tuple[int, ...]]
    SystemTestPair = tuple[ThreeDSketchSystem, ThreeDSketchSystem]
    PlaneInputs = tuple[Space3DVector, Space3DVector]
    LineInputs = tuple[Space3DVector, Space3DVector]

SolveTestPair = tuple[ThreeDSketchSystem, ThreeDSketchSystem]
"""Systems to compare. The first is the test system and the second is the goal system."""

def _generate_system(geo: list[AbstractGeometry],
                     cons_def: list[ConstraintDef]) -> ThreeDSketchSystem:
    """Generates a new 3D geometry system."""
    constraints = []
    for sketch_con, indices in cons_def:
        constraints.append(make_constraint(sketch_con, *[geo[i] for i in indices]))
    return ThreeDSketchSystem(geo, constraints)

def _perpendicular_planes(plane: PlaneInputs, fixed_plane: PlaneInputs, fixed_line: LineInputs,
                          expected_plane: PlaneInputs) -> SystemTestPair:
    """Generates a system of 1 movable plane, 1 fixed plane, and 1 fixed line already coincident
    to the fixed plane. The movable plane is coincident with the fixed line and perpendicular to
    the fixed plane. The movable plane's normal vector is constrained unique to guarantee only one
    solution is possible.

    :param plane: Movable plane's point and normal vectors.
    :param fixed_plane: Fixed plane's point and normal vectors.
    :param fixed_line: Fixed line's reference point and direction vectors.
    :param expected_plane: Expected result plane's point and normal vectors.
    """
    cons = [
        (SC.PERPENDICULAR, (0, 1)),
        (SC.COINCIDENT, (0, 2)),
        (SC.UNIQUE, (0,)),
        (SC.FIXED, (1,)),
        (SC.FIXED, (2,)),
    ]
    fixed_line = Line(Point(fixed_line[0]), fixed_line[1])
    initial = _generate_system(
        [Plane(*plane), Plane(*fixed_plane), fixed_line.copy()], cons)
    expected = _generate_system([Plane(*expected_plane), Plane(*fixed_plane), fixed_line.copy()],
                                cons)
    return initial, expected

def _plane_intersection_line(line: LineInputs, plane_1: PlaneInputs, plane_2: PlaneInputs,
                             expected_line: LineInputs) -> SystemTestPair:
    """Generates a pair systems of 2 fixed planes and a line coincident to both of them."""
    cons = [
        (SC.COINCIDENT, (0, 1)),
        (SC.COINCIDENT, (0, 2)),
        (SC.FIXED, (1,)),
        (SC.FIXED, (2,)),
    ]
    point, direction = line
    initial = _generate_system([Line(Point(point), direction), Plane(*plane_1), Plane(*plane_2)],
                               cons)
    point, direction = expected_line
    expected = _generate_system([Line(Point(point), direction), Plane(*plane_1), Plane(*plane_2)],
                                cons)
    return initial, expected

def _coincident_planes(plane_1: PlaneInputs, plane_2: PlaneInputs,
                       expected_plane: PlaneInputs) -> SystemTestPair:
    """Generates a pair of systems for 1 fixed plane and a plane that is coincident to the fixed
    plane.

    :param plane_1: Movable plane's point and normal vectors.
    :param plane_2: Fixed plane's point and normal vectors.
    :param expected_plane: Expected result plane's point and normal vectors.
    """
    cons = [
        (SC.COINCIDENT, (0, 1)),
        (SC.UNIQUE, (0,)),
        (SC.FIXED, (1,)),
    ]
    initial = _generate_system([Plane(*plane_1), Plane(*plane_2)], cons)
    expected = _generate_system([Plane(*expected_plane), Plane(*plane_2)], cons)
    return initial, expected

def _coincident_points(point: SpaceVector, fixed_point: SpaceVector) -> SystemTestPair:
    """Generates a pair of systems for 1 fixed point and a point that is constrained coincident to
    the fixed point.

    :param point: Movable point's location vector.
    :param fixed_point: Fixed point's location vector.
    """
    cons = [
        (SC.COINCIDENT, (0, 1)),
        (SC.FIXED, (1,)),
    ]
    initial = _generate_system([Point(point), Point(fixed_point)], cons)
    expected = _generate_system([Point(fixed_point), Point(fixed_point)], cons)
    return initial, expected

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

def _2_planes_distance(fix_pln_vecs: tuple[Space3DVector, Space3DVector],
                       ini_pln_vecs: tuple[Space3DVector, Space3DVector],
                       distance: float) -> tuple[ThreeDSketchSystem, ThreeDSketchSystem]:
    fix = Plane(*fix_pln_vecs)
    new_pt = np.array(fix.reference_point) + distance * np.array(fix.normal)
    systems = []
    for geometry in [(fix, Plane(*ini_pln_vecs)), (fix.copy(), Plane(new_pt, fix.normal))]:
        constraints = [
            make_constraint(SC.FIXED, geometry[0]),
            make_constraint(SC.DISTANCE, geometry[0], geometry[1], value=distance),
            make_constraint(SC.CODIRECTIONAL, geometry[0], geometry[1]),
        ]
        systems.append(ThreeDSketchSystem(geometry, constraints))
    return tuple(systems)

@pytest.mark.parametrize(
    "initial, expected",
    [
        ### Point-Point Coincident Tests
        # Both points starting at origin, already coincident. 3D
        pytest.param(*_coincident_points((0,0,0), (0,0,0)), id="pt000-coin-fixpt000"),
        # Both points starting at origin, already coincident. 2D
        pytest.param(*_coincident_points((0,0), (0,0)), id="pt00-coin-fixpt00"),
        # Point at (1,1,1), fixed point at origin. 3D.
        pytest.param(*_coincident_points((1,1,1), (0,0,0)), id="pt111-coin-fixpt000"),
        # Point at (1,1,1), fixed point at origin. 2D.
        pytest.param(*_coincident_points((1,1), (0,0)), id="pt11-coin-fixpt00"),
        # Point at (0,0,0), fixed point at (1,1,1). 3D.
        pytest.param(*_coincident_points((0,0,0), (1,1,1)), id="pt000-coin-fixpt111"),
        # Point at (0,0), fixed point at (1,1). 2D.
        pytest.param(*_coincident_points((0,0), (1,1)), id="pt00-coin-fixpt11"),

        ### Point-Line Coincident Tests
        # Line starting with ref point (0,0,1) and in the x direction coincident with two fixed
        # points at (0,0,0) and (1,0,0).
        pytest.param(*_line_to_2_pts((0,0,1), (1,0,0), (0,0,0), (1,0,0)),
                     id="2-pt-coincident-Line(0,0,1)(1,0,0)-to-x-axis-aligned"),
        # Line starting with ref point (0,0,1) and in the x direction coincident with two fixed
        # points at (0,0,0) and (1,1,1).
        pytest.param(*_line_to_2_pts((0,0,1), (1,0,0), (0,0,0), (1,1,1)),
                     id="2-pt-coincident-Line(0,0,1)(1,0,0)-to-(0,0,0)(1,1,1)"),

        ### Plane-Point Coincident Tests
        # Plane starting at ref point (0,0,0) with normal in the z direction coincident with 3
        # points (0,0,1), (1,0,1), and (0,1,1).
        pytest.param(*_plane_to_3_pts((0,0,0), (0,0,1), ((0,0,1), (1,0,1), (0,1,1))),
                     id="3-pt-coincident-Plane-XY-to-Plane-XY-plus-1-z"),
        # Plane starting at ref point (0,0,0) with normal in the z direction coincident with 3
        # points (2,0,0), (0,2,0), and (0,0,2).
        pytest.param(*_plane_to_3_pts((0,0,0), (0,0,1), ((2,0,0), (0,2,0), (0,0,2))),
                     id="3-pt-coincident-Plane-XY-to-all-2-away"),
        # Plane starting at ref point (0,0,0) with normal in the z direction coincident with 3
        # points (0,0,0), (0,1,0), and (0,0,1).
        pytest.param(*_plane_to_3_pts((0,0,1), (0,0,1), ((0,0,0), (0,1,0), (0,0,1))),
                     id="3-pt-coincident-Plane-XY-plus-1-z-to-YZ-Plane"),

        ### Fixed System Tests
        # A system with one of each geometry fixed into place.
        pytest.param(*_fixed_3d_system(), id="fixed-3d-system"),

        ### Axis-Axis Coincident with Codirectional Tests
        # X Axis coincident to negative x axis.
        *_coincident_axis_duo(((0,0,0), (1,0,0)), ((0,0,0), (-1,0,0)), "axes-coincident-X-to-negX"),
        # X Axis coincident to another X axis.
        *_coincident_axis_duo(((0,0,0), (1,0,0)), ((0,0,0), (1,0,0)), "axes-coincident-X-to-X"),
        # X Axis coincident to Y axis.
        *_coincident_axis_duo(((0,0,0), (1,0,0)), ((0,0,0), (0,1,0)), "axes-coincident-X-to-Y"),
        # X Axis coincident to Z axis.
        *_coincident_axis_duo(((0,0,0), (1,0,0)), ((0,0,0), (0,0,1)), "axes-coincident-X-to-Z"),
        # An Axis with ref point (1,1,1) and direction in the x direction coincident to Y axis.
        *_coincident_axis_duo(((1,1,1), (1,0,0)), ((0,0,0), (0,1,0)), "axes-coincident-111-to-Y"),

        ### Plane-Plane Distance Tests
        # XY plane +10 units away from a fixed XY plane. (Fixed plane first arg)
        pytest.param(*_2_planes_distance(((0,0,0), (0,0,1)), ((0,0,0), (0,0,1)), 10),
                     id="plane-dist-xy-xy-10"),
        # Plane at ref point (1,1,1) and direction (1,1,1) +10 units away from a fixed XY plane.
        # (Fixed plane first arg)
        pytest.param(*_2_planes_distance(((0,0,0), (0,0,1)), ((1,1,1), (1,1,1)), 10),
                     id="plane-dist-xy-111-111pln-10"),
        # Plane at ref point (0,0,0) and direction (1,1,1) +10 units away from a fixed XY plane.
        # (Fixed plane first arg)
        pytest.param(*_2_planes_distance(((0,0,0), (0,0,1)), ((0,0,0), (1,1,1)), 10),
                     id="plane-dist-xy-000-111pln-10"),
        # Plane at ref point (0,0,0) and direction (1,0,0) +10 units away from a fixed XY plane.
        # (Fixed plane first arg). In other words: The planes start perpendicular.
        pytest.param(*_2_planes_distance(((0,0,0), (0,0,1)), ((0,0,0), (1,0,0)), 10),
                     id="plane-dist-xy-yz-10",
                     marks=pytest.mark.xfail(reason="Starting from perp planes not yet defined")),
        # Plane at ref point (0,0,1) and direction in z direction coincident with XY plane.
        pytest.param(
            *_coincident_planes(((0,0,1), (0,0,1)), ((0,0,0), (0,0,1)), ((0,0,0), (0,0,1))),
            id="planes-coincident-xyp1z-to-xy"
        ),
        # Line starting with ref point (1,0,0) and in the z direction coincident with fixed YZ and
        # XZ planes.
        pytest.param(
            *_plane_intersection_line(
                ((1,0,0), (0,0,1)), # Line
                ((0,0,0), (1,0,0)), ((0,0,0), (0,1,0)), # Planes
                ((0,0,0), (0,0,1)) # Expected Line
            ),
            id="line-coincident-xz-and-yz-planes"
        ),

        ### Plane-Plane Perpendicular Tests
        # plane starting at origin and normal pointing to (1,1,1) constrained perpendicular to the
        # xy plane and coincident with a line on the X axis.
        pytest.param(
            *_perpendicular_planes(
                ((0,0,0), (1,1,1)), # Initial Movable Plane
                ((0,0,0), (0,0,1)), # Fixed Plane: XY Plane
                ((0,0,0), (1,0,0)), # Fixed Line: X Axis Line
                ((0,0,0), (0,1,0)), # Expected Plane: XZ Plane
            ),
            id="000-111pln-perp-xypln-coin-xline"
        ),
        # Plane starting at (1,1,1) and normal pointing to (1,1,1) constrained perpendicular to
        # the XY plane and coincident with a line on the X axis.
        pytest.param(
            *_perpendicular_planes(
                ((1,1,1), (1,1,1)), # Initial Movable Plane
                ((0,0,0), (0,0,1)), # Fixed Plane: XY Plane
                ((0,0,0), (1,0,0)), # Fixed Line: X Axis Line
                ((0,0,0), (0,1,0)), # Expected Plane: XZ Plane
            ),
            id="111-111pln-perp-xypln-coin-xline"
        ),
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
        assert pcres.unit_vector(np.array(v)) == expected

    @pytest.mark.parametrize(
        "func, v1, v2, expected",
        [
            pytest.param(solvers.pcres.codirectional, (1,0,0), (1,0,0), (0,0,0),
                         id="cd_both_x_vectors"),
            pytest.param(solvers.pcres.codirectional, (1,0,0), (-1,0,0), (2,0,0),
                         id="cd_opposite_x_vectors"),
            pytest.param(solvers.pcres.antiparallel, (1,0,0), (1,0,0), (2,0,0),
                         id="ap_both_x_vectors"),
            pytest.param(solvers.pcres.antiparallel, (1,0,0), (-1,0,0), (0,0,0),
                         id="ap_opposite_x_vectors"),
            pytest.param(solvers.pcres.parallel, (1,0,0), (1,0,0), (0,0,0),
                         id="pa_both_x_vectors"),
            pytest.param(solvers.pcres.parallel, (1,0,0), (-1,0,0), (0,0,0),
                         id="pa_opposite_x_vectors"),
            pytest.param(solvers.pcres.codirectional, (1,EPS_64,0), (1,0,0), (0,EPS_64,0),
                         id="cd_x_vector_off_eps_in_y"),
            pytest.param(solvers.pcres.codirectional, (1,0,0), (1,EPS_64,0), (0,-EPS_64,0),
                         id="cd_x_vector_off_eps_in_y"),
            pytest.param(solvers.pcres.codirectional, (2,0,0), (2,0,0), (0,0,0),
                         id="cd_2x_vectors"),
            pytest.param(solvers.pcres.codirectional, (2,0,0), (4,0,0), (0,0,0),
                         id="cd_2xand4x_vectors"),
            pytest.param(solvers.pcres.codirectional, (-2,0,0), (-4,0,0), (0,0,0),
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
            pytest.param((1,0), (0,1), 0, id="2d-x-and-y"),
        ]
    )
    def test_perpendicular(self, v1: SpaceVector, v2: SpaceVector, expected: float) -> None:
        """Test for calculating the residual of two vectors that must be perpendicular."""
        assert pcres.perpendicular(np.array(v1, dtype=np.float64),
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
        nptest.assert_array_equal(pcres.unique_vector(v, zero_atol=atol), exp)

    @pytest.mark.parametrize(
        "plane, point, distance, expected",
        [
            pytest.param(((0,0,0),(0,0,1)), (0,0,0), 0, 0, id="000-0d-xy"),
            pytest.param(((0,0,0),(0,0,1)), (0,0,1), 1, 0, id="00n1-1d-xy"),
            pytest.param(((0,0,0),(0,0,1)), (0,0,-1), -1, 0, id="00n1-n1d-xy"),
        ]
    )
    def test_point_plane_distance(self, plane: PlaneInputs, point: Space3DVector, distance: float,
                                  expected: float) -> None:
        """Test for calculating the distance residual of a point-plane distance constraint."""
        pln_pt, normal = map(np.array, plane)
        result = pcres.point_plane_distance(pln_pt, normal, np.array(point), np.float64(distance))
        assert result == expected

    @pytest.mark.parametrize(
        "plane, line, distance, expected",
        [
            pytest.param(((0,0,0),(0,0,1)), ((0,0,0),(1,0,0)), 0, 0, id="xy-0d-xline"),
            pytest.param(((0,0,0),(0,0,1)), ((0,0,1),(1,0,0)), 0, 1, id="xy-0d-1r-001L100"),
            pytest.param(((0,0,0),(0,0,1)), ((0,0,-1),(1,0,0)), 0, -1, id="xy-0d-n1r-00n1L100"),
        ]
    )
    def test_plane_line_distance(self, plane: PlaneInputs, line: LineInputs,
                                 distance: float, expected: float) -> None:
        """Test for calculating the distance residual of a line/axis-plane distance constraint."""
        pln_pt, normal = map(np.array, plane)
        line_pt, direction = map(np.array, line)
        result = pcres.plane_line_distance(pln_pt, normal, line_pt, direction,
                                           np.float64(distance))
        assert result == expected

    @pytest.mark.parametrize(
        "point1, normal1, point2, normal2, distance, expected",
        [
            pytest.param((0,0,0), (0,0,1), (0,0,0), (0,0,1), 0, 0, id="xy-xy-0d-0r"),
            pytest.param((0,0,0), (0,0,1), (0,0,1), (0,0,1), 1, 0, id="xy-xy-p1z-1d-0r"),
            pytest.param((0,0,1), (0,0,1), (0,0,0), (0,0,1), -1, 0, id="xy-p1z-xy-1d-0r"),
            pytest.param((0,0,0), (0,0,1), (0,0,1), (0,0,1), 0, 1, id="xy-xy-p1z-0d-n1r"),
            pytest.param((0,0,1), (0,0,1), (0,0,0), (0,0,1), 0, -1, id="xy-p1z-xy-0d-n1r"),
            pytest.param((0,0,0), (0,0,1), (0,0,-1), (0,0,1), 0, -1, id="xy-xy-m1z-0d-n1r"),
            pytest.param((0,0,-1), (0,0,1), (0,0,0), (0,0,1), 0, 1, id="xy-m1z-xy-0d-n1r"),
            pytest.param((0,0,0), (1,1,1), (1,1,1), (1,1,1), np.linalg.norm((1,1,1)), 0,
                         id="111pln-111pln-p111-1d-0r"),
            pytest.param((1,1,1), (1,1,1), (0,0,0), (1,1,1), -np.linalg.norm((1,1,1)), 0,
                         id="111pln-p111-111pln-1d-0r"),
            pytest.param((0,0,0), (0,0,1), (0,0,0), (1,1,1), 0, -np.sqrt(2),
                         id="xy-111pln-0d-rt2r"),
            pytest.param((0,0,0), (1,1,1), (0,0,0), (0,0,1), 0, -2.121320343559643,
                         id="111pln-xy-0d-rt2r"),
            pytest.param((0,0,0), (0,0,1), (0,0,0), (0,1,0), 0, np.inf, id="xy-xz-0d-infr"),
            pytest.param((0,0,0), (0,1,0), (0,0,0), (0,0,1), 0, np.inf, id="xz-xy-0d-infr"),
        ]
    )
    def test_plane_plane_distance(self,
                                  point1: Space3DVector, normal1: Space3DVector,
                                  point2: Space3DVector, normal2: Space3DVector,
                                  distance: float | np.float64,
                                  expected: float | np.float64) -> None:
        print("Points:",
              pcres.get_3_plane_points(np.array(point1),
                                       pcres.get_unique_vector(np.array(normal1))))
        assert pcres.plane_plane_distance(np.array(point1), np.array(normal1),
                                          np.array(point2), np.array(normal2),
                                          np.float64(distance)
                                          ) == pytest.approx(expected)

class TestResidualHelpers:
    """Tests for functions that are broken down steps of a residual function."""

    @pytest.mark.parametrize(
        "point, normal",
        [
            pytest.param((0,0,0), (1,0,0), id="yz"),
            pytest.param((0,0,0), (0,1,0), id="xz"),
            pytest.param((0,0,0), (0,0,1), id="xy"),
            pytest.param((1,1,1), (0,0,1), id="xy-pln-z-p1-offset"),
            pytest.param((0,0,0), (1,1,1), id="111-norm-pln"),
            pytest.param((1,1,1), (1,1,1), id="111-norm-111-mv-pln"),
            pytest.param((-1,-1,-1), (-1,-1,-1), id="n1n1n1-norm-n1n1n1-mv-pln"),
        ]
    )
    def test_get_3_plane_points(self, point: Space3DVector, normal: Space3DVector):
        result = pcres.get_3_plane_points(np.array(point), np.array(normal))
        print("Points:", result)
        for result_pt in result:
            # Check that all 3 points are on the plane
            try:
                assert np.dot(normal, result_pt) == pytest.approx(np.dot(normal, point))
            except AssertionError as exc:
                exc.add_note(f"Point {result_pt} is not on the plane")
                raise
        # Check matrix rank greater than 1 to check that the points are not collinear.
        try:
            assert np.linalg.matrix_rank(result) > 1
        except AssertionError as exc:
            exc.add_note(f"The result points are all collinear: {result}")
            raise

    @pytest.mark.parametrize(
        "vector, expected",
        [
            # 0D
            pytest.param(tuple(), tuple(), id="0d"),

            # 1D
            pytest.param((0,), (0,), id="zero_vector_1d"),
            pytest.param((1,), (1,), id="1_1d"),
            pytest.param((-1,), (1,), id="-1_1d"),
            # 2D
            pytest.param((0,0), (0,0), id="zero_vector_2d"),
            # 3D
            pytest.param((0,0,0), (0,0,0), id="zero_vector_3d"),
            pytest.param((1,0,0), (1,0,0), id="x_3d"),
            pytest.param((-1,0,0), (1,0,0), id="-x_3d"),
            pytest.param((0,1,0), (0,1,0), id="y_3d"),
            pytest.param((0,-1,0), (0,1,0), id="-y_3d"),
            pytest.param((0,0,1), (0,0,1), id="z_3d"),
            pytest.param((0,0,-1), (0,0,1), id="-z_3d"),
            pytest.param((-1,-1,-1), (1,1,1), id="-1-1-1_3d"),
            pytest.param((-1,-1,EPS_64), (-1,-1,EPS_64), id="-1-1eps_3d"),
            pytest.param((-1,-1,-EPS_64), (1,1,EPS_64), id="-1-1-eps_3d"),
        ]
    )
    def test_get_unique_vector(self, vector: tuple[float, ...], expected: tuple[float, ...]):
        result = pcres.get_unique_vector(np.array(vector))
        np.testing.assert_array_equal(result, expected)

    @pytest.mark.parametrize(
        "plane, point, expected",
        [
            ### Moving Point around the XY plane.
            # Origin Point on the XY plane.
            pytest.param(((0,0,0), (0,0,1)), (0,0,0), 0, id="000-to-xy"),
            # Point 1 unit above the XY plane.
            pytest.param(((0,0,0), (0,0,1)), (0,0,1), 1, id="001-to-xy"),
            # Point 5 units above the XY plane.
            pytest.param(((0,0,0), (0,0,1)), (0,0,10), 10, id="005-to-xy"),
            # Point 1 unit below the XY plane.
            pytest.param(((0,0,0), (0,0,1)), (0,0,-1), -1, id="00n1-to-xy"),
            # Point at 5,5,0 on the XY plane.
            pytest.param(((0,0,0), (0,0,1)), (5,5,0), 0, id="550-to-xy"),
            # Point at 5,5,5 above the XY plane.
            pytest.param(((0,0,0), (0,0,1)), (5,5,5), 5, id="555-to-xy"),
            # Point at 5,5,-5 below the XY plane.
            pytest.param(((0,0,0), (0,0,1)), (5,5,-5), -5, id="55n5-to-xy"),

            ### Moving Point around an XY plane with its normal vector reversed.
            # Point 1 unit above the plane.
            pytest.param(((0,0,0), (0,0,-1)), (0,0,1), -1, id="001-to-000pt-00n1norm"),
            # Point 1 unit below the plane.
            pytest.param(((0,0,0), (0,0,-1)), (0,0,-1), 1, id="00n1-to-000pt-00n1norm"),

            ### Moving Point around a plane positioned 1 unit above the XY plane.
            # Point on the plane.
            pytest.param(((0,0,1), (0,0,1)), (0,0,1), 0, id="001-to-001pt-001norm"),
            # Point 1 unit above the plane.
            pytest.param(((0,0,1), (0,0,1)), (0,0,2), 1, id="002-to-001pt-001norm"),
            # Point 1 unit below the plane.
            pytest.param(((0,0,1), (0,0,1)), (0,0,0), -1, id="000-to-001pt-001norm"),

            ### Moving point around a 0,0,5 normal vector XY plane. Should have no effect.
            # Point on the XY Plane.
            pytest.param(((0,0,0), (0,0,5)), (0,0,0), 0, id="000-to-5normxy"),
            # Point 1 unit above the XY plane.
            pytest.param(((0,0,0), (0,0,5)), (0,0,1), 1, id="001-to-5normxy"),
            # Point 5 units above the XY plane.
            pytest.param(((0,0,0), (0,0,5)), (0,0,10), 10, id="005-to-5normxy"),
            # Point 1 unit below the XY plane.
            pytest.param(((0,0,0), (0,0,5)), (0,0,-1), -1, id="00n1-to-5normxy"),

            ### Moving point around a 0,0,-5 normal vector XY plane. Should have no effect.
            # Point 1 unit above the plane.
            pytest.param(((0,0,0), (0,0,-5)), (0,0,1), -1, id="001-to-000pt-00n5norm"),
            # Point 1 unit below the plane.
            pytest.param(((0,0,0), (0,0,-5)), (0,0,-1), 1, id="00n1-to-000pt-00n5norm"),

            ### Moving point around a 0,0,0 point, 1,1,1 normal vector plane.
            # Origin Point on the plane.
            pytest.param(((0,0,0), (1,1,1)), (0,0,0), 0, id="000-to-000pt-111norm"),
            # Point 1,1,1 above the plane.
            pytest.param(((0,0,0), (1,1,1)), (1,1,1), np.linalg.norm((1,1,1)),
                         id="000-to-111pt-111norm"),
            # Point -1,-1,-1 below the plane.
            pytest.param(((0,0,0), (1,1,1)), (-1,-1,-1), -np.linalg.norm((1,1,1)),
                         id="000-to-n1n1n1pt-111norm"),

        ]
    )
    def test_get_plane_to_point_distance(self, plane: PlaneInputs, point: Space3DVector,
                                         expected: float | np.float64) -> None:
        """Test that plane to point distance is the correct magnitude and sign."""
        plane_point, normal = map(np.array, plane)
        result = pcres.get_plane_to_point_distance(plane_point, normal, np.array(point))
        assert result == pytest.approx(expected)

    def test_get_plane_to_point_distance_zero_normal_exc(self) -> None:
        plane_point, normal, point = map(np.array, ((1,1,1), (0,0,0), (1,1,1)))
        with pytest.raises(ValueError):
            pcres.get_plane_to_point_distance(plane_point, normal, point)
