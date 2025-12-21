"""A module providing a class defining the required properties and interfaces of 
pancad feature classes.
"""
from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING

from pancad.geometry import PancadThing

if TYPE_CHECKING:
    from pancad.geometry import AbstractGeometry

class AbstractFeature(PancadThing):
    """A class defining the interfaces provided by pancad Feature elements."""
    # Public Methods #
    @abstractmethod
    def get_dependencies(self) -> tuple[AbstractFeature | AbstractGeometry]:
        """Returns the feature's external dependencies. Example: A 
        :class:`~pancad.geometry.Sketch` returns the sketch's coordinate 
        system and its external geometry references.
        """
    # Abstract Properties
    @property
    @abstractmethod
    def context(self) -> AbstractFeature | None:
        """Returns the feature that contains the feature. If context is None, 
        then the feature's context is the top level of the file that the feature 
        is inside of.
        """
    # Properties #
    @property
    def name(self) -> str:
        """The name of the feature. Usually user assigned or automatically 
        generated. Does not need to be unique.
        """
        if hasattr(self, "_name"):
            return self._name
        return ""
    @name.setter
    def name(self, value: str) -> str | None:
        self._name = value
