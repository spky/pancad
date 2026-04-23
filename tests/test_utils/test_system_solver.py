"""Tests for pancad's system constraint solving systems."""
from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pytest
from pprint import pp

from pancad.api import (Axis, Point, Plane, ThreeDSketchSystem,
                        make_constraint, SketchConstraint as SC)
from pancad.utils.solvers import SystemSolver

if TYPE_CHECKING:
    from numbers import Real

    from pancad.abstract import AbstractGeometrySystem
    from pancad.utils.pancad_types import SpaceVector, Space3DVector

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
    ]
)
def test_solve_system(initial: AbstractGeometrySystem, expected: AbstractGeometrySystem):
    """Tests that SystemSolver can solve the constraints in the initial system and output the
    expected system.
    """
    solver = SystemSolver(initial)
    print("\nInitial Input Vector")
    print(solver.label_x(solver.get_initial()))
    print("Initial Residuals")
    print(solver.label_fun(solver.fun(solver.get_initial())))
    solution = solver.solve()
    solver.update(solution.x)
    print("Solution Vector")
    print(solver.label_x(solution.x))
    assert initial.is_equal(expected)
