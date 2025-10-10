"""A module providing functions to generate FreeCAD sketch constraints from 
PanCAD constraints"""
from __future__ import annotations

from functools import singledispatch, singledispatchmethod
from typing import TYPE_CHECKING

from PanCAD.geometry import LineSegment
from PanCAD.geometry.constraints import (
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
    make_constraint,
)
from PanCAD.geometry.constants import ConstraintReference

from . import App, Sketcher
from ._application_types import FreeCADConstraint
from .constants import (
    ConstraintType, EdgeSubPart, InternalAlignmentType, ListName
)

if TYPE_CHECKING:
    from uuid import UUID
    from PanCAD.geometry import Sketch, AbstractGeometry, AbstractFeature
    from PanCAD.geometry.constants import SketchConstraint
    from PanCAD.geometry.constraints import (AbstractConstraint,
                                             AbstractStateConstraint,
                                             AbstractSnapTo,
                                             Abstract2GeometryDistance)
    from ._application_types import FreeCADSketch
    from ._map_typing import SketchElementID

################################################################################
# FreeCAD ---> PanCAD Constraints
################################################################################
def _freecad_to_pancad_constraint(self,
                                  constraint_id: SketchElementID
                                  ) -> AbstractConstraint:
    """Returns a FreeCAD constraint that can be placed into a PanCAD Sketch.
    
    :param constraint_id: A FreeCAD constraint FreeCADID.
    :returns: The equivalent PanCAD constraint.
    """
    constraint_type = ConstraintType(self._id_map[constraint_id].Type)
    match constraint_type:
        case ConstraintType.ANGLE:
            pass
        case (
                    ConstraintType.COINCIDENT
                    | ConstraintType.EQUAL
                    | ConstraintType.PARALLEL
                    | ConstraintType.PERPENDICULAR
                    | ConstraintType.POINT_ON_OBJECT
                    | ConstraintType.TANGENT
                    | ConstraintType.HORIZONTAL
                    | ConstraintType.VERTICAL
                ):
            return _add_state_or_snapto(self,
                                        constraint_id,
                                        constraint_type.get_sketch_constraint())
        case (
                    ConstraintType.DIAMETER
                    | ConstraintType.DISTANCE
                    | ConstraintType.DISTANCE_X
                    | ConstraintType.DISTANCE_Y
                    | ConstraintType.RADIUS
                ):
            return _add_distance(self,
                                 constraint_id,
                                 constraint_type.get_sketch_constraint())
        case _:
            raise ValueError(f"Unsupported type {constraint.Type}")

def _add_state_or_snapto(self,
                         constraint_id: SketchElementID,
                         constraint_type: SketchConstraint
                         ) -> AbstractStateConstraint | AbstractSnapTo:
    """Returns a PanCAD state or snapto equivalent constraint from a FreeCAD 
    constraint.
    
    :param constraint_id: The FreeCADID for the FreeCAD constraint.
    :param constraint_type: The SketchConstraint for the FreeCAD constraint's 
        type.
    :returns: The equivalent state or snapto constraint.
    """
    constraint_pairs = zip(
        self._constraint_map.get_constrained_ids(constraint_id),
        self._constraint_map.get_constrained_sub_parts(constraint_id),
    )
    pancad_paired_inputs = []
    for freecad_id, sub_part in constraint_pairs:
        pancad_paired_inputs.extend(
            _get_pancad_pair(self, freecad_id, sub_part)
        )
    return make_constraint(constraint_type, *pancad_paired_inputs)

def _add_distance(self,
                  constraint_id: SketchElementID,
                  constraint_type: SketchConstraint
                  ) -> Abstract2GeometryDistance:
    """Returns a PanCAD distance equivalent constraint from a FreeCAD
    constraint.
    
    :param constraint_id: The FreeCADID for the FreeCAD constraint.
    :param constraint_type: The SketchConstraint for the FreeCAD constraint's 
        type.
    :returns: The equivalent distance type constraint.
    """
    freecad_constraint = self._id_map[constraint_id]
    
    constraint_pairs = zip(
        self._constraint_map.get_constrained_ids(constraint_id),
        self._constraint_map.get_constrained_sub_parts(constraint_id),
    )
    pancad_paired_inputs = []
    for freecad_id, sub_part in constraint_pairs:
        pancad_paired_inputs.extend(
            _get_pancad_pair(self, freecad_id, sub_part)
        )
    
    return make_constraint(constraint_type,
                           *pancad_paired_inputs,
                           value=freecad_constraint.Value,
                           unit="mm")

def _get_pancad_pair(self,
                     geometry_id: SketchElementID,
                     sub_part: EdgeSubPart
                     ) -> tuple[AbstractGeometry | AbstractFeature,
                                ConstraintReference]:
    """Returns the equivalent PanCAD geometry and mapped constraint reference 
    for a given FreeCAD geometry and subpart.
    
    :param geometry_id: The FreeCADID for a FreeCAD geometry element.
    :param sub_part: The EdgeSubPart referring to the portion of the FreeCAD 
        geometry.
    :returns: A tuple of the PanCAD geometry and its associated 
        ConstraintReference
    """
    if self._constraint_map.is_internal_geometry(geometry_id):
        constrained_geometry_id = self._constraint_map \
                                      .get_parent_geometry_id(geometry_id)
        geometry, sub_reference = self.get_pancad(constrained_geometry_id)
        alignment_type = InternalAlignmentType(
            self._constraint_map.get_internal_alignment_type(sub_part)
        )
        reference = alignment_type.get_constraint_reference(sub_part)
    else:
        geometry, sub_reference = self.get_pancad(geometry_id)
        
        reference = sub_part.get_constraint_reference(geometry, sub_reference)
    if geometry is None:
        return None, None
    else:
        return geometry, reference

