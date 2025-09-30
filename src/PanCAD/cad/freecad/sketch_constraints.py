"""A module providing functions to generate FreeCAD sketch constraints from 
PanCAD constraints"""

from functools import singledispatch, singledispatchmethod

from PanCAD.geometry import Sketch, LineSegment
from PanCAD.geometry.constraints import (
    AbstractConstraint,
    Angle,
    Coincident,
    Diameter,
    Distance,
    Equal,
    Horizontal,
    HorizontalDistance,
    Parallel,
    Perpendicular,
    Radius,
    Vertical,
    VerticalDistance,
)
from PanCAD.geometry.constants import ConstraintReference, SketchConstraint
from PanCAD.utils.trigonometry import is_clockwise

from . import App, Sketcher, FreeCADConstraint, FreeCADSketch
from .constants import ConstraintType, EdgeSubPart, ListName

# Primary Translation Functions ################################################
def translate_constraint(sketch: Sketch,
                         constraint: AbstractConstraint) -> FreeCADConstraint:
    """Returns a FreeCAD constraint from a PanCAD constraint.
    
    :param sketch: A PanCAD Sketch.
    :param constraint: A constraint in the sketch.
    :returns: The equivalent FreeCAD constraint.
    """
    if isinstance(constraint, Distance):
        geometry_inputs = bug_fix_001_distance(sketch, constraint)
    else:
        geometry_inputs = _get_freecad_inputs(sketch, constraint)
    return _pancad_to_freecad_constraint(constraint, geometry_inputs)

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

################################################################################
# PanCAD ---> FreeCAD Constraint Addition
################################################################################

# for constraint in key.constraints:
        # constraint_index = len(sketch.Constraints)
        # new_constraint = translate_constraint(key, constraint)
        # sketch.addConstraint(new_constraint)
        # constraint_id = (sketch.ID, ListName.CONSTRAINTS, constraint_index)
        # constrained_ids = tuple()
        # for parent, reference in zip(constraint.get_constrained(),
                                     # constraint.get_references()):
            # sketch_geometry_id = self.get_freecad_id(parent, reference)
            # constrained_ids = constrained_ids + (
                # (*sketch_geometry_id, reference),
            # )
        # self._pancad_to_freecad[constraint.uid] = (constraint,
                                                   # constraint_id)
        # self._freecad_to_pancad[constraint_id] = (constraint.uid,
                                                  # ConstraintReference.CORE)
        # self._id_map[constraint_id] = new_constraint
        # self._constraint_map[constraint_id] = constrained_ids

def _pancad_to_freecad_add_constraints(self,
                                       pancad_sketch: Sketch, 
                                       sketch: FreeCADSketch) -> FreeCADSketch:
    """Adds the constraints in a PanCAD Sketch to a FreeCAD Sketch."""
    for pancad_constraint in pancad_sketch.constraints:
        constraint = self._pancad_to_freecad_constraint(pancad_constraint)
        index = len(sketch.Constraints)
        sketch.addConstraint(constraint)
        constraint_id = (sketch.ID, ListName.CONSTRAINTS, index)
        constrained_ids = tuple()
        for geometry, reference in zip(pancad_constraint.get_constrained(),
                                       pancad_constraint.get_references()):
            freecad_id = self.get_freecad_id(geometry, reference)
            constrained_ids = constrained_ids + ((*freecad_id, reference),)
        self._id_map[constraint_id] = constraint
        self._pancad_to_freecad[pancad_constraint.uid] = (pancad_constraint,
                                                          constraint_id)
        self._freecad_to_pancad[constraint_id] = (pancad_constraint.uid,
                                                  ConstraintReference.CORE)
        self._constraint_map[constraint_id] = constrained_ids
    return sketch

################################################################################
# PanCAD ---> FreeCAD Constraints
################################################################################
@singledispatchmethod
def _pancad_to_freecad_constraint(self, constraint: AbstractConstraint
                                  ) -> FreeCADConstraint:
    """Returns a FreeCAD constraint that can be placed in a FreeCAD Sketch.
    
    :param constraint: A PanCAD constraint.
    """
    raise NotImplementedError(f"Unsupported 1st type {constraint.__class__}")

@_pancad_to_freecad_constraint.register
def _angle(self, constraint: Angle) -> FreeCADConstraint:
    constraint_type = ConstraintType.from_pancad(constraint)
    indices = []
    for geometry, reference in zip(constraint.get_constrained(),
                                   constraint.get_references()):
        # Need indices of the line segments
        freecad_id = self.get_freecad_id(geometry, reference)
        indices.append(self._constraint_map.get_constraint_index(freecad_id))
    
    match constraint.quadrant:
        case 1:
            line_1_index, line_2_index = indices
            sub_part_1, sub_part_2 = EdgeSubPart.START, EdgeSubPart.START
        case 2:
            line_2_index, line_1_index = indices
            sub_part_1, sub_part_2 = EdgeSubPart.START, EdgeSubPart.END
        case 3:
            line_1_index, line_2_index = indices
            sub_part_1, sub_part_2 = EdgeSubPart.END, EdgeSubPart.START
        case 4:
            line_2_index, line_1_index = indices
            sub_part_1, sub_part_2 = EdgeSubPart.START, EdgeSubPart.START
    
    freecad_value = App.Units.Quantity(f"{constraint.value} deg")
    return Sketcher.Constraint(constraint_type,
                               line_1_index, sub_part_1,
                               line_2_index, sub_part_2,
                               freecad_value)

