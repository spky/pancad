"""A module providing a constraint class for coincident relations between two 
geometry elements.

"""
from __future__ import annotations

from functools import reduce

from PanCAD.geometry.constraints.abstract_constraint import AbstractConstraint
from PanCAD.geometry import (
    Point, Line, LineSegment, Plane, CoordinateSystem, Circle
)
from PanCAD.geometry.constants import ConstraintReference
from PanCAD.geometry.spatial_relations import coincident

class Coincident(AbstractConstraint):
    # Type Tuples for checking with isinstance()
    CONSTRAINED_TYPES = (Point, Line, LineSegment,
                         Plane, CoordinateSystem, Circle)
    GEOMETRY_TYPES = (Point, Line, LineSegment, Plane, Circle)
    
    # Type Hints
    ConstrainedType = reduce(lambda x, y: x | y, CONSTRAINED_TYPES)
    GeometryType = reduce(lambda x, y: x | y, GEOMETRY_TYPES)
    
    def __init__(self,
                 constrain_a: ConstrainedType, reference_a: ConstraintReference,
                 constrain_b: ConstrainedType, reference_b: ConstraintReference,
                 uid: str=None):
        self.uid = uid
        
        if len(constrain_a) == len(constrain_b):
            self._a = constrain_a
            self._a_reference = reference_a
            self._b = constrain_b
            self._b_reference = reference_b
        else:
            raise ValueError("Geometry a and b must have the same number"
                             " of dimensions")
        
        self._validate_constrained()
        self._validate_geometry()
    
    # Public Methods
    def get_constrained(self) -> tuple[ConstrainedType]:
        """Returns a tuple of the constrained geometry elements"""
        return (self._a, self._b)
    
    def get_geometry(self) -> tuple[GeometryType]:
        """Returns a tuple of the specific geometry elements inside of the 
        constrained elements"""
        return (self._a.get_reference(self._a_reference),
                self._b.get_reference(self._b_reference))
    
    def get_references(self) -> tuple[ConstraintReference]:
        """Returns a tuple of the constrained geometry's references to the 
        specific geometry inside the constrained element"""
        return (self._a_reference, self._b_reference)
    
    # Private Methods #
    def _validate_constrained(self):
        """Raises an error if the geometries are not one of the allowed 
        types"""
        if not any([isinstance(g, self.CONSTRAINED_TYPES)
                    for g in self.get_geometry()]):
            raise ValueError(
                f"geometry a and b must be one of:\n{self.CONSTRAINED_TYPES}\n"
                f"Given: {self._a.__class__} and {self._b.__class__}"
            )
        elif self._a is self._b:
            raise ValueError("Constrained a/b cannot be the same geometry"
                             " element")
    
    def _validate_geometry(self):
        """Raises an error if the constrainted geometries are not one of the 
        allowed types"""
        if not any([isinstance(g, self.GEOMETRY_TYPES)
                    for g in self.get_geometry()]):
            classes = [g.__class__ for g in self.get_geometry()]
            raise ValueError(
                f"geometry a and b must be one of:\n{self.GEOMETRY_TYPES}\n"
                f"Given: {classes}"
            )
    
    # Python Dunders #
    def __eq__(self, other: Coincident) -> bool:
        """Checks whether two coincident relations are functionally the same by 
        comparing the memory ids of their geometries.
        
        :param other: Another coincident relationship.
        :returns: Whether the relations are the same.
        """
        geometry_zip = zip(self.get_geometry(), other.get_geometry())
        if isinstance(other, Coincident):
            return all([g is other_g for g, other_g in geometry_zip])
        else:
            return NotImplemented
    
    def __repr__(self) -> str:
        """Returns the short string representation of the Coincident"""
        return f"<Coincident'{self.uid}'{repr(self._a)}{repr(self._b)}>"
    
    def __str__(self) -> str:
        """Returns the longer string representation of the Coincident"""
        return (
            f"PanCAD Coincident Constraint '{self.uid}' with {repr(self._a)}"
            f" as geometry a and {repr(self._b)} as geometry b"
        )