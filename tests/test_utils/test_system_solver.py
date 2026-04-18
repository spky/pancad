"""Tests for pancad's system constraint solving systems."""
from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pytest

from pancad.api import Axis, Point, ThreeDSketchSystem, make_constraint, SketchConstraint as SC
from pancad.utils.solvers import SystemSolver

if TYPE_CHECKING:
    from numbers import Real

    from pancad.abstract import AbstractGeometrySystem
    from pancad.utils.pancad_types import SpaceVector

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

@pytest.mark.parametrize(
    "initial, expected",
    [
        pytest.param(*_axis_to_2_pts((0,0,1), (1,0,0), (0,0,0), (1,0,0)),
                     id="0,0,1-x-aligned_to_x"),
        pytest.param(*_axis_to_2_pts((0,0,1), (1,0,0), (0,0,0), (1,1,1)),
                     id="0,0,1-x-aligned_to_direct1,1,1"),
    ]
)
def test_solve_system(initial: AbstractGeometrySystem, expected: AbstractGeometrySystem):
    """Tests that SystemSolver can solve the constraints in the initial system and output the
    expected system.
    """
    solver = SystemSolver(initial)
    solution = solver.solve()
    solver.update(solution.x)
    print(solver.label_x(solution.x))
    assert initial.is_equal(expected)
