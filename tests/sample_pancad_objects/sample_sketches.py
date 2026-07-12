"""A module providing sample sketch features to test pancad with."""

from math import radians, sqrt
from numbers import Real

import pytest

from pancad.geometry.line_segment import LineSegment
from pancad.geometry.system import TwoDSketchSystem
from pancad.geometry.sketch import Pose, Sketch
from pancad.utils import solvers
from pancad.constants import ConstraintReference as CR, SketchConstraint as SC
from pancad.constraints._generator import make_constraint

from tests.testing_utils import sketch_gen

@pytest.fixture
def unconstrained_square_sketch() -> Sketch:
    """Square sketch with just the lines, no constraints."""
    side = 1
    bottom_left = (0, 0)
    bottom_right = (side, 0)
    top_left = (0, side)
    top_right = (side, side)

    bottom = LineSegment(bottom_left, bottom_right)
    right = LineSegment(bottom_right, top_right)
    top = LineSegment(top_right, top_left)
    left = LineSegment(top_left, bottom_left)
    system = TwoDSketchSystem([bottom, right, top, left])
    pose = Pose.from_yaw_pitch_roll((0, 0, 0), 0, 0, 0)
    return Sketch(system, pose)

@pytest.fixture
def joined_square_sketch(unconstrained_square_sketch) -> Sketch:
    """Square sketch with just the lines. Line end points are coincident."""
    sketch = unconstrained_square_sketch
    bottom, right, top, left = sketch.geometry_system.geometry
    sketch.geometry_system.constraints.extend(
        [
            make_constraint(SC.COINCIDENT, bottom.start, left.end),
            make_constraint(SC.COINCIDENT, bottom.end, right.start),
            make_constraint(SC.COINCIDENT, right.end, top.start),
            make_constraint(SC.COINCIDENT, top.end, left.start),
        ]
    )
    return sketch

@pytest.fixture
def square_sketch_bottom_length(joined_square_sketch) -> Sketch:
    """Square sketch with the bottom line length constrained."""
    sketch = joined_square_sketch
    unit = "mm"
    bottom, *_ = sketch.geometry_system.geometry
    side_length = bottom.end.x - bottom.start.x
    distance = make_constraint(SC.DISTANCE, bottom.start, bottom.end,
                               value=side_length, unit=unit)
    sketch.geometry_system.constraints.append(distance)
    return sketch

CSYS = -1
BOTTOM = 0
RIGHT = 1
TOP = 2
LEFT = 3

