"""A module providing a class defining the required properties and interfaces of 
PanCAD feature classes.
"""
from __future__ import annotations

from abc import abstractmethod

from PanCAD.geometry import PanCADThing, AbstractGeometry
from PanCAD.geometry.constants import ConstraintReference

class AbstractFeature(PanCADThing):
    
    # Public Methods #
    @abstractmethod
    def get_dependencies(self) -> tuple[AbstractFeature | AbstractGeometry]:
        """Returns the feature's external dependencies. Example: A 
        :class:`~PanCAD.geometry.Sketch` returns the sketch's coordinate 
        system and its external geometry references.
        """
    
    # Abstract Properties
    @property
    @abstractmethod
    def context(self) -> AbstractFeature | None:
        """Returns the feature that contains the feature. If context is None, 
        then the feature's context is the file that the feature is in.
        """
    
    # Getters #
    @property
    def name(self) -> str:
        """The name of the feature. Usually user assigned or automatically 
        generated.
        """
        if hasattr(self, "_name"):
            return self._name
        else:
            return None
    
    # Setters #
    @name.setter
    def name(self, value: str) -> str | None:
        self._name = value