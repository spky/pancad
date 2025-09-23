from math import radians
from numbers import Real

from PanCAD.geometry import (
    Circle,
    CoordinateSystem,
    Ellipse,
    LineSegment,
    Sketch,
)
from PanCAD.geometry.constants import ConstraintReference
from PanCAD.geometry.constraints import (
    Coincident,
    Diameter,
    Distance,
    Horizontal,
    Vertical,
)

def circle(coordinate_system: CoordinateSystem=None,
           plane_reference: ConstraintReference=ConstraintReference.XY,
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
        Diameter(circle, ConstraintReference.CORE,
                 radius, unit=unit),
        Coincident(circle, ConstraintReference.CENTER,
                   sketch, ConstraintReference.ORIGIN)
    ]
    return sketch

def square(coordinate_system: CoordinateSystem=None,
           plane_reference: ConstraintReference=ConstraintReference.XY,
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
            Horizontal(b, ConstraintReference.CORE),
            Vertical(r, ConstraintReference.CORE),
            Horizontal(t, ConstraintReference.CORE),
            Vertical(l, ConstraintReference.CORE),
            Coincident(b, ConstraintReference.START,
                       l, ConstraintReference.END),
            Coincident(b, ConstraintReference.END,
                       r, ConstraintReference.START),
            Coincident(r, ConstraintReference.END,
                       t, ConstraintReference.START),
            Coincident(t, ConstraintReference.END,
                       l, ConstraintReference.START),
            Distance(b, ConstraintReference.CORE,
                     t, ConstraintReference.CORE,
                     side, unit="mm"),
            Distance(r, ConstraintReference.CORE,
                     l, ConstraintReference.CORE,
                     side, unit="mm"),
            Coincident(b, ConstraintReference.START,
                       sketch, ConstraintReference.ORIGIN),
        ]
    
    return sketch

def ellipse(coordinate_system: CoordinateSystem=None,
            plane_reference: ConstraintReference=ConstraintReference.XY,
            name: str = "Test Ellipse",
            center: tuple[Real]=None,
            semi_major_axis: Real=2,
            semi_minor_axis: Real=1,
            angle_degrees: Real=45) -> Sketch:
    """Returns an angled ellipse in a sketch."""
    if center is None:
        center = (0, 0)
    geometry = [
        Ellipse.from_angle(center,
                           semi_major_axis,
                           semi_minor_axis,
                           radians(angle_degrees))
    ]
    sketch = Sketch(coordinate_system=coordinate_system,
                    plane_reference=plane_reference,
                    geometry=geometry,
                    name=name)
    return sketch