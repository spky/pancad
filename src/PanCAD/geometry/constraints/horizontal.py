"""A module providing a constraint class for Horizontal constraints in 2D 
geometry contexts. Horizontal can be used to force a Line/LineSegment to be held 
Horizontal (parallel to x-axis in 2D) or it can be used to force 2 points to be 
collinear with a theoretical Horizontal line.
"""

from __future__ import annotations

from functools import reduce

from PanCAD.geometry import Point, Line, LineSegment, CoordinateSystem
from PanCAD.geometry.constants import ConstraintReference

class Horizontal:
    # Type Tuples for checking with isinstance()
    GEOMETRY_TYPES = (Point, Line, LineSegment, CoordinateSystem)
    ONE_GEOMETRY_TYPES = (Line, LineSegment)
    TWO_GEOMETRY_TYPES = (Point,)
    REFERENCE_TYPES = ONE_GEOMETRY_TYPES + TWO_GEOMETRY_TYPES
    
    # Type Hints
    GeometryType = reduce(lambda x, y: x | y, GEOMETRY_TYPES)
    OneGeometryType = reduce(lambda x, y: x | y, ONE_GEOMETRY_TYPES)
    TwoGeometryType = TWO_GEOMETRY_TYPES
    ReferenceType = reduce(lambda x, y: x | y, REFERENCE_TYPES)
    
    def __init__(self,
                 geometry_a: GeometryType,
                 reference_a: ConstraintReference,
                 geometry_b: GeometryType=None,
                 reference_b: ConstraintReference=None,
                 uid: str=None):
        self.uid = uid
        if geometry_b is None:
            # One geometry case (e.g. Line or LineSegment)
            self._a = geometry_a
            self._a_reference = reference_a
            self._b = None
            self._b_reference = None
        elif len(geometry_a) == len(geometry_b):
            # Two geometry case (e.g. Point to Point)
            self._a = geometry_a
            self._a_reference = reference_a
            self._b = geometry_b
            self._b_reference = reference_b
        else:
            raise ValueError("Geometry a and b must have the same number"
                             " of dimensions")
        self._validate_parent_geometry()
        self._validate_constrained_geometry()
    
    # Private Methods #
    def _validate_parent_geometry(self):
        """Raises an error if the geometries are not one of the allowed 
        types"""
        a = self.get_a()
        b = self.get_b()
        if b is None:
            if not isinstance(a, self.GEOMETRY_TYPES):
                raise ValueError(
                    f"geometry a must be one of:\n{self.GEOMETRY_TYPES}\n"
                    f"Given: {a.__class__}"
                )
        elif (not isinstance(a, self.GEOMETRY_TYPES)
                or not isinstance(b, self.GEOMETRY_TYPES)):
            raise ValueError(
                f"geometry a and b must be one of:\n{self.GEOMETRY_TYPES}\n"
                f"Given: {a.__class__} and {b.__class__}"
            )
        elif len(a) == 3 or len(b) == 3:
            raise ValueError("geometry must be 2D to be constrained Horizontal")
        elif a is b:
            raise ValueError("geometry a/b cannot be the same geometry element")
    
    def _validate_constrained_geometry(self) -> None:
        """Raises an error if the constrainted geometries are not one of the 
        allowed types"""
        a_constrain = self.get_a_constrained()
        b_constrain = self.get_b_constrained()
        if b_constrain is None:
            if not isinstance(a_constrain, self.ONE_GEOMETRY_TYPES):
                raise ValueError(
                    "A single geometry Horizontal relation can only constrain:"
                    f"\n{self.ONE_GEOMETRY_TYPES}\nGiven: {a_constrain}"
                )
        else:
            b_constrain = self.get_b_constrained()
            if (not isinstance(a_constrain, self.TWO_GEOMETRY_TYPES)
                    or not isinstance(b_constrain, self.TWO_GEOMETRY_TYPES)):
                raise ValueError(
                    "A two geometry Horizontal relation can only constrain:"
                    f"\n{self.TWO_GEOMETRY_TYPES}\nGiven:"
                    f" {a_constrain.__class__} and {b_constrain.__class__}"
                )
    
    # Public Methods
    def check(self) -> bool:
        """Returns whether the constraint is met by the geometry."""
        raise NotImplementedError("Horizontal check not implemented yet")
    
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
        if self._b is None:
            return None
        else:
            return self._b.get_reference(self._b_reference)
    
    def get_constrained(self) -> tuple[GeometryType]:
        """Returns a tuple of the constrained geometries"""
        if self.get_b() is None:
            return (self.get_a(),)
        else:
            return (self.get_a(), self.get_b())
    
    # Python Dunders #
    def __eq__(self, other: Horizontal) -> bool:
        """Checks whether two Horizontal relations are functionally the same by 
        comparing the memory ids of their constrained geometries.
        
        :param other: Another Horizontal relationship.
        :returns: Whether the relations are the same.
        """
        if isinstance(other, Horizontal):
            return (
                self.get_a_constrained() is other.get_a_constrained()
                and self.get_b_constrained() is other.get_b_constrained()
            )
        else:
            return NotImplemented
    
    def __repr__(self) -> str:
        """Returns the short string representation of the Horizontal"""
        if self.get_b() is None:
            return (f"<Horizontal'{self.uid}'"
                    f"{repr(self._a)}{self._a_reference.name}>")
        else:
            return f"<Horizontal'{self.uid}'{repr(self._a)}{repr(self._b)}>"
    
    def __str__(self) -> str:
        """Returns the longer string representation of the Horizontal"""
        if self.get_b() is None:
            return (f"PanCAD Horizontal Constraint '{self.uid}' constraining"
                    f" {repr(self._a)}")
        else:
            return (f"PanCAD Horizontal Constraint '{self.uid}' with"
                    f" {repr(self._a)} as constrained a and {repr(self._b)}"
                    " as constrained b")