"""A module providing sample sketch features to test pancad with."""

from math import radians
from numbers import Real

from pancad.geometry import (
    Circle,
    CircularArc,
    CoordinateSystem,
    Ellipse,
    LineSegment,
    Sketch,
)
from pancad.geometry.sketch import Pose, Sketch, SketchGeometrySystem
from pancad.geometry.constants import (ConstraintReference as CR,
                                       SketchConstraint as SC)
from pancad.geometry.constraints import (
    make_constraint,
    Coincident,
    Diameter,
    Distance,
    Horizontal,
    Vertical,
)

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
    system = SketchGeometrySystem([circle])
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
    system = SketchGeometrySystem([bottom, right, top, left])
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
    system = SketchGeometrySystem(geometry)
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
    system = SketchGeometrySystem([ellipse])
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
