"""A module providing functions to generate FreeCAD sketch constraints from 
PanCAD constraints"""

from functools import singledispatch

from PanCAD.cad.freecad import App, Sketcher
from PanCAD.cad.freecad.constants import EdgeSubPart, ConstraintType

from PanCAD.geometry import Sketch, LineSegment
from PanCAD.geometry.constraints import (
    AbstractConstraint,
    Vertical, Horizontal,
    Angle, Distance, HorizontalDistance, VerticalDistance, 
    Radius, Diameter,
    Coincident, Equal, Perpendicular, Parallel
)
from PanCAD.geometry.constants import ConstraintReference, SketchConstraint
from PanCAD.utils.trigonometry import is_clockwise

# Primary Translation Functions ################################################
def translate_constraint(sketch: Sketch,
                         constraint: AbstractConstraint) -> Sketcher.Constraint:
    """Returns a FreeCAD constraint from a PanCAD constraint.
    
    :param sketch: A PanCAD Sketch.
    :param constraint: A constraint in the sketch.
    :returns: The equivalent FreeCAD constraint.
    """
    if isinstance(constraint, Distance):
        geometry_inputs = bug_fix_001_distance(sketch, constraint)
    else:
        geometry_inputs = _get_freecad_inputs(sketch, constraint)
    return freecad_constraint(constraint, geometry_inputs)

def add_pancad_sketch_constraint(constraint: Sketcher.Constraint,
                                 pancad_sketch: Sketch) -> Sketch:
    """Adds a FreeCAD constraint to a PanCAD Sketch.
    
    :param constraint: A FreeCAD Sketcher Constraint read from a FreeCAD model.
    :param pancad_sketch: A PanCAD sketch.
    :returns: The updated PanCAD sketch.
    """
    match constraint.Type:
        case ConstraintType.ANGLE:
            pass
        case ConstraintType.COINCIDENT:
            return _add_state(constraint, pancad_sketch,
                              SketchConstraint.COINCIDENT)
        case ConstraintType.DIAMETER:
            return _add_distance(constraint, pancad_sketch,
                                 SketchConstraint.DISTANCE_DIAMETER)
        case ConstraintType.DISTANCE:
            return _add_distance(constraint, pancad_sketch,
                                 SketchConstraint.DISTANCE)
        case ConstraintType.DISTANCE_X:
            return _add_distance(constraint, pancad_sketch,
                                 SketchConstraint.DISTANCE_HORIZONTAL)
        case ConstraintType.DISTANCE_Y:
            return _add_distance(constraint, pancad_sketch,
                                 SketchConstraint.DISTANCE_VERTICAL)
        case ConstraintType.EQUAL:
            return _add_state(constraint, pancad_sketch,
                              SketchConstraint.EQUAL)
        case ConstraintType.HORIZONTAL:
            return _add_snapto(constraint, pancad_sketch,
                               SketchConstraint.HORIZONTAL)
        case ConstraintType.PARALLEL:
            return _add_state(constraint, pancad_sketch,
                              SketchConstraint.PARALLEL)
        case ConstraintType.PERPENDICULAR:
            return _add_state(constraint, pancad_sketch,
                              SketchConstraint.PERPENDICULAR)
        case ConstraintType.POINT_ON_OBJECT:
            pass
        case ConstraintType.RADIUS:
            return _add_distance(constraint, pancad_sketch,
                                 SketchConstraint.DISTANCE_RADIUS)
        case ConstraintType.VERTICAL:
            return _add_snapto(constraint, pancad_sketch,
                               SketchConstraint.VERTICAL)
        case ConstraintType.TANGENT:
            pass
        case _:
            raise ValueError(f"Unsupported type {constraint.Type}")

# PanCAD Constraint Functions ##################################################

def _add_state(constraint: Sketcher.Constraint,
               pancad_sketch: Sketch,
               state_type: SketchConstraint) -> Sketch:
    index_a, reference_a = _get_pancad_index_pair(constraint.First,
                                                  constraint.FirstPos)
    index_b, reference_b = _get_pancad_index_pair(constraint.Second,
                                                  constraint.SecondPos)
    pancad_sketch.add_constraint_by_index(state_type,
                                          index_a, reference_a,
                                          index_b, reference_b)
    return pancad_sketch

def _add_snapto(constraint: Sketcher.Constraint,
                pancad_sketch: Sketch,
                snap_type: SketchConstraint) -> Sketch:
    index_a, reference_a = _get_pancad_index_pair(constraint.First,
                                                  constraint.FirstPos)
    index_b, reference_b = _get_pancad_index_pair(constraint.Second,
                                                  constraint.SecondPos)
    pancad_sketch.add_constraint_by_index(snap_type,
                                          index_a, reference_a,
                                          index_b, reference_b)
    return pancad_sketch

def _add_distance(constraint: Sketcher.Constraint,
                  pancad_sketch: Sketch,
                  distance_type: SketchConstraint) -> Sketch:
    index_a, reference_a = _get_pancad_index_pair(constraint.First,
                                                  constraint.FirstPos)
    index_b, reference_b = _get_pancad_index_pair(constraint.Second,
                                                  constraint.SecondPos)
    pancad_sketch.add_constraint_by_index(distance_type,
                                          index_a, reference_a,
                                          index_b, reference_b,
                                          value=constraint.Value,
                                          unit="mm")
    return pancad_sketch

