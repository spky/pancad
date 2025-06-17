"""A module providing a constraint class for coincident relations between two 
geometry elements.

"""
from __future__ import annotations

from functools import reduce

from PanCAD.geometry import Point, Line, LineSegment, Plane, CoordinateSystem
from PanCAD.geometry.constants import ConstraintReference
from PanCAD.geometry.spatial_relations import coincident

class Coincident:
    # Type Tuples for checking with isinstance()
    GEOMETRY_TYPES = (Point, Line, LineSegment, Plane, CoordinateSystem)
    REFERENCE_TYPES = (Point, Line, LineSegment, Plane)
    
    # Type Hints
    GeometryType = reduce(lambda x, y: x | y, GEOMETRY_TYPES)
    ReferenceType = reduce(lambda x, y: x | y, REFERENCE_TYPES)
    
    def __init__(self,
                 geometry_a: GeometryType,
                 reference_a: ConstraintReference,
                 geometry_b: GeometryType,
                 reference_b: ConstraintReference,
                 uid: str=None):
        self.uid = uid
        
        
        if len(geometry_a) == len(geometry_b):
            self._a = geometry_a
            self._a_reference = reference_a
            self._b = geometry_b
            self._b_reference = reference_b
        else:
            raise ValueError("Geometry a and b must have the same number"
                             " of dimensions")
        
        self._validate_constrained_geometry()
    
    # Public Methods
    def check(self) -> bool:
        """Returns whether the constraint is met by the geometry."""
        return coincident(self.get_a_constrained(), self.get_b_constrained())
    
    def get_a(self) -> GeometryType:
        """Returns geometry a."""
        return self._a
    
    def get_a_reference(self) -> ConstraintReference:
        """Returns the ConstraintReference of geometry a."""
        return self._a_reference
    
    def get_a_constrained(self) -> GeometryType:
        """Returns the constrained reference geometry of geometry a."""
        return self._a.get_reference(self._a_reference)
    
    def get_b(self) -> GeometryType:
        """Returns geometry a"""
        return self._b
    
    def get_b_reference(self) -> ConstraintReference:
        """Returns the ConstraintReference of geometry b."""
        return self._b_reference
    
    def get_b_constrained(self) -> GeometryType:
        """Returns the constrained reference geometry of geometry b."""
        return self._b.get_reference(self._b_reference)
    
    def get_constrained(self) -> tuple[GeometryType]:
        """Returns a tuple of the constrained geometries"""
        return (self.get_a(), self.get_b())
    
    # Private Methods #
    def _validate_parent_geometry(self):
        """Raises an error if the geometries are not one of the allowed 
        types"""
        a = self.get_a()
        b = self.get_b()
        if (not isinstance(a, self.GEOMETRY_TYPES)
                or not isinstance(b, self.GEOMETRY_TYPES)):
            raise ValueError(
                f"geometry a and b must be one of:\n{self.GEOMETRY_TYPES}\n"
                f"Given: {a.__class__} and {b.__class__}"
            )
        elif a is b:
            raise ValueError("geometry a/b cannot be the same geometry element")
    
    def _validate_constrained_geometry(self):
        """Raises an error if the constrainted geometries are not one of the 
        allowed types"""
        a_constrain = self.get_a_constrained()
        b_constrain = self.get_b_constrained()
        if (not isinstance(a_constrain, self.REFERENCE_TYPES)
                or not isinstance(a_constrain, self.REFERENCE_TYPES)):
            raise ValueError(
                f"geometry a and b must be one of:\n{self.REFERENCE_TYPES}\n"
                f"Given: {a_constrain.__class__} and {b_constrain.__class__}"
            )
    
    # Python Dunders #
    def __eq__(self, other: Coincident) -> bool:
        """Checks whether two coincident relations are functionally the same by 
        comparing the memory ids of their geometries.
        
        :param other: Another coincident relationship.
        :returns: Whether the relations are the same.
        """
        if isinstance(other, Coincident):
            return (
                self.get_a_constrained() is other.get_a_constrained()
                and self.get_b_constrained() is other.get_b_constrained()
            )
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
    