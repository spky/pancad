"""A module providing functions to generate pancad constraints without calling each constraint
class individually.
"""
from __future__ import annotations

from typing import overload, TYPE_CHECKING

from pancad.constants import SketchConstraint
from pancad.constraints.distance import (
    Angle, Diameter, Distance, HorizontalDistance, Radius, VerticalDistance
)
from pancad.constraints.snapto import Horizontal, Vertical, Fixed, Unique
from pancad.constraints.state_constraint import (
    Coincident, Equal, Parallel, Perpendicular, AlignAxes, Antiparallel, Codirectional
)

if TYPE_CHECKING:
    from typing import Type, NoReturn
    from uuid import UUID

    from pancad.abstract import AbstractGeometry, AbstractConstraint, AbstractGeometrySystem
    from pancad.constraints.distance import AbstractDistance
    from pancad.constraints.state_constraint import AbstractStateConstraint
    from pancad.constraints.snapto import AbstractSnapTo, AbstractSingleSnapTo

    NonValueConstraint = AbstractStateConstraint | AbstractSnapTo | AbstractSingleSnapTo

_DISTANCE_MAP: dict[SketchConstraint, Type[AbstractDistance]] = {
    SketchConstraint.DISTANCE: Distance,
    SketchConstraint.DISTANCE_DIAMETER: Diameter,
    SketchConstraint.DISTANCE_RADIUS: Radius,
    SketchConstraint.DISTANCE_HORIZONTAL: HorizontalDistance,
    SketchConstraint.DISTANCE_VERTICAL: VerticalDistance,
}

_NON_VALUE_CONSTRAINT_MAP: dict[SketchConstraint, Type[NonValueConstraint]] = {
    SketchConstraint.ALIGN_AXES: AlignAxes,
    SketchConstraint.ANTIPARALLEL: Antiparallel,
    SketchConstraint.CODIRECTIONAL: Codirectional,
    SketchConstraint.COINCIDENT: Coincident,
    SketchConstraint.HORIZONTAL: Horizontal,
    SketchConstraint.EQUAL: Equal,
    SketchConstraint.FIXED: Fixed,
    SketchConstraint.PARALLEL: Parallel,
    SketchConstraint.PERPENDICULAR: Perpendicular,
    SketchConstraint.UNIQUE: Unique,
    SketchConstraint.VERTICAL: Vertical,
}

# Non Value Constraint Overloads
@overload
def make_constraint(type_: SketchConstraint | str,
                    *geometry: AbstractGeometry,
                    system: AbstractGeometrySystem | None=None,
                    uid: UUID | str | None=None,
                    value: None=None,
                    unit: None=None,
                    is_radians: None=None,
                    quadrant: None=None) -> NonValueConstraint: ...
@overload
def make_constraint(type_: SketchConstraint | str,
                    *geometry: AbstractGeometry,
                    value: float,
                    unit: str | None=None,
                    system: AbstractGeometrySystem | None=None,
                    uid: UUID | str | None=None,
                    quadrant: None=None,
                    is_radians: None=None) -> AbstractDistance: ...
@overload
def make_constraint(type_: SketchConstraint | str,
                    *geometry: AbstractGeometry,
                    value: float,
                    quadrant: int,
                    is_radians: bool | None=None,
                    system: AbstractGeometrySystem | None=None,
                    uid: UUID | str | None=None,
                    unit: None=None) -> Angle: ...

def make_constraint(type_: SketchConstraint | str,
                    *geometry: AbstractGeometry,
                    uid: UUID | str | None=None,
                    value: float | None=None,
                    unit: str | None=None,
                    quadrant: int | None=None,
                    is_radians: bool | None=None,
                    system: AbstractGeometrySystem | None=None) -> AbstractConstraint:
    """Creates a new pancad constraint.

    :param type_: The SketchConstraint enumeration value for the constraint to be created.
    :param geometry: The geometry elements to be constrained.
    :param uid: The constraint's uid. Is auto-generated when None is provided.
    :param value: The constraint's associated value. Can be a length or an angle and is required
        for value constraints.
    :param unit: The unit used for the constraint. Defaults to None.
    :param quadrant: The quadrant an angle constraint should appear in. Defaults to None but must
        be given for angle constraints.
    :param is_radians: Whether the value of an angle constraint is provided in radians.
    :param system: The geometry system context for the constraint.
    :returns: The new pancad constraint.
    :raises ValueError: When a necessary argument for the constraint type has not been provided.
        Arguments that are not required for the constraint are ignored.
    """
    type_ = SketchConstraint(str(type_).lower())
    kwargs = {"value": value, "unit": unit, "quadrant": quadrant, "is_radians": is_radians}
    if type_ in _DISTANCE_MAP:
        # Creating a Distance constraint.
        if value is None: # Both Distances and Angles need value.
            _raise_missing(type_, {"value"}, dict(kwargs))
        return _DISTANCE_MAP[type_](*geometry, value=value, uid=uid, unit=unit, system=system)
    if type_ == SketchConstraint.ANGLE:
        # Creating an Angle constraint
        if quadrant is None or value is None:
            _raise_missing(type_, {"value", "quadrant"}, dict(kwargs))
        if is_radians is None:
            return Angle(*geometry, value=value, quadrant=quadrant, uid=uid, system=system)
        return Angle(*geometry, value=value, quadrant=quadrant, is_radians=is_radians,
                     uid=uid, system=system)
    try:
        non_value_constraint_type = _NON_VALUE_CONSTRAINT_MAP[type_]
    except KeyError as exc:
        if type_ in {SketchConstraint.SYMMETRIC, SketchConstraint.TANGENT}:
            raise NotImplementedError("See issue #82 or #85") from exc
        raise NotImplementedError(f"Unsupported SketchConstraint type: {type_}") from exc
    return non_value_constraint_type(*geometry, uid=uid, system=system)

def _raise_missing(type_: SketchConstraint, must_have: set[str],
                   kwargs: dict[str, object]) -> NoReturn:
    # Raises a ValueError describing each missing argument for the constraint type.
    missing = ", ".join([k for k, v in kwargs.items() if k in must_have and v is None])
    assert missing != "" # Ensure that this function wasn't called accidentally
    raise ValueError(f"'{missing}' was not provided and is required for {type_} constraints")
