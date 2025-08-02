"""A module providing functions to generate FreeCAD sketch constraints from 
PanCAD constraints"""

from functools import singledispatch

from PanCAD.cad.freecad import App, Sketcher
from PanCAD.cad.freecad.constants import EdgeSubPart

from PanCAD.geometry import Sketch, LineSegment
from PanCAD.geometry.constraints.abstract_constraint import AbstractConstraint
from PanCAD.geometry.constraints import (
    Vertical, Horizontal,
    Angle, Distance, HorizontalDistance, VerticalDistance, 
    Radius, Diameter,
    Coincident, Equal, Perpendicular, Parallel
)
from PanCAD.geometry.constants import ConstraintReference
from PanCAD.utils.trigonometry import is_clockwise

# Primary Translation Function #################################################
def translate_constraint(sketch: Sketch,
                         constraint: AbstractConstraint):
    if isinstance(constraint, Distance):
        geometry_inputs = bug_fix_001_distance(sketch, constraint)
    else:
        geometry_inputs = get_constraint_inputs(sketch, constraint)
    
    return freecad_constraint(constraint, geometry_inputs)

# Constraint Dispatch Functions ################################################
@singledispatch
def freecad_constraint(constraint: AbstractConstraint,
                       args: tuple) -> Sketcher.Constraint:
    """Returns a FreeCAD constraint that can be placed in a FreeCAD Sketch."""
    raise NotImplementedError(f"Unsupported 1st type {constraint.__class__}")

@freecad_constraint.register
def freecad_constraint_angle(constraint: Angle,
                             args: tuple) -> Sketcher.Constraint:
    match constraint.quadrant:
        case 1:
            iline1, iline2 = args[0::2]
            pointpos1, pointpos2 = 1, 1
        case 2:
            iline2, iline1 = args[0::2]
            pointpos1, pointpos2 = 1, 2
        case 3:
            iline1, iline2 = args[0::2]
            pointpos1, pointpos2 = 2, 1
        case 4:
            iline2, iline1 = args[0::2]
            pointpos1, pointpos2 = 1, 1
    
    angle_value_str = App.Units.Quantity(f"{constraint.value} deg")
    return Sketcher.Constraint("Angle", iline1, pointpos1, iline2, pointpos2,
                               angle_value_str)

@freecad_constraint.register
def freecad_constraint_coincident(constraint: Coincident,
                                  args: tuple) -> Sketcher.Constraint:
    return Sketcher.Constraint("Coincident", *args)

@freecad_constraint.register
def freecad_constraint_diameter(constraint: Diameter,
                                args: tuple) -> Sketcher.Constraint:
    geometry_index, _ = args
    value_str = f"{constraint.value} {constraint.unit}"
    return Sketcher.Constraint("Diameter", geometry_index,
                               App.Units.Quantity(value_str))

@freecad_constraint.register
def freecad_constraint_distance(constraint: Distance,   
                                args: tuple) -> Sketcher.Constraint:
    value_str = f"{constraint.value} {constraint.unit}"
    return Sketcher.Constraint("Distance", *args, App.Units.Quantity(value_str))

@freecad_constraint.register
def freecad_constraint_horizontal(constraint: Horizontal,
                                  args: tuple) -> Sketcher.Constraint:
    if len(constraint.get_constrained()) == 1:
        geometry_index, _ = args
        return Sketcher.Constraint("Horizontal", geometry_index)
    else:
        return Sketcher.Constraint("Horizontal", *args)

@freecad_constraint.register
def freecad_constraint_radius(constraint: Radius,
                              args: tuple) -> Sketcher.Constraint:
    geometry_index, _ = args
    value_str = f"{constraint.value} {constraint.unit}"
    return Sketcher.Constraint("Radius", geometry_index,
                               App.Units.Quantity(value_str))

@freecad_constraint.register
def freecad_constraint_vertical(constraint: Vertical,
                                args: tuple) -> Sketcher.Constraint:
    if len(constraint.get_constrained()) == 1:
        geometry_index, _ = args
        return Sketcher.Constraint("Vertical", geometry_index)
    else:
        return Sketcher.Constraint("Vertical", *args)

