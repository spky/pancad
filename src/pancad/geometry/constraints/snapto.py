"""A module providing a constraint classes for snapto constraints in 2D 
geometry contexts. pancad defines a snapto constraint as one that can be applied 
to geometry with no additional arguments but still meaningfully constrain the 
geometry.
"""

from __future__ import annotations

from functools import reduce
from typing import TYPE_CHECKING

from pancad.geometry.constraints import AbstractConstraint
from pancad.geometry import (
    Circle,
    CircularArc,
    CoordinateSystem,
    Ellipse,
    Line,
    LineSegment,
    Point,
)

if TYPE_CHECKING:
    from typing import NoReturn
    from pancad.geometry.constants import ConstraintReference

class AbstractSnapTo(AbstractConstraint):
    """An abstract class of constraints that can be applied to a set of **one 
    or two** geometries without any further definition.
    
    :param constrain_a: The first geometry to be constrained.
    :param reference_a: The ConstraintReference of the portion of constrain_a to 
        be constrained.
    :param constrain_b: The second geometry to be constrained. Does not need to 
        be provided if only constraining constrain_a.
    :param reference_b: The ConstraintReference of the portion of constrain_b to 
        be constrained.
    :param uid: The unique id of the constraint.
    """
    # Type Tuples for checking with isinstance()
    CONSTRAINED_TYPES = (
        Circle,
        CircularArc,
        CoordinateSystem,
        Ellipse,
        Line,
        LineSegment,
        Point,
    )
    ONE_GEOMETRY_TYPES = (Line, LineSegment)
    TWO_GEOMETRY_TYPES = (Point,)
    GEOMETRY_TYPES = ONE_GEOMETRY_TYPES + TWO_GEOMETRY_TYPES
    
    # Type Hints
    ConstrainedType = reduce(lambda x, y: x | y, CONSTRAINED_TYPES)
    GeometryType = reduce(lambda x, y: x | y, GEOMETRY_TYPES)
    OneConstrainedType = reduce(lambda x, y: x | y, ONE_GEOMETRY_TYPES)
    """The types of geometry constrainable by this constraint without a second 
    geometry element.
    """
    TwoConstrainedType = reduce(lambda x, y: x | y, TWO_GEOMETRY_TYPES)
    """The types of geometry that can be constrained by this constraint relative 
    to second geometry element.
    """
    
    def __init__(self,
                 constrain_a: ConstrainedType,
                 reference_a: ConstraintReference,
                 constrain_b: ConstrainedType=None,
                 reference_b: ConstraintReference=None,
                 uid: str=None) -> None:
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
    
    # Public Methods
    def get_constrained(self) -> tuple[ConstrainedType]:
        if self._b is None:
            return (self._a,)
        else:
            return (self._a, self._b)
    
    def get_geometry(self) -> tuple[GeometryType]:
        if self._b is None:
            return (self._a.get_reference(self._a_reference),)
        else:
            return (self._a.get_reference(self._a_reference),
                    self._b.get_reference(self._b_reference))
    
    def get_references(self) -> tuple[ConstraintReference]:
        if self._b is None:
            return (self._a_reference,)
        else:
            return (self._a_reference, self._b_reference)
    
    # Private Methods #
    def _validate_constrained(self) -> NoReturn:
        """Raises an error if the constrained geometries are not one of the 
        allowed types.
        """
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
    
    def _validate_geometry(self) -> NoReturn:
        """Raises an error if the portions of the constrained geometries are not 
        one of the allowed types.
        """
        if self._b is None and not all([isinstance(g, self.ONE_GEOMETRY_TYPES)
                                        for g in self.get_geometry()]):
            name = self.__class__.__name__
            raise ValueError(
                f"A single geometry {self.__class__.__name__} relation can only"
                f" constrain:\n{self.ONE_GEOMETRY_TYPES}\nGiven: {self._a}"
            )
        elif (self._b is not None
                and not any([isinstance(g, self.TWO_GEOMETRY_TYPES)
                            for g in self.get_geometry()])
                ):
            classes = [g.__class__ for g in self.get_geometry()]
            raise ValueError(
                f"A two geometry {self.__class__.__name__} relation can only"
                f" constrain:\n{self.TWO_GEOMETRY_TYPES}\nGiven: {classes}"
            )
    
    # Python Dunders #
    def __eq__(self, other: AbstractSnapTo) -> bool:
        """Checks whether two snapto relations are functionally the same by 
        comparing the memory ids of their constrained geometries.
        
        :param other: Another SnapTo relationship of the same type.
        :returns: Whether the relations are the same.
        """
        geometry_zip = zip(self.get_geometry(), other.get_geometry())
        if isinstance(other, self.__class__):
            return all([g is other_g for g, other_g in geometry_zip])
        else:
            return NotImplemented

class Horizontal(AbstractSnapTo):
    """A constraint that sets either a single geometry horizontal or a pair of 
    geometries horizontal relative to each other in a 2D coordinate system. Can 
    constrain:
    
    - :class:`~pancad.geometry.CoordinateSystem`
    - :class:`~pancad.geometry.Circle`
    - :class:`~pancad.geometry.CircularArc`
    - :class:`~pancad.geometry.Ellipse`
    - :class:`~pancad.geometry.Line`
    - :class:`~pancad.geometry.LineSegment`
    - :class:`~pancad.geometry.Point`
    """

class Vertical(AbstractSnapTo):
    """A constraint that sets either a single geometry vertical or a pair of 
    geometries vertical relative to each other in a 2D coordinate system. Can 
    constrain:
    
    - :class:`~pancad.geometry.CoordinateSystem`
    - :class:`~pancad.geometry.Circle`
    - :class:`~pancad.geometry.CircularArc`
    - :class:`~pancad.geometry.Ellipse`
    - :class:`~pancad.geometry.Line`
    - :class:`~pancad.geometry.LineSegment`
    - :class:`~pancad.geometry.Point`
    """