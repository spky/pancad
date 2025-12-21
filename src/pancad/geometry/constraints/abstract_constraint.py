"""A module providing a class defining the required properties and interfaces of 
pancad constraint classes.
"""
from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING

from pancad.geometry import PancadThing

if TYPE_CHECKING:
    from pancad.geometry import AbstractGeometry
    from pancad.geometry.constants import ConstraintReference

class AbstractConstraint(PancadThing):
    """A class defining the interfaces provided by all pancad Constraint 
    Elements.
    """
    @property
    def _pairs(self) -> list[tuple[AbstractGeometry, ConstraintReference]]:
        return self.__pairs
    @_pairs.setter
    def _pairs(self, value: list[tuple[AbstractGeometry,
                                       ConstraintReference]]) -> None:
        self.__pairs = value
    def get_constrained(self) -> tuple[AbstractGeometry]:
        """Returns the geometry or geometries being constrained."""
        return tuple(geometry for geometry, _ in self._pairs)
    def get_geometry(self) -> tuple[AbstractGeometry]:
        """Returns the portions of the constrained geometry being constrained. 
        
        Examples: The x axis of a :class:`~pancad.geometry.CoordinateSystem` or 
        the start point of a :class:`~pancad.geometry.LineSegment`.
        """
        return tuple(geometry.get_reference(reference)
                     for geometry, reference in self._pairs)
    def get_references(self) -> tuple[ConstraintReference]:
        """Returns a tuple of the constrained geometrys' ConstraintReferences in 
        the same order as the tuple returned by :meth:`get_constrained`.
        """
        return tuple(reference for _, reference in self._pairs)
    @abstractmethod
    def _validate(self) -> None:
        """Checks whether the constraint is badly formed."""
    def __repr__(self) -> str:
        return str(self)
    def __str__(self) -> str:
        strings = ["<", self.__class__.__name__]
        if self.STR_VERBOSE:
            strings.append(f"'{self.uid}'")
        strings.append("-")
        constrained = self.get_constrained()
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
