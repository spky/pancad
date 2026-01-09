"""A module providing a class defining the required properties and interfaces of 
pancad constraint classes.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from pancad.geometry import PancadThing

if TYPE_CHECKING:
    from collections.abc import Sequence

    from pancad.geometry.abstract_geometry import AbstractGeometry
    from pancad.geometry.abstract_feature import AbstractFeature
    from pancad.geometry.constants import ConstraintReference
    from pancad.geometry.sketch import SketchGeometrySystem


class AbstractConstraint(PancadThing):
    """A class defining the interfaces provided by all pancad Constraint 
    Elements.
    """

    # Properties
    @property
    def _geometry(self) -> list[AbstractGeometry]:
        """The geometry being constrained"""
        return self.__geometry
    @_geometry.setter
    def _geometry(self, values: Sequence[AbstractGeometry]) -> None:
        self.__geometry = list(values)

    @property
    def _pairs(self) -> list[tuple[AbstractGeometry, ConstraintReference]]:
        return self.__pairs
    @_pairs.setter
    def _pairs(self, value: list[tuple[AbstractGeometry,
                                       ConstraintReference]]) -> None:
        self.__pairs = value

    @property
    def system(self) -> SketchGeometrySystem | None:
        """The system the constraint is in. This defaults to None unless set by 
        a higher level context like a SketchGeometrySystem object.
        """
        if not hasattr(self, "_system"):
            return None
        return self._system
    @system.setter
    def system(self, value: SketchGeometrySystem) -> None:
        self._system = value

    # Public Methods
    def get_dependencies(self) -> list[AbstractFeature]:
        """Returns the features that this constraint depends on."""
        geometry_deps = [geometry.system.feature
                         for geometry in self.get_parents()]
        return list(set([self.system.feature] + geometry_deps))

    def get_parents(self) -> list[AbstractGeometry]:
        """Returns highest geometry scope being constrained for each geometry.

        Example: A circle's center point would return the circle object, but a 
        standalone point would just return the point.
        """
        parents = []
        for geometry in self._geometry:
            if geometry.parent is None:
                parents.append(geometry)
            else:
                parents.append(geometry.parent)
        return parents

    def get_geometry(self) -> list[AbstractGeometry]:
        """Returns the portions of the constrained geometry being constrained. 
        
        Examples: The x axis of a :class:`~pancad.geometry.CoordinateSystem` or 
        the start point of a :class:`~pancad.geometry.LineSegment`.
        """
        return self._geometry

    def get_references(self) -> tuple[ConstraintReference]:
        """Returns a tuple of the constrained geometrys' ConstraintReferences in 
        the same order as the tuple returned by :meth:`get_constrained`.
        """
        return tuple(geometry.self_reference for geometry in self._geometry)

    # Dunders
    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        strings = ["<", self.__class__.__name__]
        if self.STR_VERBOSE:
            strings.append(f"'{self.uid}'")
        strings.append("-")
        constrained = self.get_parents()
        references = self.get_references()
        geometry_strings = []
        for geometry, reference in zip(constrained, references):
            geometry_strings.append(
                repr(geometry).replace("<", "").replace(">", "")
            )
            geometry_strings[-1] += reference.name
        strings.append(",".join(geometry_strings))
        strings.append(">")
        return "".join(strings)
