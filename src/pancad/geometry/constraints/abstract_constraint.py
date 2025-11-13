"""A module providing a class defining the required properties and interfaces of 
pancad constraint classes.
"""
from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING

from pancad.geometry import PancadThing

if TYPE_CHECKING:
    from pancad.geometry import AbstractGeometry, AbstractFeature
    from pancad.geometry.constants import ConstraintReference
    
class AbstractConstraint(PancadThing):
    """A class defining the interfaces provided by all pancad Constraint 
    Elements.
    """
    
    @property
    def context(self) -> AbstractFeature:
        """The feature containing the constraint, usually
        a :class:`~pancad.geometry.Sketch`.
        
        :getter: Returns the feature containing the constraint.
        :setter: Sets the feature containing the constraint, should only be set 
            by a method inside the containing feature.
        :raises AttributeError: Raised when the context getter is called when
            the context has not been set.
        """
        return self._context
    
    @context.setter
    def context(self, feature: AbstractFeature) -> None:
        self._context = feature
    
    # Abstract Properties #
    @property
    @abstractmethod
    def ConstrainedType(self) -> tuple[AbstractGeometry]:
        """The types of geometry constrainable by this constraint."""
    
    @property
    @abstractmethod
    def GeometryType(self) -> tuple[AbstractGeometry]:
        """Types of geometry portions that can be constrained by this 
        constraint. Geometry portions refer to the subgeometry inside of a 
        ConstrainedType geometry that can be referred to using a 
        :class:`~pancad.geometry.constants.ConstraintReference`.
        
        Examples: The x axis of a :class:`~pancad.geometry.CoordinateSystem` or 
        the start point of a :class:`~pancad.geometry.LineSegment`.
        """
    
    # Abstract Public Methods #
    @abstractmethod
    def get_constrained(self) -> tuple[AbstractGeometry]:
        """Returns the geometry or geometries being constrained."""
    
    @abstractmethod
    def get_geometry(self) -> tuple[AbstractGeometry]:
        """Returns the portions of the constrained geometry being constrained. 
        
        Examples: The x axis of a :class:`~pancad.geometry.CoordinateSystem` or 
        the start point of a :class:`~pancad.geometry.LineSegment`.
        """
    
    @abstractmethod
    def get_references(self) -> tuple[ConstraintReference]:
        """Returns a tuple of the constrained geometrys' ConstraintReferences in 
        the same order as the tuple returned by :meth:`get_constrained`.
        """
    
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