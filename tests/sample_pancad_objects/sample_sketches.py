"""A module providing sample sketch features to test pancad with."""

from math import radians, sqrt
from numbers import Real

import pytest

from pancad.geometry.circle import Circle
from pancad.geometry.circular_arc import CircularArc
from pancad.geometry.coordinate_system import CoordinateSystem
from pancad.geometry.ellipse import Ellipse
from pancad.geometry.line_segment import LineSegment
from pancad.geometry.point import Point
from pancad.geometry.system import TwoDSketchSystem
from pancad.geometry.sketch import Pose, Sketch

from pancad.constants import ConstraintReference as CR, SketchConstraint as SC

from pancad.constraints._generator import make_constraint
from pancad.constraints.snapto import Horizontal, Vertical
from pancad.constraints.state_constraint import Coincident
from pancad.constraints.distance import Distance, Diameter

def circle(pose: Pose=None,
           name: str="Test Circle",
           radius: Real=5,
           center: tuple[Real, Real]=None,
           unit: str="mm",
           include_constraints: bool=True) -> Sketch:
    """Returns a circle centered at the sketch origin."""
    if center is None:
        center = (0, 0)
    circle = Circle(center, radius)
    system = TwoDSketchSystem([circle])
    if pose is None:
        pose = Pose.from_yaw_pitch_roll((0, 0, 0), 0, 0, 0)
    system.constraints.extend(
        [
            Diameter(circle, value=radius, unit=unit),
            Coincident(circle.center, system.origin)
        ]
    )
    return Sketch(system, pose, name=name)

def square(pose: Pose=None,
           name: str="Test Square",
           side: Real=1,
           unit: str="mm",
           include_constraints: bool=True) -> Sketch:
    """Returns a square oriented parallel/perpendicular to the sketch
    coordinate system axes.
    """
    bottom_left = (0, 0)
    bottom_right = (side, 0)
    top_left = (0, side)
    top_right = (side, side)

    bottom = LineSegment(bottom_left, bottom_right)
    right = LineSegment(bottom_right, top_right)
    top = LineSegment(top_right, top_left)
    left = LineSegment(top_left, bottom_left)
    system = TwoDSketchSystem([bottom, right, top, left])
    if include_constraints:
        system.constraints.extend(
            [
                Horizontal(bottom),
                Vertical(right),
                Horizontal(top),
                Vertical(left),
                Coincident(bottom.start, left.end),
                Coincident(bottom.end, right.start),
                Coincident(right.end, top.start),
                Coincident(top.end, left.start),
                Distance(bottom, top, value=side, unit="mm"),
                Distance(right, left, value=side, unit="mm"),
                Coincident(bottom.start, system.origin),
            ]
        )
    if pose is None:
        pose = Pose.from_yaw_pitch_roll((0, 0, 0), 0, 0, 0)
    return Sketch(system, pose, name=name)

def rounded_square(pose: Pose=None,
                   name: str="Test Rounded Rectangle",
                   side: Real=3,
                   radius: Real=1,
                   unit: str="mm",
                   include_constraints: bool=True) -> Sketch:
    # All lines and arcs start from the top left of the bottom left arc and
    # travel counter clockwise in a full loop.

    # Define straight line length
    straight = side - 2 * radius

    # Line Segment Points
    # t/b = top/bottom | l/r = left/right
    b_l = (radius, 0)
    b_r = (radius + straight, 0)
    r_b = (side, radius)
    r_t = (side, radius + straight)
    l_b = (0, radius)
    l_t = (0, radius + straight)
    t_l = (radius, side)
    t_r = (radius + straight, side)

    # ls = line segment
    b = LineSegment(b_l, b_r)
    r = LineSegment(r_b, r_t)
    t = LineSegment(t_l, t_r)
    l = LineSegment(l_b, l_t)

    # Arc Center Points, c = center
    c_bl = (radius, radius)
    c_br = (radius + straight, radius)
    c_tl = (radius, radius + straight)
    c_tr = (radius + straight, radius + straight)

    # a = arc
    a_bl = CircularArc(c_bl, radius, (-1, 0), (0, -1), False)
    a_br = CircularArc(c_br, radius, (0, -1), (1, 0), False)
    a_tr = CircularArc(c_tr, radius, (1, 0), (0, 1), False)
    a_tl = CircularArc(c_tl, radius, (0, 1), (-1, 0), False)
    geometry = [b, r, t, l, a_bl, a_br, a_tr, a_tl]
    system = TwoDSketchSystem(geometry)
    if include_constraints:
        system.constraints.extend(
            [
                Horizontal(b),
                Vertical(r),
                Horizontal(t),
                Vertical(l),
                Coincident(l.end, a_bl.start),
                Coincident(a_bl.end, b.start),
                Coincident(b.end, a_br.start),
                Coincident(a_br.end, r.start,),
                Coincident(r.end, a_tr.start),
                Coincident(a_tr.end, t.start),
                Coincident(t.end, a_tl.start),
                Coincident(a_tl.end, l.start),
                Distance(b, t, value=side, unit="mm"),
                Distance(r, l, value=side, unit="mm"),
                Coincident(b, system.origin),
                Coincident(l, system.origin),
            ]
        )
    if pose is None:
        pose = Pose.from_yaw_pitch_roll((0, 0, 0), 0, 0, 0)
    return Sketch(system, pose, name=name)