CONSTRAINT_PARAMS = [
    (
        # Bottom/Right Equal, Bottom/Top Horiz, Left/Right Vert, Bottom Start
        # *point* coincident to origin.
        (SC.HORIZONTAL, ((BOTTOM, CR.CORE),)),
        (SC.VERTICAL, ((RIGHT, CR.CORE),)),
        (SC.HORIZONTAL, ((TOP, CR.CORE),)),
        (SC.VERTICAL, ((LEFT, CR.CORE),)),
        (SC.EQUAL, ((BOTTOM, CR.CORE), (RIGHT, CR.CORE))),
        (SC.COINCIDENT, ((BOTTOM, CR.START), (CSYS, CR.ORIGIN))),
    ),
    (
        # All Equal, Bottom Horizontal, Bottom/Left Perpendicular, Bottom Start
        # *point* coincident to origin.
        (SC.HORIZONTAL, ((BOTTOM, CR.CORE),)),
        (SC.EQUAL, ((BOTTOM, CR.CORE), (RIGHT, CR.CORE))),
        (SC.EQUAL, ((BOTTOM, CR.CORE), (TOP, CR.CORE))),
        (SC.EQUAL, ((BOTTOM, CR.CORE), (LEFT, CR.CORE))),
        (SC.PERPENDICULAR, ((BOTTOM, CR.CORE), (LEFT, CR.CORE))),
        (SC.COINCIDENT, ((BOTTOM, CR.START), (CSYS, CR.ORIGIN))),
    ),
    (
        # Bottom Horizontal, Bottom/Left Perpendicular, R/L parallel, B/T
        # parallel, Bottom Start *point* coincident to origin.
        (SC.HORIZONTAL, ((BOTTOM, CR.CORE),)),
        (SC.EQUAL, ((BOTTOM, CR.CORE), (RIGHT, CR.CORE))),
        (SC.PERPENDICULAR, ((BOTTOM, CR.CORE), (LEFT, CR.CORE))),
        (SC.PARALLEL, ((RIGHT, CR.CORE), (LEFT, CR.CORE))),
        (SC.PARALLEL, ((BOTTOM, CR.CORE), (TOP, CR.CORE))),
        (SC.COINCIDENT, ((BOTTOM, CR.START), (CSYS, CR.ORIGIN))),
    ),
    (
        # Bottom/Right Equal, Bottom/Top Horiz, Left/Right Vert, Bottom Left
        # *lines* coincident to origin.
        (SC.HORIZONTAL, ((BOTTOM, CR.CORE),)),
        (SC.VERTICAL, ((RIGHT, CR.CORE),)),
        (SC.HORIZONTAL, ((TOP, CR.CORE),)),
        (SC.VERTICAL, ((LEFT, CR.CORE),)),
        (SC.EQUAL, ((BOTTOM, CR.CORE), (RIGHT, CR.CORE))),
        (SC.COINCIDENT, ((BOTTOM, CR.CORE), (CSYS, CR.ORIGIN))),
        (SC.COINCIDENT, ((LEFT, CR.CORE), (CSYS, CR.ORIGIN))),
    ),
    (
        # All Sides equal, bottom horizontal, left vertical, bottom left
        # coincident to origin
        (SC.HORIZONTAL, ((BOTTOM, CR.CORE),)),
        (SC.VERTICAL, ((LEFT, CR.CORE),)),
        (SC.EQUAL, ((BOTTOM, CR.CORE), (RIGHT, CR.CORE))),
        (SC.EQUAL, ((BOTTOM, CR.CORE), (TOP, CR.CORE))),
        (SC.EQUAL, ((BOTTOM, CR.CORE), (LEFT, CR.CORE))),
        (SC.COINCIDENT, ((BOTTOM, CR.START), (CSYS, CR.ORIGIN))),
    ),

]
@pytest.fixture(params=CONSTRAINT_PARAMS)
def square_sketch_variations(request, square_sketch_bottom_length):
    """Variations on a fully constrained square sketch. Same geometry, varied
    constraints.
    """
    sketch = square_sketch_bottom_length
    constraints = []
    for type_, refs in request.param:
        input_geometry = []
        for index, constraint_ref in refs:
            geo = sketch.geometry_system.geometry[index]
            input_geometry.append(geo.get_reference(constraint_ref))
        constraints.append(make_constraint(type_, *input_geometry))
    sketch.geometry_system.constraints.extend(constraints)
    yield sketch

@pytest.fixture
def line_angled_to_x_axis_sketches(request) -> list[Sketch]:
    """A list of angle-sweeping sketches placing a single line segment in
    different quadrants relative to the sketch's x-axis. Useful for checking the
    implementation of angle constraints inside a single CAD file.
    """
    angle_sweep_params = [
        # Quadrant, Angle (Degrees), start_to_end
        (1, 45, False),
        (2, 45, False),
        (3, 45, False),
        (4, 45, False),
        (1, 45, True),
        (2, 45, True),
        (3, 45, True),
        (4, 45, True),
    ]
    sketches = []
    for quadrant, angle, start_radially_out in angle_sweep_params:
        sketch = sketch_gen.sketch_with_line_angled_to_x_axis(quadrant, angle, start_radially_out)
        sketch.name = f"Quadrant_{quadrant}_Angle_{angle}"
        if start_radially_out:
            sketch.name = sketch.name + "_EndOnOrigin"
        else:
            sketch.name = sketch.name + "_StartOnOrigin"
        sketches.append(sketch)
    return sketches
