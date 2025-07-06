"""A module providing a constraint classes for snapto constraints in 2D 
geometry contexts. PanCAD defines a snapto constraint as one that can be applied 
to geometry with no additional arguments but still meaningfully constrain the 
geometry.

Horizontal can be used to force a Line/LineSegment to be held horizontal 
(parallel to x-axis in 2D) or it can be used to force 2 points to be 
collinear with a theoretical horizontal line.

Vertical can be used to force a Line/LineSegment to be held vertical 
(parallel to y-axis in 2D) or it can be used to force 2 points to be collinear 
with a theoretical vertical line.

"""

from __future__ import annotations

from functools import reduce
from abc import abstractmethod

from PanCAD.geometry.constraints.abstract_constraint import AbstractConstraint
from PanCAD.geometry import Point, Line, LineSegment, CoordinateSystem
from PanCAD.geometry.constants import ConstraintReference

class AbstractSnapTo(AbstractConstraint):
    # Type Tuples for checking with isinstance()
    CONSTRAINED_TYPES = (Point, Line, LineSegment, CoordinateSystem)
    ONE_GEOMETRY_TYPES = (Line, LineSegment)
    TWO_GEOMETRY_TYPES = (Point,)
    GEOMETRY_TYPES = ONE_GEOMETRY_TYPES + TWO_GEOMETRY_TYPES
    
    # Type Hints
    ConstrainedType = reduce(lambda x, y: x | y, CONSTRAINED_TYPES)
    OneConstrainedType = reduce(lambda x, y: x | y, ONE_GEOMETRY_TYPES)
    TwoConstrainedType = TWO_GEOMETRY_TYPES
    GeometryType = reduce(lambda x, y: x | y, GEOMETRY_TYPES)
    
    def __init__(self,
                 constrain_a: ConstrainedType,
                 reference_a: ConstraintReference,
                 constrain_b: ConstrainedType=None,
                 reference_b: ConstraintReference=None,
                 uid: str=None):
        self.uid = uid
        if constrain_b is None or len(constrain_a) == len(constrain_b):
            # One geometry case (e.g. Line or LineSegment)
            self._a = constrain_a
            self._a_reference = reference_a
            self._b = constrain_b
            self._b_reference = reference_b
        else:
            raise ValueError("Geometry a and b must have the same number"
                             " of dimensions")
        self._validate_constrained()
        self._validate_geometry()
    
    # Private Methods #
    def _validate_constrained(self):
        """Raises an error if the geometries are not one of the allowed 
        types"""
        if self._b is None:
            if not isinstance(self._a, self.CONSTRAINED_TYPES):
                raise ValueError(
                    f"geometry a must be one of:\n{self.CONSTRAINED_TYPES}\n"
                    f"Given: {self._a.__class__}"
                )
        elif (not isinstance(self._a, self.CONSTRAINED_TYPES)
                or not isinstance(self._b, self.CONSTRAINED_TYPES)):
            raise ValueError(
                f"geometry a and b must be one of:\n{self.CONSTRAINED_TYPES}\n"
                f"Given: {self._a.__class__} and {self._b.__class__}"
            )
        elif len(self._a) == 3 or len(self._b) == 3:
            raise ValueError("geometry must be 2D to be constrained"
                             f" {self.__class__.__name__}")
        elif self._a is self._b:
            raise ValueError("geometry a/b cannot be the same geometry element")
    
    def _validate_geometry(self) -> None:
        """Raises an error if the constrained geometries are not one of the 
        allowed types"""
        if self._b is None and not isinstance(self._a,
                                              self.ONE_GEOMETRY_TYPES):
            name = self.__class__.__name__
            raise ValueError(
                f"A single geometry {self.__class__.__name__} relation can only"
                f" constrain:\n{self.ONE_GEOMETRY_TYPES}\nGiven: {self._a}"
            )
        elif (self._b is not None
                and not any(
                    [isinstance(g, self.TWO_GEOMETRY_TYPES)
                     for g in self.get_geometry()]
                )):
            classes = [g.__class__ for g in self.get_geometry()]
            raise ValueError(
                f"A two geometry {self.__class__.__name__} relation can only"
                f" constrain:\n{self.TWO_GEOMETRY_TYPES}\nGiven: {classes}"
            )
    
    # Public Methods
    def get_constrained(self) -> tuple[ConstrainedType]:
        """Returns a tuple of the constrained geometry parents"""
        if self._b is None:
            return (self._a,)
        else:
            return (self._a, self._b)
    
    def get_geometry(self) -> tuple[GeometryType]:
        """Returns a tuple of the specific geometry elements inside of the 
        constrained elements"""
        if self._b is None:
            return (self._a.get_reference(self._a_reference),)
        else:
            return (self._a.get_reference(self._a_reference),
                    self._b.get_reference(self._b_reference))
    
    def get_references(self) -> tuple[ConstraintReference]:
        """Returns a tuple of the constrained geometry's references"""
        if self._b is None:
            return (self._a_reference,)
        else:
            return (self._a_reference, self._b_reference)
    
    # Python Dunders #
    def __eq__(self, other: AbstractSnapTo) -> bool:
        """Checks whether two snapto relations are functionally the same by 
        comparing the memory ids of their constrained geometries.
        
        :param other: Another snapto relationship of the same type.
        :returns: Whether the relations are the same.
        """
        geometry_zip = zip(self.get_geometry(), other.get_geometry())
        if isinstance(other, self.__class__):
            return all([g is other_g for g, other_g in geometry_zip])
        else:
            return NotImplemented
    
    def __repr__(self) -> str:
        """Returns the short string representation of the snapto relation"""
        name = self.__class__.__name__
        if self._b is None:
            return (f"<{name}'{self.uid}'"
                    f"{repr(self._a)}{self._a_reference.name}>")
        else:
            return f"<{name}'{self.uid}'{repr(self._a)}{repr(self._b)}>"
    
    def __str__(self) -> str:
        """Returns the longer string representation of the snapto relation"""
        name = self.__class__.__name__
        if self._b is None:
            return (f"PanCAD {name} Constraint '{self.uid}' constraining"
                    f" {repr(self._a)}")
        else:
            return (f"PanCAD {name} Constraint '{self.uid}' with"
                    f" {repr(self._a)} as constrained a and {repr(self._b)}"
                    " as constrained b")
    
    # Abstract Methods #
    @abstractmethod
    def check(self) -> bool:
        """Returns whether the constraint is met by the geometry."""

class Horizontal(AbstractSnapTo):
    def check(self) -> bool:
        """Returns whether the constraint is met by the geometry."""
        raise NotImplementedError("Horizontal check not implemented yet")

class Vertical(AbstractSnapTo):
    def check(self) -> bool:
        """Returns whether the constraint is met by the geometry."""
        raise NotImplementedError("Vertical check not implemented yet")