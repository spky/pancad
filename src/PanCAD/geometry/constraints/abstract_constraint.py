"""A module providing a class defining the required properties and interfaces of 
PanCAD constraint classes.
"""

from abc import ABC, abstractmethod

from PanCAD.geometry.abstract_geometry import AbstractGeometry
from PanCAD.geometry.constants import ConstraintReference

class AbstractConstraint(ABC):
    
    # Properties #
    
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
        :class:`~PanCAD.geometry.constants.ConstraintReference`.
        
        Examples: The x axis of a :class:`~PanCAD.geometry.CoordinateSystem` or 
        the start point of a :class:`~PanCAD.geometry.LineSegment`.
        """
    
    # Public Methods #
    @abstractmethod
    def get_constrained(self) -> tuple[AbstractGeometry]:
        """Returns the geometry or geometries being constrained."""
    
    @abstractmethod
    def get_geometry(self) -> tuple[AbstractGeometry]:
        """Returns the portions of the constrained geometry being constrained. 
        
        Examples: The x axis of a :class:`~PanCAD.geometry.CoordinateSystem` or 
        the start point of a :class:`~PanCAD.geometry.LineSegment`.
        """
    
    @abstractmethod
    def get_references(self) -> tuple[ConstraintReference]:
        """Returns a tuple of the constrained geometrys' ConstraintReferences in 
        the same order as the tuple returned by :meth:`get_constrained`.
        """