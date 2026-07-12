"""A module providing functions to generate sketches and sketch geometry for pancad tests."""

from math import radians, sqrt

from pancad.geometry.circle import Circle
from pancad.geometry.circular_arc import CircularArc
from pancad.geometry.coordinate_system import CoordinateSystem
from pancad.geometry.ellipse import Ellipse
from pancad.geometry.system import TwoDSketchSystem
from pancad.geometry.sketch import Pose, Sketch
from pancad.geometry.point import Point
from pancad.geometry.line_segment import LineSegment
from pancad.constraints.snapto import Horizontal, Vertical
from pancad.constraints.state_constraint import Coincident
from pancad.constraints.distance import Distance, Diameter, Angle
from pancad.utils import solvers

def circle(pose: Pose=None,
           name: str="Test Circle",
           radius: float=5,
           center: tuple[float, float]=None,
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
           side: float=1,
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
                   side: float=3,
                   radius: float=1,
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
            center: tuple[float]=None,
            semi_major_axis: float=2,
            semi_minor_axis: float=1,
            angle_degrees: float=0,
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
                Coincident(ellipse.center, system.origin),
                Horizontal(ellipse.major_axis_line),
                Distance(ellipse.major_axis_min, ellipse.major_axis_max, value=a, unit=unit),
                Distance(ellipse.minor_axis_min, ellipse.minor_axis_max, value=b, unit=unit)
            ]
        )
    if pose is None:
        pose = Pose.from_yaw_pitch_roll((0, 0, 0), 0, 0, 0)
    return Sketch(system, pose, name=name)

def line_angled_to_x_axis(quadrant: int,
                          angle: float,
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
            Coincident(line_origin, system.origin),
            Distance(line.start, line.end, value=solvers.get_length(line), unit="mm"),
            Angle(system.x_axis, line, value=angle, quadrant=quadrant)
        ]
    )
    pose = Pose.from_yaw_pitch_roll((0, 0, 0), 0, 0, 0)
    return Sketch(system, pose)
