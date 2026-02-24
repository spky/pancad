"""A module providing abstract classes to define the interfaces between pancad
CAD objects.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from uuid import uuid4

from pancad.constants import ConstraintReference

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Self
    from uuid import UUID

    from pancad.constants import SketchConstraint


class PancadThing(ABC):
    """An abstract class defining the properties and methods that all pancad
    elements, constraints, or whatever must have with no exceptions.
    """
    def __init__(self, system: PancadThing=None):
        self.system = system

    STR_VERBOSE = False
    """A flag allowing pancad objects to print detailed strings and reprs."""

    # Properties
    @property
    def uid(self) -> str | UUID:
        """The unique id of the element, used for CAD interoperability. Can be
        manually set, but is usually randomly generated or read from an existing
        file.
        """
        return self._uid
    @uid.setter
    def uid(self, value: str | UUID | None) -> None:
        if value is None:
            self._uid = uuid4()
        else:
            self._uid = value

    @property
    def system(self) -> PancadThing | None:
        """The system that defines the object's location and dependencies. Some
        objects like files representing parts or assemblies can exist by
        themselves, which should be represented by settings those objects'
        system to None.
        """
        return self._system
    @system.setter
    def system(self, value: PancadThing | None) -> None:
        self._system = value

    @abstractmethod
    def get_dependencies(self) -> list[PancadThing]:
        """Returns the object's external dependencies. Dependencies are anything
        that if deleted or not present in the object's system the object
        would not be able to function.
        """

    @abstractmethod
    def __repr__(self) -> str:
        strings = ["<", self.__class__.__name__, "{details}", ">"]
        if self.STR_VERBOSE:
            class_index = strings.index(self.__class__.__name__)
            strings.insert(class_index + 1, f"'{self.uid}'")
        return "".join(strings)

    def __str__(self) -> str:
        return repr(self)

class AbstractFeature(PancadThing):
    """A class defining the interfaces provided by pancad Feature elements."""

    def __init__(self, system: PancadThing=None, name: str="") -> None:
        super().__init__(system)
        self._name = name

    # Properties #
    @property
    def name(self) -> str:
        """The name of the feature. Usually user assigned or automatically
        generated. Does not need to be unique.
        """
        return self._name
    @name.setter
    def name(self, value: str) -> str | None:
        self._name = value

    def get_dependencies(self) -> list[AbstractFeature]:
        """Returns the feature's external feature dependencies."""
        if self.system is not None and self is not self.system:
            dependencies = set()
            dependencies.add(self.system.feature)
            dependencies.update(self.system.get_topo_dependencies(self))
            return list(dependencies)
        return []


class AbstractGeometry(PancadThing):
    """A class defining the interfaces provided by pancad Geometry Elements."""
    def __init__(self, references: dict[ConstraintReference, AbstractGeometry],
                 *,
                 system: AbstractGeometrySystem=None,
                 feature: AbstractFeature=None,
                 ) -> None:
        self._references = references
        super().__init__(system)
        self.feature = feature
        for _, child in self.children.items():
            if child.uid != self.uid:
                child.parent = self

    @property
    def feature(self) -> AbstractFeature:
        """The feature that owns this geometry element."""
        return self._feature
    @feature.setter
    def feature(self, value: AbstractFeature) -> None:
        self._feature = value
        for _, child in self.children.items():
            if child.uid != self.uid:
                child.feature = value

    @property
    def system(self) -> PancadThing | None:
        return self._system
    @system.setter
    def system(self, value: PancadThing | None) -> None:
        self._system = value
        for _, child in self.children.items():
            if child.uid != self.uid:
                child.system = value

    @property
    def parent(self) -> AbstractGeometry | None:
        """The parent of the geometry.

        Example: A circle center point's parent would be the circle, but if the
        point's parent is None then the point is its own parent. Should
        never be set by the instance itself, only by the parent to claim
        ownership.
        """
        if not hasattr(self, "_parent"):
            return None
        parent = self._parent
        while parent.parent:
            parent = parent.parent
        return parent
    @parent.setter
    def parent(self, value: AbstractGeometry) -> None:
        self._parent = value

    @property
    def self_reference(self) -> ConstraintReference:
        """The ConstraintReference that applies to this instance of geometry.
        Example: A circle's curve would be CORE, but its center point would
        be CENTER. A point with no parent would be CORE.
        """
        if self.parent is None:
            return ConstraintReference.CORE
        uid_to_child = {geometry.uid: reference
                        for reference, geometry in self.parent.children.items()}
        return uid_to_child[self.uid]

    @property
    def children(self) -> dict[ConstraintReference, AbstractGeometry]:
        """The mapping of the geometry's constraint references to its child
        geometries. Read-only.
        """
        return {reference: self.get_reference(reference)
                for reference in self.get_all_references()}

    # Public Methods
    def get_dependencies(self) -> list[AbstractFeature]:
        """Returns the features that this geometry element depends on."""
        dependencies = []
        if self.feature:
            dependencies.append(self.feature)
        return dependencies

    def get_reference(self, reference: ConstraintReference) -> AbstractGeometry:
        """Returns the subgeometry associated with the reference."""
        return self._references[reference]

    def get_all_references(self) -> tuple[ConstraintReference]:
        """Returns the constraint references available for the geometry."""
        return list(self._references.keys())

    # Abstract Methods
    @abstractmethod
    def update(self, other: AbstractGeometry) -> Self:
        """Takes geometry of the same type as the calling geometry and updates
        the calling geometry to match the new geometry while maintaining its
        uid. Should return itself afterwards.
        """

    # Python Dunders #
    def __len__(self) -> int:
        """Implements the Python len() function to return whether the geometry
        is 2D or 3D.
        """

