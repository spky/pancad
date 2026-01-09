"""A module defining the lists of unique CAD elements used by features and geometry."""
from __future__ import annotations

from collections.abc import MutableSequence
from typing import TYPE_CHECKING

from pancad.exceptions import (
    DupeUidError,
    HasDependentsError,
    MissingCADDependencyError,
)

if TYPE_CHECKING:
    from typing import Sequence
    from uuid import UUID

    from pancad.geometry.abstract_feature import AbstractFeature
    from pancad.geometry.abstract_geometry import AbstractGeometry
    from pancad.geometry.abstract_pancad_thing import PancadThing
    from pancad.geometry.constraints.abstract_constraint import AbstractConstraint
    from pancad.geometry.sketch import SketchGeometrySystem
    from pancad.geometry.feature_container import FeatureContainer


class UniqueCADList(MutableSequence):
    """A class managing a mutable list of CAD elements (geometry, constraints, 
    features).

    :param parent: The object containing this list.
    :param values: elements to initialize the list with.
    :raises DupeUidError: When trying to add multiple of elements with 
        the same uid to the list.
    """
    __type_name = "PancadThing"

    def __init__(self,
                 parent: FeatureContainer,
                 values: Sequence[PancadThing]=None) -> None:
        self._parent = parent
        self._values = []
        if values is not None:
            self.extend(values)

    # Properties
    @property
    def _type_name(self) -> str:
        """Name used in error messages for this list."""
        return self.__type_name

    # Public Methods
    def get_by_uid(self, uid: str | UUID) -> PancadThing:
        """Returns a feature with the matching uid.

        :raises LookupError: When no matching uid is found.
        """
        try:
            return next(value for value in self if value.uid == uid)
        except StopIteration as exc:
            raise LookupError(
                f"No {self._type_name} with uid '{uid}' found."
            ) from exc

    def insert(self, index: int, value: PancadThing) -> None:
        """Inserts the feature into the feature list.

        :raises DupeUidError: When a duped uid value is added to the list.
        """
        self._raise_if_duped_uid(value)
        self._values.insert(index, value)

    def get_contents(self) -> list[PancadThing]:
        """Returns the full list of contents, including any items in specialized 
        indices.
        """
        return self._values

    # Private Methods
    def _raise_if_duped_uid(self, value: PancadThing) -> None:
        """Raises a DupeUidError if the geometry's uid is already in the 
        list. Used when trying to add geometry to the list.
        """
        if value in self:
            raise DupeUidError(
                f"{self._type_name} {value} uid: {value.uid} already in list."
            )

    def _raise_if_has_dependents(self, value: PancadThing) -> None:
        """Raises a SketchGeometryHasConstraintsError if geometry still has 
        constraints. Used when trying to delete geometry from list.
        """
        if dependents := self._parent.get_dependents(value):
            raise HasDependentsError(
                f"{self._type_name} {value} has dependents: {dependents}"
            )

    # Dunders
    def __getitem__(self, index: int) -> PancadThing:
        return self._values[index]

    def __setitem__(self, index: int, value: PancadThing) -> None:
        """Sets the index to the value.

        :raises DupeUidError: When a duped uid value is added to the list.
        :raises HasDependentsError: When trying to replace an element that still 
            has dependents.
        """
        if self[index].uid != value.uid:
            self._raise_if_duped_uid(value)
        self._raise_if_has_dependents(self[index])
        self._values[index] = value

    def __delitem__(self, index: int) -> None:
        """Deletes the value from the list after checking deletion validity.
        
        :raises HasDependentsError: Raised if the feature still has dependents.
        """
        self._raise_if_has_dependents(self[index])
        del self._values[index]

    def __len__(self) -> int:
        return len(self._values)

    def __contains__(self, value: PancadThing) -> bool:
        return any(value.uid == element.uid for element in self.get_contents())

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return str(self._values)


class FeatureList(UniqueCADList):
    """A class managing a mutable list of CAD features. The list's parent 
    does not contribute to the lists's length, but is accessible at index -1.

    :param parent: The FeatureContainer containing this list.
    :param values: Features to initialize the list with.
    """
    __type_name = "Feature"

    def __init__(self,
                 parent: FeatureContainer,
                 values: Sequence[AbstractFeature]) -> None:
        super().__init__(parent, values)

    # Public Methods
    def get_by_name(self, name: str) -> AbstractFeature:
        """Returns the first feature with the matching name.

        :raises LookupError: When no matching name is found.
        """
        try:
            return next(value for value in self if value.name == name)
        except StopIteration as exc:
            raise LookupError(
                f"No {self._type_name} with name '{name}' found."
            ) from exc

    def get_contents(self) -> list[AbstractFeature]:
        return [self._parent] + super().get_contents()

    # Dunders
    def __getitem__(self, index: int) -> AbstractFeature:
        if index == -1:
            return self._parent
        return super().__getitem__(index)


