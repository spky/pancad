"""A module providing functions to query common FreeCAD information using its 
Python API.
"""
from __future__ import annotations

from typing import TYPE_CHECKING
from .constants import ListName

if TYPE_CHECKING:
    from ._application_types import FreeCADSketch
    from ._map_typing import SketchElementID
    from .constants import EdgeSubPart

def get_constraints_on(sketch: FreeCADSketch,
                       geometry_id: SketchElementID,
                       subpart: EdgeSubPart=None) -> list[SketchElementID]:
    """Returns the ids of the constraints on the geometry.
    
    :param sketch: A FreeCAD Sketch object.
    :param geometry_id: The (Sketch.ID, ListName, Index) of a FreeCAD geometry 
        element in the sketch.
    :param subpart: The constrained subpart of the geometry to filter by.
    :returns: The list of constraint ids of constraints on the geometry. Returns 
        only  the constraints referencing the subpart if subpart is provided.
    """
    feature_id, list_type, _ = geometry_id
    
    # Check whether geometry_id is geometry and in the sketch
    if feature_id != sketch.ID:
        raise KeyError(f"id {geometry_id} not found"
                       f" in sketch with id {sketch.ID}")
    if list_type not in [ListName.GEOMETRY, ListName.EXTERNALS]:
        raise ValueError(f"geometry_id {geometry_id} is for {list_type},"
                         f" not {ListName.GEOMETRY} or {ListName.EXTERNALS}")
    # Ensure that external references are negative
    geometry_index = get_constraint_index(geometry_id)
    
    # Find relevant constraints in sketch
    constraints = []
    id_prefix = (sketch.ID, ListName.CONSTRAINTS)
    for i, constraint in enumerate(sketch.Constraints):
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

def get_constraint_index(freecad_id: SketchElementID) -> int:
    """Returns the index that a FreeCAD constraint would need to be defined. 
    Makes sure to use negative indices for ExternalGeo references.
    """
    _, list_name, index = freecad_id
    if list_name == ListName.EXTERNALS:
        return -index - 1
    else:
        return index