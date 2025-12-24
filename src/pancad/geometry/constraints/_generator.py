"""A module providing functions to generate pancad constraints without calling
each constraint class individually.
"""
from __future__ import annotations

from typing import overload, TYPE_CHECKING

from pancad.geometry.constants import SketchConstraint

from . import (
    AbstractConstraint,
    AbstractStateConstraint,
    AbstractDistance,
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
from pancad.utils.constraints import GeometryReference

if TYPE_CHECKING:
    from uuid import UUID
    from numbers import Real
    from pancad.geometry import AbstractGeometry
    from pancad.geometry.constants import ConstraintReference

SKETCH_CONSTRAINT_TO_CLASS = {
    SketchConstraint.ANGLE: Angle,
    SketchConstraint.COINCIDENT: Coincident,
    SketchConstraint.HORIZONTAL: Horizontal,
    SketchConstraint.DISTANCE: Distance,
    SketchConstraint.DISTANCE_DIAMETER: Diameter,
    SketchConstraint.DISTANCE_RADIUS: Radius,
    SketchConstraint.DISTANCE_HORIZONTAL: HorizontalDistance,
    SketchConstraint.DISTANCE_VERTICAL: VerticalDistance,
    SketchConstraint.EQUAL: Equal,
    SketchConstraint.PARALLEL: Parallel,
    SketchConstraint.PERPENDICULAR: Perpendicular,
    SketchConstraint.VERTICAL: Vertical,
}

@overload
def make_constraint(type_: SketchConstraint,
                    *reference_pairs: GeometryReference,
                    uid: UUID | str=None) -> AbstractStateConstraint: ...

@overload
def make_constraint(type_: SketchConstraint,
                    *reference_pairs: GeometryReference,
                    value: Real,
                    unit: str | None=None,
                    uid: UUID | str=None) -> AbstractDistance: ...

@overload
def make_constraint(type_: SketchConstraint,
                    *reference_pairs: GeometryReference,
                    value: Real,
                    uid: UUID | str=None,
                    quadrant: int,
                    is_radians: bool=False) -> Angle: ...

def make_constraint(type_, *reference_pairs, **kwargs) -> AbstractConstraint:
    """Creates a new pancad constraint.
    
    :param type_: The SketchConstraint value for the constraint to be created.
    :param reference_pairs: The (AbstractGeometry, ConstraintReference) pairs of 
        the geometry to be constrained.
    :param value: The constraint's associate value. Can be a length or an angle 
        and is required for value constraints.
    :param uid: The constraint's uid. Defaults to being auto-generated.
    :param unit: The unit used for the constraint. Defaults to None.
    :param quadrant: The quadrant an angle constraint should appear in. Defaults 
        to None but must be given for angle constraints.
    :param is_radians: Whether the value provided for an angle constraint is 
        provided in radians. Defaults to False.
    :returns: The new pancad constraint.
    :raises ValueError: Raised if the SketchConstraint is not recognized.
    :raises NotImplementedError: Raised if a SketchConstraint for a constraint 
        that is not yet implemented is provided.
    """
    try:
        class_ = SKETCH_CONSTRAINT_TO_CLASS[type_]
    except KeyError as err:
        if type_ in [SketchConstraint.SYMMETRIC, SketchConstraint.TANGENT]:
            raise NotImplementedError("See issue #82 or #85") from err
        raise KeyError from err
    return class_(*reference_pairs, **kwargs)