################################################################################
# Constraint Addition
################################################################################

def _freecad_to_pancad_add_constraints(self,
                                       freecad_sketch: FreeCADSketch,
                                       sketch: Sketch) -> Sketch:
    """Adds the constraints in a FreeCAD Sketch to a PanCAD Sketch.
    
    :param freecad_sketch: The FreeCAD sketch to read constraints from.
    :param sketch: The PanCAD sketch to add constraints to.
    :returns: The updated PanCAD sketch.
    """
    for i, freecad_constraint in enumerate(freecad_sketch.Constraints):
        if freecad_constraint.Type == ConstraintType.INTERNAL_ALIGNMENT:
            # Skip internal alignment constraints, not needed for PanCAD
            continue
        constraint_id = (freecad_sketch.ID, ListName.CONSTRAINTS, i)
        self._id_map[constraint_id] = freecad_constraint
        constraint = self._freecad_to_pancad_constraint(constraint_id)
        sketch.add_constraint(constraint)
        self._link_constraints(constraint, constraint_id)
    return sketch

def _pancad_to_freecad_add_constraints(self,
                                       pancad_sketch: Sketch, 
                                       sketch: FreeCADSketch) -> FreeCADSketch:
    """Adds the constraints in a PanCAD Sketch to a FreeCAD Sketch.
    
    :param pancad_sketch: The PanCAD sketch to read constraints from.
    :param sketch: The FreeCAD sketch to add constraints to.
    :returns: The updated FreeCAD sketch.
    """
    for pancad_constraint in pancad_sketch.constraints:
        constraint = self._pancad_to_freecad_constraint(pancad_constraint)
        index = len(sketch.Constraints)
        sketch.addConstraint(constraint)
        constraint_id = (sketch.ID, ListName.CONSTRAINTS, index)
        self._id_map[constraint_id] = constraint
        self._link_constraints(pancad_constraint, constraint_id)
    return sketch

def _link_constraints(self,
                      pancad_constraint: AbstractConstraint,
                      freecad_constraint_id: SketchElementID) -> None:
    """Creates a link between a PanCAD constraint and a FreeCAD constraint. This 
    linking is the same regardless of which software the map is originating from.
    
    :param pancad_constraint: The PanCAD constraint to link.
    :param freecad_constraint: The FreeCADID for the FreeCAD constraint to link.
    """
    constrained_ids = tuple()
    for geometry, reference in zip(pancad_constraint.get_constrained(),
                                   pancad_constraint.get_references()):
        freecad_id = self.get_freecad_id(geometry, reference)
        constrained_ids = constrained_ids + ((*freecad_id, reference),)
    self._pancad_to_freecad[pancad_constraint.uid] = (pancad_constraint,
                                                      freecad_constraint_id)
    self._freecad_to_pancad[freecad_constraint_id] = (pancad_constraint,
                                                      ConstraintReference.CORE)
    self._constraint_map[freecad_constraint_id] = constrained_ids

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
    # Constraints that always need pairs of indexes and subparts
    
    constraint_type = ConstraintType.from_pancad(constraint)
    inputs = []
    for geometry, reference in zip(constraint.get_constrained(),
                                   constraint.get_references()):
        # Needs pairs of indices and edge sub parts
        freecad_id = self.get_freecad_id(geometry, reference)
        index = self._constraint_map.get_constraint_index(freecad_id)
        sub_part = EdgeSubPart.from_constraint_reference(reference)
        inputs.extend([index, sub_part])
    return Sketcher.Constraint(constraint_type, *inputs)

@_pancad_to_freecad_constraint.register
def _index_and_value(self, constraint: Diameter | Radius) -> FreeCADConstraint:
    # Constraints that need one index and a value
    
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
    # For constraints that sometimes need just an index, but sometimes need an 
    # index and a subpart.
    
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
            sub_part = EdgeSubPart.from_constraint_reference(reference)
            inputs.extend([index, sub_part])
        return Sketcher.Constraint(constraint_type, *inputs)

@_pancad_to_freecad_constraint.register
def _index_only(self, constraint: Equal | Parallel | Perpendicular
                ) -> FreeCADConstraint:
    # For constraints that only need indices, no sub parts
    
    inputs = []
    constraint_type = ConstraintType.from_pancad(constraint)
    for geometry, reference in zip(constraint.get_constrained(),
                                   constraint.get_references()):
        # Needs list of indices
        freecad_id = self.get_freecad_id(geometry, reference)
        index = self._constraint_map.get_constraint_index(freecad_id)
        sub_part = EdgeSubPart.from_constraint_reference(reference)
        inputs.append(index)
    return Sketcher.Constraint(constraint_type, *inputs)

@_pancad_to_freecad_constraint.register
def _distance(self,
              constraint: Distance | HorizontalDistance | VerticalDistance
              ) -> FreeCADConstraint:
    # For distance constraints since FreeCAD has a bug in how it defines 
    # distances.
    
    inputs = []
    constraint_type = ConstraintType.from_pancad(constraint)
    pancad_pairs = list(
        zip(constraint.get_constrained(), constraint.get_references())
    )
    for geometry, reference in pancad_pairs:
        # Needs pairs of indices and edge sub parts
        freecad_id = self.get_freecad_id(geometry, reference)
        index = self._constraint_map.get_constraint_index(freecad_id)
        sub_part = EdgeSubPart.from_constraint_reference(reference)
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
    
    freecad_value = App.Units.Quantity(f"{constraint.value} {constraint.unit}")
    return Sketcher.Constraint(constraint_type, *inputs, freecad_value)