"""A module defining the properties and methods that all pancad elements 
share.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from uuid import uuid4

if TYPE_CHECKING:
    from uuid import UUID

class PancadThing(ABC):
    """An abstract class defining the properties and methods that all pancad 
    elements, constraints, or whatever must have with no exceptions.
    """
    
    STR_VERBOSE = False
    """A Flag allowing pancad objects to print more detailed strings and reprs.
    """
    
    # Getters #
    @property
    def uid(self) -> str | UUID:
        """The unique id of the element, used for CAD interoperability. Can be 
        manually set, but is usually randomly generated or read from an existing 
        file.
        """
        return self._uid
    
    # Setters #
    @uid.setter
    def uid(self, value: str | UUID | None) -> None:
        if value is None:
            self._uid = uuid4()
        else:
            self._uid = value