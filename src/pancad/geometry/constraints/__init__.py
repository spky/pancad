"""A module containing geometry constraint classes and functions to make them."""
from .abstract_constraint import AbstractConstraint

from .state_constraint import (
    AbstractStateConstraint,
    Coincident,
    Equal,
    Parallel,
    Perpendicular,
    Tangent,
)
from .snapto import (
    AbstractSnapTo,
    Horizontal,
    Vertical,
)

from .distance import (
    AbstractValue,
    AbstractDistance,
    Abstract1GeometryDistance,
    Abstract2GeometryDistance,
    AbstractDistance2D,
    Angle,
    Diameter,
    Distance,
    HorizontalDistance,
    Radius,
    VerticalDistance,
)

from ._generator import make_constraint
