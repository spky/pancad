"""A module providing functions to query common FreeCAD information using its 
Python API.
"""
from __future__ import annotations

from typing import TYPE_CHECKING
from xml.etree import ElementTree

from .constants import (
    ConstraintType,
    EdgeSubPart,
    ListName,
    InternalAlignmentType,
    SketchNumber,
)

if TYPE_CHECKING:
    from ._application_types import FreeCADSketch
    from ._map_typing import SketchElementID

def get_constraints_on(sketch: FreeCADSketch,
                       geometry_id: SketchElementID,
                       subpart: EdgeSubPart=None,
                       include_internals: bool=False) -> list[SketchElementID]:
    """Returns the ids of the constraints on the geometry.
    
    :param sketch: A FreeCAD Sketch object.
    :param geometry_id: The (Sketch.ID, ListName, Index) of a FreeCAD geometry 
        element in the sketch.
    :param subpart: The constrained subpart of the geometry to filter by.
    :param include_internals: Sets whether to include internal alignment 
        constraints in the result.
    :returns: The list of constraint ids of constraints on the geometry. Returns 
        only  the constraints referencing the subpart if subpart is provided.
    """
    if not in_sketch(sketch, geometry_id):
        raise KeyError(f"id {geometry_id} not found in sketch {sketch.ID}")
    _, list_type, _ = geometry_id
    if list_type not in [ListName.GEOMETRY, ListName.EXTERNALS]:
        raise ValueError(f"id {geometry_id} is for {list_type},"
                         f" not {ListName.GEOMETRY} or {ListName.EXTERNALS}")
    # Ensure that external references are negative
    geometry_index = get_constraint_index(geometry_id)
    
    # Find relevant constraints in sketch
    constraints = []
    for i, constraint in enumerate(sketch.Constraints):
        if constraint.Type == ConstraintType.INTERNAL_ALIGNMENT:
            if not include_internals:
                continue
            id_prefix = (sketch.ID, ListName.INTERNAL_ALIGNMENT)
        else:
            id_prefix = (sketch.ID, ListName.CONSTRAINTS)
        
        geometry = [constraint.First, constraint.Second, constraint.Third]
        if subpart:
            # Filter by subpart
            subparts = [constraint.FirstPos,
                        constraint.SecondPos,
                        constraint.ThirdPos]
            pairs = zip(geometry, subparts)
            if (geometry_index, subpart) in list(pairs):
                constraints.append(id_prefix + (i,))
        elif geometry_index in geometry:
            # No filter
            constraints.append(id_prefix + (i,))
    return constraints

def get_constraint_pairs(sketch: FreeCADSketch,
                         constraint_id: SketchElementID
                         ) -> tuple[tuple[SketchElementID, EdgeSubPart]]:
    """Returns a tuple of (geometry_id, subpart) tuples corresponding to the 
    constraint's geometry indices and their subparts.
    
    :param sketch: A FreeCAD Sketch object.
    :param constraint_id: The (Sketch.ID, ListName, Index) of a FreeCAD 
        constraint in the sketch.
    """
    if not in_sketch(sketch, constraint_id):
        raise KeyError(f"id {constraint_id} not found in sketch {sketch.ID}")
    
    _, sketch_list, index = constraint_id
    if sketch_list not in (ListName.CONSTRAINTS, ListName.INTERNAL_ALIGNMENT):
        raise ValueError(f"id {constraint_id} is not a constraint")
    
    constraint = sketch.Constraints[index]
    constrained = [constraint.First, constraint.Second, constraint.Third]
    subparts = [constraint.FirstPos, constraint.SecondPos, constraint.ThirdPos]
    
    pairs = []
    for geometry_index, subpart in zip(constrained, subparts):
        if geometry_index == SketchNumber.UNUSED_CONSTRAINT_POSITION:
            break
        pairs.append((get_freecad_id_from_index(sketch.ID, geometry_index),
                      EdgeSubPart(subpart)))
    return tuple(pairs)

def get_constraint_type(sketch: FreeCADSketch,
                        constraint_id: SketchElementID) -> ConstraintType:
    """Returns the ConstraintType of the FreeCAD constraint."""
    if not in_sketch(sketch, constraint_id):
        raise KeyError(f"id {constraint_id} not found in sketch {sketch.ID}")
    
    _, sketch_list, index = constraint_id
    if sketch_list not in (ListName.CONSTRAINTS, ListName.INTERNAL_ALIGNMENT):
        raise ValueError(f"id {constraint_id} is not a constraint")
    return ConstraintType(sketch.Constraints[index].Type)

def get_constraint_index(freecad_id: SketchElementID) -> int:
    """Returns the index that a FreeCAD constraint would need to be defined. 
    Makes sure to use negative indices for ExternalGeo references.
    """
    _, list_name, index = freecad_id
    if list_name == ListName.EXTERNALS:
        return -index - 1
    else:
        return index

def get_freecad_id_from_index(sketch_id: int, index: int) -> SketchElementID:
    """Returns the equivalent freecad_id from a sketch id and index, assuming 
    that the index is an external geometry or normal geometry index. Does 
    not work for constraint indices!
    """
    if index < 0:
        return (sketch_id, ListName.EXTERNALS, -(index + 1))
    else:
        return (sketch_id, ListName.GEOMETRY, index)

def get_internal_constraints(sketch: FreeCADSketch,
                             id_: SketchElementID) -> list[SketchElementID]:
    """Returns the ids of the internal constraints on the geometry."""
    constraints = get_constraints_on(sketch, id_, include_internals=True)
    return [c for c in constraints if c[1] == ListName.INTERNAL_ALIGNMENT]

def get_internal_geometry(sketch: FreeCADSketch,
                          id_: SketchElementID
                          ) -> dict[InternalAlignmentType, SketchElementID]:
    """Returns a dict of the internal geometry related to the geometry_id. The 
    keys is an InternalAlignmentType that indicates how the geometry 
    supports the parent geometry.
    """
    internal_constraints = get_internal_constraints(sketch, id_)
    geometry = {}
    for sketch_id, _, index in internal_constraints:
        constraint = sketch.Constraints[index]
        content = ElementTree.fromstring(constraint.Content)
        type_ = InternalAlignmentType(
            int(content.attrib["InternalAlignmentType"])
        )
        geometry[type_] = (sketch_id, ListName.GEOMETRY, constraint.First)
    return geometry

def is_internal_geometry(sketch: FreeCADSketch, id_: SketchElementID) -> bool:
    """Returns whether a FreeCAD geometry element is internal geometry."""
    internal_constraints = get_internal_constraints(sketch, id_)
    for constraint in internal_constraints:
        pairs = get_constraint_pairs(sketch, constraint)
        if len(pairs) == 2:
            first, second = pairs
            internal_id, subpart = first
            if internal_id == id_:
                return True
    return False

def in_sketch(sketch: FreeCADSketch, id_: SketchElementID) -> bool:
    """Returns whether the SketchElementID is in the FreeCAD sketch."""
    feature_id, sketch_list, index = id_
    if feature_id != sketch.ID:
        return False
    
    match sketch_list:
        case ListName.CONSTRAINTS:
            list_ = sketch.Constraints
        case ListName.INTERNAL_ALIGNMENT:
            list_ = sketch.Constraints
        case ListName.EXTERNALS:
            list_ = sketch.ExternalGeo
        case ListName.GEOMETRY:
            list_ = sketch.Geometry
        case _:
            return False
    return 0 <= index < len(list_)