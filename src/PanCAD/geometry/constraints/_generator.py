"""A module providing functions to generate PanCAD constraints without calling
each constraint class individually.
"""
from numbers import Real
from typing import overload
from uuid import UUID

from .. import AbstractGeometry
from ..constants import ConstraintReference, SketchConstraint
from . import (
    AbstractConstraint,
    AbstractStateConstraint,
    AbstractSnapTo,
    AbstractValue,
    Abstract1GeometryDistance,
    Abstract2GeometryDistance,
    AbstractDistance2D,
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

@overload
def make_constraint(self,
                    constraint_type: SketchConstraint,
                    a: AbstractGeometry,
                    reference_a: ConstraintReference,
                    b: AbstractGeometry | None=None,
                    reference_b: ConstraintReference | None=None,
                    *,
                    uid: UUID | str=None) -> AbstractSnapTo: ...

@overload
def make_constraint(self,
                    constraint_type: SketchConstraint,
                    a: AbstractGeometry,
                    reference_a: ConstraintReference,
                    b: AbstractGeometry,
                    reference_b: ConstraintReference,
                    *,
                    uid: UUID | str=None) -> AbstractStateConstraint: ...

@overload
def make_constraint(self,
                    constraint_type: SketchConstraint,
                    a: AbstractGeometry,
                    reference_a: ConstraintReference,
                    *,
                    value: Real,
                    unit: str | None=None,
                    uid: UUID | str=None) -> Abstract1GeometryDistance: ...

@overload
def make_constraint(self,
                    constraint_type: SketchConstraint,
                    a: AbstractGeometry,
                    reference_a: ConstraintReference,
                    b: AbstractGeometry,
                    reference_b: ConstraintReference,
                    *,
                    value: Real,
                    unit: str | None=None,
                    uid: UUID | str=None) -> Abstract2GeometryDistance: ...

@overload
def make_constraint(self,
                    constraint_type: SketchConstraint,
                    a: AbstractGeometry,
                    reference_a: ConstraintReference,
                    b: AbstractGeometry,
                    reference_b: ConstraintReference,
                    *,
                    value: Real,
                    uid: UUID | str=None,
                    quadrant: int,
                    is_radians: bool=False) -> Angle: ...

def make_constraint(constraint_type,
                    a,
                    reference_a,
                    b=None,
                    reference_b=None,
                    c=None,
                    reference_c=None,
                    *,
                    value=None,
                    uid=None,
                    unit=None,
                    quadrant=None,
                    is_radians=False,
                    ) -> AbstractConstraint:
    """Creates a new PanCAD constraint.
    
    :param constraint_type: The SketchConstraint value for the constraint to be 
        created.
    :param a: First constraint geometry.
    :param reference_a: A ConstraintReference for a portion of a.
    :param b: Second constraint geometry. Only required for constraints 
        that require at least 2 geometry elements (e.g. coincident, parallel).
    :param reference_b: A ConstraintReference for a portion of b. Required if 
        b is provided.
    :param c: Third constraint geometry. Only required for constraints 
        requiring 3 geometry elements (i.e. symmetry).
    :param reference_c: A ConstraintReference for a portion of c. Required if 
        index_c is provided.
    :param value: The constraint's associate value. Can be a length or an angle 
        and is required for value constraints.
    :param uid: The constraint's uid. Defaults to being auto-generated.
    :param 
    """
    match constraint_type:
        case SketchConstraint.ANGLE:
            constraint = Angle(a, reference_a,
                               b, reference_b,
                               uid=uid,
                               value=value,
                               quadrant=quadrant,
                               is_radians=is_radians)
        case SketchConstraint.COINCIDENT:
            constraint = Coincident(a, reference_a, b, reference_b)
        case SketchConstraint.HORIZONTAL:
            constraint = Horizontal(a, reference_a, b, reference_b)
        case SketchConstraint.DISTANCE:
            constraint = Distance(a, reference_a,
                                  b, reference_b,
                                  uid=uid,
                                  value=value,
                                  unit=unit)
        case SketchConstraint.DISTANCE_DIAMETER:
            constraint = Diameter(a, reference_a,
                                  uid=uid,
                                  value=value,
                                  unit=unit)
        case SketchConstraint.DISTANCE_HORIZONTAL:
            constraint = HorizontalDistance(a, reference_a,
                                            b, reference_b,
                                            uid=uid,
                                            value=value,
                                            unit=unit)
        case SketchConstraint.DISTANCE_RADIUS:
            constraint = Radius(a, reference_a,
                                uid=uid,
                                value=value,
                                unit=unit)
        case SketchConstraint.DISTANCE_VERTICAL:
            constraint = VerticalDistance(a, reference_a,
                                          b, reference_b,
                                          uid=uid,
                                          value=value,
                                          unit=unit)
        case SketchConstraint.EQUAL:
            constraint = Equal(a, reference_a, b, reference_b)
        case SketchConstraint.PARALLEL:
            constraint = Parallel(a, reference_a, b, reference_b)
        case SketchConstraint.PERPENDICULAR:
            constraint = Perpendicular(a, reference_a, b, reference_b)
        case SketchConstraint.SYMMETRIC:
            raise NotImplementedError("Symmetric not yet implemented, #85")
        case SketchConstraint.TANGENT:
            raise NotImplementedError("Tangent not yet implemented, #82")
        case SketchConstraint.VERTICAL:
            constraint = Vertical(a, reference_a, b, reference_b)
        case _:
            raise ValueError(f"Constraint choice {constraint_type}"
                             " not recognized")
    return constraint