class AbstractGeometrySystem(AbstractGeometry):
    """A type of geometry defining interfaces provided by systems of pancad
    Geometry elements. A geometry system is a system managing interfaces between
    geometry and constraints. All geometry system geometry is defined relative
    to the geometry system's internal coordinate system.
    """

    @abstractmethod
    def get_dependencies(self) -> list[AbstractFeature]:
        """Must return the features that the system depends on."""

    @abstractmethod
    def get_dependents(self, element: PancadThing) -> list[PancadThing]:
        """Must return any elements that depend on the element in the context of
        the system.
        """

class AbstractConstraint(PancadThing):
    """A class defining the interfaces provided by all pancad Constraint
    Elements.
    """
    def __init__(self,
                 system: AbstractGeometrySystem=None) -> None:
        self.system = system
        if system:
            self.feature = system.feature
        else:
            self.feature = None

    # Properties
    @property
    def feature(self) -> AbstractFeature | None:
        """The feature that owns this constraint."""
        return self._feature
    @feature.setter
    def feature(self, value: AbstractFeature):
        self._feature = value

    @property
    def _geometry(self) -> list[AbstractGeometry]:
        """The geometry being constrained"""
        return self.__geometry
    @_geometry.setter
    def _geometry(self, values: Sequence[AbstractGeometry]) -> None:
        self.__geometry = list(values)

    @property
    def _pairs(self) -> list[tuple[AbstractGeometry, ConstraintReference]]:
        return self.__pairs
    @_pairs.setter
    def _pairs(self, value: list[tuple[AbstractGeometry,
                                       ConstraintReference]]) -> None:
        self.__pairs = value

    @property
    def system(self) -> AbstractGeometrySystem | None:
        """The system the constraint is in. This defaults to None unless set by
        a higher level context like a SketchGeometrySystem object.
        """
        if not hasattr(self, "_system"):
            return None
        return self._system
    @system.setter
    def system(self, value: AbstractGeometrySystem) -> None:
        self._system = value

    # Abstract Properties
    @property
    @abstractmethod
    def type_name(self) -> SketchConstraint:
        """Returns the SketchConstraint enum value for the constraint type."""

    # Public Methods
    def get_dependencies(self) -> list[AbstractFeature]:
        """Returns the features that this constraint depends on."""
        geometry_deps = []
        for geometry in self.get_parents():
            if geometry.feature is None:
                raise ValueError(f"Geometry '{geometry}' cannot be constrained"
                                 " if its feature is None")
            geometry_deps.append(geometry.feature)
        geometry_deps = [geometry.feature for geometry in self.get_parents()]
        return list(set([self.system.feature] + geometry_deps))

    def get_parents(self) -> list[AbstractGeometry]:
        """Returns highest geometry scope being constrained for each geometry.

        Example: A circle's center point would return the circle object, but a
        standalone point would just return the point.
        """
        parents = []
        for geometry in self._geometry:
            if geometry.parent is None:
                parents.append(geometry)
            else:
                parents.append(geometry.parent)
        return parents

    def get_geometry(self) -> list[AbstractGeometry]:
        """Returns the portions of the constrained geometry being constrained.

        Examples: The x axis of a :class:`~pancad.geometry.CoordinateSystem` or
        the start point of a :class:`~pancad.geometry.LineSegment`.
        """
        return self._geometry

    def get_references(self) -> tuple[ConstraintReference]:
        """Returns a tuple of the constrained geometrys' ConstraintReferences in
        the same order as the tuple returned by :meth:`get_constrained`.
        """
        return tuple(geometry.self_reference for geometry in self._geometry)

    # Dunders
    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        strings = ["<", self.__class__.__name__]
        if self.STR_VERBOSE:
            strings.append(f"'{self.uid}'")
        strings.append("-")
        constrained = self.get_parents()
        references = self.get_references()
        geometry_strings = []
        for geometry, reference in zip(constrained, references):
            geometry_strings.append(
                repr(geometry).replace("<", "").replace(">", "")
            )
            geometry_strings[-1] += reference.name
        strings.append(",".join(geometry_strings))
        strings.append(">")
        return "".join(strings)