# Constraint Dispatch Functions ################################################
@singledispatch
def freecad_constraint(constraint: AbstractConstraint,
                       args: tuple) -> Sketcher.Constraint:
    """Returns a FreeCAD constraint that can be placed in a FreeCAD Sketch.
    
    :param constraint: A PanCAD constraint.
    :param args: The FreeCAD subpart arguments obtained from 
        :func:`_get_freecad_inputs` or an equivalent method.
    """
    raise NotImplementedError(f"Unsupported 1st type {constraint.__class__}")

@freecad_constraint.register
def _angle(constraint: Angle, args: tuple) -> Sketcher.Constraint:
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
def _coincident(constraint: Coincident, args: tuple) -> Sketcher.Constraint:
    return Sketcher.Constraint("Coincident", *args)

@freecad_constraint.register
def _diameter(constraint: Diameter, args: tuple) -> Sketcher.Constraint:
    geometry_index, _ = args
    value_str = f"{constraint.value} {constraint.unit}"
    return Sketcher.Constraint("Diameter", geometry_index,
                               App.Units.Quantity(value_str))

@freecad_constraint.register
def _distance(constraint: Distance, args: tuple) -> Sketcher.Constraint:
    value_str = f"{constraint.value} {constraint.unit}"
    return Sketcher.Constraint("Distance", *args, App.Units.Quantity(value_str))

@freecad_constraint.register
def _horizontal(constraint: Horizontal, args: tuple) -> Sketcher.Constraint:
    if len(constraint.get_constrained()) == 1:
        geometry_index, _ = args
        return Sketcher.Constraint("Horizontal", geometry_index)
    else:
        return Sketcher.Constraint("Horizontal", *args)

@freecad_constraint.register
def _radius(constraint: Radius, args: tuple) -> Sketcher.Constraint:
    geometry_index, _ = args
    value_str = f"{constraint.value} {constraint.unit}"
    return Sketcher.Constraint("Radius", geometry_index,
                               App.Units.Quantity(value_str))

@freecad_constraint.register
def _vertical(constraint: Vertical, args: tuple) -> Sketcher.Constraint:
    if len(constraint.get_constrained()) == 1:
        geometry_index, _ = args
        return Sketcher.Constraint("Vertical", geometry_index)
    else:
        return Sketcher.Constraint("Vertical", *args)

@freecad_constraint.register
def _equal(constraint: Equal, args: tuple) -> Sketcher.Constraint:
    return Sketcher.Constraint("Equal", *args[0::2])

@freecad_constraint.register
def _perpendicular(constraint: Perpendicular,
                   args: tuple) -> Sketcher.Constraint:
    return Sketcher.Constraint("Perpendicular", *args[0::2])

@freecad_constraint.register
def _parallel(constraint: Parallel, args: tuple) -> Sketcher.Constraint:
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
        a_i, a_ref, b_i, b_ref = _get_freecad_inputs(sketch, constraint)
        return (a_i, EdgeSubPart.START, b_i)
    else:
        return _get_freecad_inputs(sketch, constraint)

def _get_freecad_inputs(sketch: Sketch,
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

def _get_pancad_index_pair(index: int,
                           sub_part: EdgeSubPart | int
                           ) -> tuple[int | ConstraintReference]:
    if index >= 0:
        pancad_index = index
        pancad_reference = subpart_to_reference(sub_part)
    else:
        if index in [-1, -2]:
            pancad_index = -1
            if sub_part == EdgeSubPart.START:
                pancad_reference = ConstraintReference.ORIGIN
            elif index == -1 and sub_part == EdgeSubPart.EDGE:
                pancad_reference = ConstraintReference.X
            elif index == -2 and sub_part == EdgeSubPart.EDGE:
                pancad_reference = ConstraintReference.Y
            else:
                raise ValueError("Unexpected coordinate system"
                                 f" subpart {sub_part}")
        elif index == -2000:
            pancad_index = None
            pancad_reference = None
        else:
            raise NotImplementedError("External references have not been"
                                      " implemented yet, see issue #87")
    return pancad_index, pancad_reference

def map_to_subpart(reference: ConstraintReference) -> EdgeSubPart:
    """Returns the EdgeSubPart that matches the PanCAD ConstraintReference.
    
    :param reference: A reference to a subpart of geometry.
    :returns: The FreeCAD equivalent to the reference.
    """
    match reference:
        case ConstraintReference.CORE:
            return EdgeSubPart.EDGE
        case ConstraintReference.X:
            return EdgeSubPart.EDGE
        case ConstraintReference.Y:
            return EdgeSubPart.EDGE
        case ConstraintReference.START:
            return EdgeSubPart.START
        case ConstraintReference.END:
            return EdgeSubPart.END
        case ConstraintReference.CENTER:
            return EdgeSubPart.CENTER
        case _:
            raise ValueError(f"Unsupported reference: {reference}")

def subpart_to_reference(sub_part: EdgeSubPart) -> ConstraintReference:
    """Returns the PanCAD ConstraintReference that matches the FreeCAD 
    EdgeSubPart.
    
    :param reference: A reference to a subpart of geometry.
    :returns: The FreeCAD equivalent to the reference.
    """
    match sub_part:
        case EdgeSubPart.EDGE:
            return ConstraintReference.CORE
        case EdgeSubPart.START:
            return ConstraintReference.START
        case EdgeSubPart.END:
            return ConstraintReference.END
        case EdgeSubPart.CENTER:
            return ConstraintReference.CENTER
        case _:
            raise ValueError(f"Unsupported subpart: {sub_part}")
