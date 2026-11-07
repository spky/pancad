"""
solver_schemas.py contains CalculationSchema specification dictionaries that map
ResidualCalculation types to constraint type, geometry combination, and value name combinations.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from pancad.utils.residual_calculations import CoincidentLinePoint2D, EqualVectorComponents2D
from pancad.constraints.state_constraint import Coincident
from pancad.geometry.point import Point
from pancad.geometry.line import Axis, Line

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping
    from typing import Type

    from pancad.abstract import AbstractGeometry, PancadThing
    from pancad.utils.residual_calculations import ResidualCalculation

    # 'Mixed' means an iterable consisting of types and an iterable of the types.
    # Mixed of PancadThing types and iterables of PancadThing types. Indicates applicability.
    MixedThing = Type[PancadThing] | Iterable[Type[PancadThing]]
    MixedGeo = Type[AbstractGeometry] | Iterable[Type[AbstractGeometry]]
    MixedStr = str | Iterable[str]

    # A cartesian product expression of geometry types. Used to specify GeoCombos succinctly.
    GeoComboSpec = Type[AbstractGeometry] | Iterable[MixedGeo]

    # A specification for a mapping from geometry types to an iterable of value names.
    ValueMapSpec = Mapping[MixedGeo, MixedStr]

SCHEMAS: Mapping[str, Mapping[Type[ResidualCalculation],
                                   Mapping[MixedThing, Mapping[GeoComboSpec, ValueMapSpec]]]] = {
    "pancad_default": {
        CoincidentLinePoint2D: {
            Coincident: {
                (Point, (Line, Axis)): {
                    Point: "cartesian",
                    (Line, Axis): ("ref", "direction"),
                },
            }
        },
        EqualVectorComponents2D: {
            Coincident: {Point: {Point: "cartesian"}},
        },
    }
}