class UniqueSketchList(UniqueCADList):
    """A class managing the interfaces for CAD sketch lists."""
    def insert(self, index: int,
               value: AbstractConstraint | AbstractGeometry) -> None:
        """Inserts the object into the list and assigns its system to the 
        list's parent.
        """
        super().insert(index, value)
        self._assign_system(value)

    # Private Methods
    def _assign_system(self,
                       value: AbstractConstraint | AbstractGeometry) -> None:
        """Assigns the system of the object to the list's parent."""
        if value.system is not None:
            raise ValueError(f"{self._type_name} '{value}' is already"
                             f" in another system: '{value.system}'")
        value.system = self._parent

    # Dunders
    def __delitem__(self, index: int) -> None:
        """Deletes object from list and removes its system."""
        previous_value = self._values[index] # -1 is not allowed here
        super().__delitem__(index)
        previous_value.system = None # Remove the system from exiting geometry

    def __setitem__(self, index: int,
                    value: AbstractConstraint | AbstractGeometry) -> None:
        """Replaces object in list and removes the old object's system."""
        previous_value = self._values[index] # -1 is not allowed here
        super().__setitem__(index, value)
        self._assign_system(value)
        previous_value.system = None # Remove the system from exiting geometry


class GeometryList(UniqueSketchList):
    """A class managing a mutable list of sketch geometry. The sketch's 
    coordinate_system does not contribute to the lists's length, but is 
    accessible at index -1.

    :param parent: The SketchGeometrySystem that contains this list.
    :param values: Geometry to initialize the list with.
    :raises DupeUidError: When trying to add multiple geometries with the same 
        uid to the list.
    """
    __type_name = "Geometry"

    def __init__(self,
                 parent: SketchGeometrySystem,
                 values: Sequence[AbstractGeometry]=None) -> None:
        super().__init__(parent, values)

    def get_contents(self) -> list[AbstractGeometry]:
        return [self._parent] + super().get_contents()

    def __getitem__(self, index: int) -> AbstractGeometry:
        if index == -1:
            return self._parent
        return super().__getitem__(index)


class ConstraintList(UniqueSketchList):
    """A class managing a mutable list of sketch constraints and their 
    dependencies.

    :param parent: The SketchGeometrySystem that contains this list.
    :param values: Constraints to initialize the list with.
    :raises DupeUidError: When trying to add multiple constraints with the same 
        uid to the list.
    """
    __type_name = "Constraint"

    def __init__(self,
                 parent: SketchGeometrySystem,
                 values: Sequence[AbstractConstraint]) -> None:
        for value in values:
            self._raise_if_missing_dependencies(value)
        super().__init__(parent, values)

    # Public Methods
    def insert(self, index: int, value: AbstractConstraint) -> None:
        """Inserts the constraint into the constraint list.
        
        :raises SketchMissingDependencyError: When not all constraint 
            dependencies are in the constraint lists's associated system.
        """
        self._raise_if_missing_dependencies(value)
        super().insert(index, value)

    def missing_dependencies(self, value: AbstractConstraint
                             ) -> list[AbstractGeometry]:
        """Returns missing geometry dependencies for a constraint."""
        return [geometry for geometry in value.get_parents()
                if geometry not in self._parent]

    # Private Methods
    def _raise_if_missing_dependencies(self, value: AbstractConstraint):
        """Raises a SketchMissingDependencyError when not all of a constraint's 
        dependencies are in the list's system.
        """
        if missing := self.missing_dependencies(value):
            raise MissingCADDependencyError(f"'{value}' missing: {missing}")

    # Dunders
    def __setitem__(self, index: int, value: AbstractConstraint) -> None:
        """Sets the index to the constraint.
        
        :raises SketchMissingDependencyError: When not all constraint 
            dependencies are in the constraint lists's parent.
        """
        self._raise_if_missing_dependencies(value)
        super().__setitem__(index, value)

    def __len__(self) -> int:
        return len(self._values)

    def __contains__(self, value: AbstractConstraint) -> bool:
        return any(value.uid == element.uid for element in self)