def ellipse(pose: CoordinateSystem=None,
            name: str = "Test Ellipse",
            center: tuple[Real]=None,
            semi_major_axis: Real=2,
            semi_minor_axis: Real=1,
            angle_degrees: Real=0,
            include_constraints: bool=True) -> Sketch:
    """Returns an angled ellipse in a sketch."""
    if center is None:
        center = (0, 0)
    ellipse = Ellipse.from_angle(center,
                           semi_major_axis, semi_minor_axis,
                           radians(angle_degrees))
    a = 20
    b = 10
    unit = "mm"
    geometry = [ellipse]
    system = TwoDSketchSystem([ellipse])
    if include_constraints:
        system.constraints.extend(
            [
                make_constraint(SC.COINCIDENT,
                                ellipse.center, system.origin),
                make_constraint(SC.HORIZONTAL, ellipse.major_axis_line),
                make_constraint(SC.DISTANCE,
                                ellipse.major_axis_min, ellipse.major_axis_max,
                                value=a, unit=unit),
                make_constraint(SC.DISTANCE,
                                ellipse.minor_axis_min, ellipse.minor_axis_max,
                                value=b, unit=unit),
            ]
        )
    if pose is None:
        pose = Pose.from_yaw_pitch_roll((0, 0, 0), 0, 0, 0)
    return Sketch(system, pose, name=name)



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

def line_angled_to_x_axis(quadrant: int,
                          angle: Real,
                          start_radially_out: bool) -> LineSegment:
    """Creates a unit long line segment at an angle to the x-axis.

    :param quadrant: The quadrant the angle dimension will appear in.
    :param angle: The angle dimension in degrees.
    :param start_radially_out: Whether the start is at the origin. The end is at
        the origin when False.
    """
    at_origin = Point(0, 0)
    length = sqrt(2)
    quadrant_polar_angle_map = {1: radians(angle),
                                2: radians(180 - angle),
                                3: radians(180 + angle),
                                4: radians(-angle)}
    radially_out = Point.from_polar(length, quadrant_polar_angle_map[quadrant])
    name = f"test_sketch_quadrant{quadrant}_{angle}_degrees"
    segment_points = [at_origin, radially_out]
    if start_radially_out:
        segment_points.reverse()
    return LineSegment(*segment_points)

def sketch_with_line_angled_to_x_axis(quadrant: int, angle: float,
                                      start_radially_out: bool) -> Sketch:
    """Creates a sketch with a single line angled relative to the x-axis."""
    line = line_angled_to_x_axis(quadrant, angle, start_radially_out)
    system = TwoDSketchSystem([line])
    line_origin = line.end if start_radially_out else line.start
    system.constraints.extend(
        [
            make_constraint(SC.COINCIDENT, line_origin, system.origin),
            make_constraint(SC.DISTANCE, line.start, line.end,
                            value=line.length, unit="mm"),
            make_constraint(SC.ANGLE, system.x_axis, line,
                            value=angle, quadrant=quadrant),
        ]
    )
    pose = Pose.from_yaw_pitch_roll((0, 0, 0), 0, 0, 0)
    return Sketch(system, pose)

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
        sketch = sketch_with_line_angled_to_x_axis(quadrant, angle,
                                                   start_radially_out)
        sketch.name = f"Quadrant_{quadrant}_Angle_{angle}"
        if start_radially_out:
            sketch.name = sketch.name + "_EndOnOrigin"
        else:
            sketch.name = sketch.name + "_StartOnOrigin"
        sketches.append(sketch)
    return sketches