@freecad_constraint.register
def freecad_constraint_equal(constraint: Equal,
                             args: tuple) -> Sketcher.Constraint:
    return Sketcher.Constraint("Equal", *args[0::2])

@freecad_constraint.register
def freecad_constraint_perpendicular(constraint: Perpendicular,
                                     args: tuple) -> Sketcher.Constraint:
    return Sketcher.Constraint("Perpendicular", *args[0::2])

@freecad_constraint.register
def freecad_constraint_parallel(constraint: Parallel,
                                args: tuple) -> Sketcher.Constraint:
    return Sketcher.Constraint("Parallel", *args[0::2])

# Utility Functions ############################################################
def bug_fix_001_distance(sketch: Sketch, constraint: Distance) -> tuple[int]:
    """Returns a modified constraint input tuple that takes into account FreeCAD 
    distance bugs.
    
    Known bugs
    - Distance between two parallel lines is actually stored as a distance 
    between the start point of the first line and the edge of the second 
    line. This causes undefined behavior when the orientation constraint that 
    made it possible to place the distance constraint is removed without 
    removing the distance constraint. Additionally, this scenario takes fewer 
    geometry inputs than normal (3 instead of 4).
    
    :param sketch: A PanCAD sketch.
    :param constraint: A PanCAD Distance constraint.
    :returns: A tuple of integer inputs to define a FreeCAD constraint.
    """
    original_inputs = zip(constraint.get_constrained(),
                          constraint.get_references())
    if all([isinstance(g, LineSegment) and r == ConstraintReference.CORE
            for g, r in original_inputs]):
        a_i, a_ref, b_i, b_ref = get_constraint_inputs(sketch, constraint)
        return (a_i, EdgeSubPart.START, b_i)
    else:
        return get_constraint_inputs(sketch, constraint)

def get_constraint_inputs(sketch: Sketch,
                          constraint: AbstractConstraint) -> tuple[int]:
    """Returns the indices required to reference constraint geometry in FreeCAD. 
    FreeCAD references the sketch origin, x-axis, and y-axis with hidden 
    external geometry elements. The origin is the start point of the x-axis 
    line, the x-axis line is at index -1, and the y-axis line is at index 
    -2. If those elements are referenced then they need to be mapped differently 
    than they are in PanCAD and likely other programs.
    
    :param sketch: A PanCAD sketch.
    :param constraint: A PanCAD Distance constraint.
    :returns: A tuple of integer inputs to define a FreeCAD constraint.
    """
    original_inputs = zip(constraint.get_constrained(),
                          constraint.get_references())
    freecad_inputs = tuple()
    for constrained, reference in original_inputs:
        if constrained is sketch.get_sketch_coordinate_system():
            # FreeCAD keeps its sketch coordinate system in negative index 
            # locations, so this is a special case for constraints.
            match reference:
                case ConstraintReference.ORIGIN:
                    index = -1
                    subpart = EdgeSubPart.START
                case ConstraintReference.X:
                    index = -1
                    subpart = EdgeSubPart.EDGE
                case ConstraintReference.Y:
                    index = -2
                    subpart = EdgeSubPart.EDGE
                case _:
                    raise ValueError(f"Invalid ConstraintReference {reference}")
        else:
            index = sketch.get_index_of(constrained)
            subpart = map_to_subpart(reference)
        freecad_inputs = freecad_inputs + (index, subpart)
    return freecad_inputs

def map_to_subpart(pancad_reference: ConstraintReference) -> EdgeSubPart:
    """Returns the EdgeSubPart that matches the PanCAD constraint reference.
    
    :param pancad_reference: A reference to a subpart of geometry.
    :returns: The FreeCAD equivalent to the pancad_reference.
    """
    match pancad_reference:
        case ConstraintReference.CORE:
            return EdgeSubPart.EDGE
        case ConstraintReference.START:
            return EdgeSubPart.START
        case ConstraintReference.END:
            return EdgeSubPart.END
        case ConstraintReference.CENTER:
            return EdgeSubPart.CENTER