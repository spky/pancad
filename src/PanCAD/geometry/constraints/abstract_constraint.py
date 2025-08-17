"""A module providing a class defining the required properties and interfaces of 
PanCAD constraint classes.
"""

from abc import ABC, abstractmethod

from PanCAD.geometry.abstract_geometry import AbstractGeometry
from PanCAD.geometry.constants import ConstraintReference

class AbstractConstraint(ABC):
    
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