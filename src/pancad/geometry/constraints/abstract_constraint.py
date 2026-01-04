"""A module providing a class defining the required properties and interfaces of 
pancad constraint classes.
"""
from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING

from pancad.geometry import PancadThing

if TYPE_CHECKING:
    from collections.abc import Sequence

    from pancad.geometry import AbstractGeometry
    from pancad.geometry.constants import ConstraintReference

# TODO: Make it possible to initialize constraints with just subgeometry and 
# determine the parent by going up the tree.

class AbstractConstraint(PancadThing):
    """A class defining the interfaces provided by all pancad Constraint 
    Elements.
    """

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
