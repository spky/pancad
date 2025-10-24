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

def circle(coordinate_system: CoordinateSystem=None,
           plane_reference: CR=CR.XY,
           name: str="Test Circle",
           radius: Real=5,
           unit: str="mm",
           include_constraints: bool=True,
           center: tuple[Real, Real]=None) -> Sketch:
    """Returns a circle centered at the sketch origin."""
    if center is None:
        center = (0, 0)
    circle = Circle(center, radius)
    geometry = [Circle(center, radius)]
    sketch = Sketch(coordinate_system=coordinate_system,
                    plane_reference=plane_reference,
                    geometry=[circle],
                    name=name)
    sketch.constraints = [
        Diameter(circle, CR.CORE, radius, unit=unit),
        Coincident(circle, CR.CENTER, sketch, CR.ORIGIN)
    ]
    return sketch

def square(coordinate_system: CoordinateSystem=None,
           plane_reference: CR=CR.XY,
           name: str="Test Square",
           side: Real=1,
           unit: str="mm",
           include_constraints: bool=True) -> Sketch:
    """Returns a square oriented parallel/perpendicular to the sketch 
    coordinate system axes.
    """
    # t/b = top/bottom | l/r = left/right
    b_l = (0, 0)
    b_r = (side, 0)
    t_l = (0, side)
    t_r = (side, side)
    
    b = LineSegment(b_l, b_r)
    r = LineSegment(b_r, t_r)
    t = LineSegment(t_r, t_l)
    l = LineSegment(t_l, b_l)
    
    geometry = [b, r, t, l]
    sketch = Sketch(coordinate_system=coordinate_system,
                    plane_reference=plane_reference,
                    geometry=geometry,
                    name=name)
    
    if include_constraints:
        sketch.constraints = [
            Horizontal(b, CR.CORE),
            Vertical(r, CR.CORE),
            Horizontal(t, CR.CORE),
            Vertical(l, CR.CORE),
            Coincident(b, CR.START, l, CR.END),
            Coincident(b, CR.END, r, CR.START),
            Coincident(r, CR.END, t, CR.START),
            Coincident(t, CR.END, l, CR.START),
            Distance(b, CR.CORE, t, CR.CORE, side, unit="mm"),
            Distance(r, CR.CORE, l, CR.CORE, side, unit="mm"),
            Coincident(b, CR.START, sketch, CR.ORIGIN),
        ]
    
    return sketch

def rounded_square(coordinate_system: CoordinateSystem=None,
                   plane_reference: CR=CR.XY,
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
    t = LineSegment(t_l, b_l)
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
    sketch = Sketch(coordinate_system=coordinate_system,
                    plane_reference=plane_reference,
                    geometry=geometry,
                    name=name)
    
    if include_constraints:
        sketch.constraints = [
            Horizontal(b, CR.CORE),
            Vertical(r, CR.CORE),
            Horizontal(t, CR.CORE),
            Vertical(l, CR.CORE),
            Coincident(l, CR.END, a_bl, CR.START),
            Coincident(a_bl, CR.END, b, CR.START),
            Coincident(b, CR.END, a_br, CR.START),
            Coincident(a_br, CR.END, r, CR.START),
            Coincident(r, CR.END, a_tr, CR.START),
            Coincident(a_tr, CR.END, t, CR.START),
            Coincident(t, CR.END, a_tl, CR.START),
            Coincident(a_tl, CR.END, l, CR.START),
            Distance(b, CR.CORE, t, CR.CORE, side, unit="mm"),
            Distance(r, CR.CORE, l, CR.CORE, side, unit="mm"),
            Coincident(b, CR.CORE, sketch, CR.ORIGIN),
            Coincident(l, CR.CORE, sketch, CR.ORIGIN),
        ]
    
    return sketch

def ellipse(coordinate_system: CoordinateSystem=None,
            plane_reference: CR=CR.XY,
            name: str = "Test Ellipse",
            center: tuple[Real]=None,
            semi_major_axis: Real=2,
            semi_minor_axis: Real=1,
            angle_degrees: Real=0) -> Sketch:
    """Returns an angled ellipse in a sketch."""
    if center is None:
        center = (0, 0)
    e = Ellipse.from_angle(center,
                           semi_major_axis, semi_minor_axis,
                           radians(angle_degrees))
    a = 20
    b = 10
    unit = "mm"
    geometry = [e]
    sketch = Sketch(coordinate_system=coordinate_system,
                    plane_reference=plane_reference,
                    geometry=geometry,
                    name=name)
    sketch.constraints = [
        make_constraint(SC.COINCIDENT, e, CR.CENTER, sketch, CR.ORIGIN),
        make_constraint(SC.HORIZONTAL, e, CR.X),
        make_constraint(SC.DISTANCE, e, CR.X_MIN, e, CR.X_MAX,
                        value=a, unit=unit),
        make_constraint(SC.DISTANCE, e, CR.Y_MIN, e, CR.Y_MAX,
                        value=b, unit=unit),
    ]
    return sketch