@_pancad_to_freecad_constraint.register
def _index_and_subpart(self, constraint: Coincident) -> FreeCADConstraint:
    constraint_type = ConstraintType.from_pancad(constraint)
    inputs = []
    for geometry, reference in zip(constraint.get_constrained(),
                                   constraint.get_references()):
        # Needs pairs of indices and edge sub parts
        freecad_id = self.get_freecad_id(geometry, reference)
        index = self._constraint_map.get_constraint_index(freecad_id)
        sub_part = reference_to_subpart(reference)
        inputs.extend([index, sub_part])
    return Sketcher.Constraint(constraint_type, *inputs)

@_pancad_to_freecad_constraint.register
def _index_and_value(self, constraint: Diameter | Radius) -> FreeCADConstraint:
    constraint_type = ConstraintType.from_pancad(constraint)
    # Assumes that there is only one constrained geometry, which should be the 
    # case for Diameter and Radius
    freecad_id = self.get_freecad_id(constraint.get_constrained()[0],
                                     constraint.get_references()[0])
    index = self._constraint_map.get_constraint_index(freecad_id)
    freecad_value = App.Units.Quantity(f"{constraint.value} {constraint.unit}")
    return Sketcher.Constraint(constraint_type, index, freecad_value)

@_pancad_to_freecad_constraint.register
def _index_and_subpart_optional(self, constraint: Horizontal | Vertical
                                ) -> FreeCADConstraint:
    constraint_type = ConstraintType.from_pancad(constraint)
    if len(constraint.get_constrained()) == 1:
        # Needs just an index
        geometry = constraint.get_constrained()[0]
        reference = constraint.get_references()[0]
        freecad_id = self.get_freecad_id(geometry, reference)
        index = self._constraint_map.get_constraint_index(freecad_id)
        return Sketcher.Constraint(constraint_type, index)
    else:
        inputs = []
        for geometry, reference in zip(constraint.get_constrained(),
                                       constraint.get_references()):
            # Needs pairs of indices and edge sub parts
            freecad_id = self.get_freecad_id(geometry, reference)
            index = self._constraint_map.get_constraint_index(freecad_id)
            sub_part = reference_to_subpart(reference)
            inputs.extend([index, sub_part])
        return Sketcher.Constraint(constraint_type, *inputs)

@_pancad_to_freecad_constraint.register
def _index_only(self, constraint: Equal | Parallel | Perpendicular
                ) -> FreeCADConstraint:
    inputs = []
    constraint_type = ConstraintType.from_pancad(constraint)
    for geometry, reference in zip(constraint.get_constrained(),
                                   constraint.get_references()):
        # Needs list of indices
        freecad_id = self.get_freecad_id(geometry, reference)
        index = self._constraint_map.get_constraint_index(freecad_id)
        sub_part = reference_to_subpart(reference)
        inputs.append(index)
    return Sketcher.Constraint(constraint_type, *inputs)

@_pancad_to_freecad_constraint.register
def _distance(self, constraint: Distance) -> FreeCADConstraint:
    inputs = []
    constraint_type = ConstraintType.from_pancad(constraint)
    pancad_pairs = list(
        zip(constraint.get_constrained(), constraint.get_references())
    )
    for geometry, reference in pancad_pairs:
        # Needs pairs of indices and edge sub parts
        freecad_id = self.get_freecad_id(geometry, reference)
        index = self._constraint_map.get_constraint_index(freecad_id)
        sub_part = reference_to_subpart(reference)
        inputs.extend([index, sub_part])
    
    is_freecad_bug_001 = all(
        [
            (isinstance(geometry, LineSegment)
             and reference == ConstraintReference.CORE)
            for geometry, reference in pancad_pairs
        ]
    )
    
    if is_freecad_bug_001:
        """freecad_bug_001 description:
        - Distance between two parallel lines is actually stored as a distance 
        between the start point of the first line and the edge of the second 
        line. This causes undefined behavior when the orientation constraint 
        that made it possible to place the distance constraint is removed 
        without removing the distance constraint. Additionally, this 
        scenario takes fewer geometry inputs than normal (3 instead of 4).
        """
        a_index, _, b_index, _ = inputs
        inputs = (a_index, EdgeSubPart.START, b_index)
    else:
        # FreeCAD doesn't use the last reference in all known cases.
        inputs.pop()
    
    freecad_value = App.Units.Quantity(f"{constraint.value} {constraint.unit}")
    return Sketcher.Constraint(constraint_type, *inputs, freecad_value)

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
            subpart = reference_to_subpart(reference)
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

def reference_to_subpart(reference: ConstraintReference) -> EdgeSubPart:
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
        case ConstraintReference.ORIGIN:
            # The origin of sketch coordinate systems in FreeCAD is arbitrarily 
            # the start point of the sketch coordinate system's x-axis line 
            # segment located in the Sketch's ExternalGeo list index 0.
            return EdgeSubPart.START
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
