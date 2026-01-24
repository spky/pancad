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

    from pancad.abstract import (
        AbstractFeature, AbstractGeometry, AbstractConstraint, PancadThing
    )
    from pancad.geometry.system import SketchGeometrySystem, FeatureSystem


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
                 parent: PancadThing,
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
        """Inserts the pancad element into the list.

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
            msg = f"{self._type_name} {value} uid: {value.uid} already in list."
            raise DupeUidError(msg)

    def _raise_if_has_dependents(self, value: PancadThing) -> None:
        """Raises a HasDependentsError if geometry still has 
        constraints. Used when trying to delete geometry from list.
        """
        if dependents := self._parent.get_dependents(value):
            msg = f"{self._type_name} {value} has dependents: {dependents}"
            raise HasDependentsError(msg)

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


class SystemFeatureList(UniqueCADList):
    """A class managing a mutable list of CAD features inside of a 
    FeatureSystem. The list's parent does not contribute to the lists's 
    length, but is accessible at index -1.

    :param parent: The system containing this list.
    :param values: Features to initialize the list with.
    """
    __type_name = "Feature"

    def __init__(self,
                 parent: FeatureSystem,
                 values: Sequence[AbstractFeature]) -> None:
        super().__init__(parent, values)

    # Public Methods
    def index(self, value: AbstractFeature) -> int:
        if value is self._parent.feature:
            return -1
        return super().index(value)

    def insert(self, index: int, value: AbstractFeature) -> None:
        """Inserts the object into the list and assigns its system to the 
        list's parent.
        """
        super().insert(index, value)
        self._assign_system(value)

    def get_by_name(self, name: str) -> AbstractFeature:
        """Returns the first feature with the matching name.

        :raises LookupError: When no matching name is found.
        """
        try:
            return next(value for value in self if value.name == name)
        except StopIteration as exc:
            msg = f"No {self._type_name} with name '{name}' found."
            raise LookupError(msg) from exc

    def get_contents(self) -> list[AbstractFeature]:
        if self._parent.feature is not None:
            return [self._parent.feature] + super().get_contents()
        return super().get_contents()

    #Private Methods
    def _assign_system(self, value: AbstractFeature) -> None:
        if value.system is not None:
            raise ValueError(f"{self._type_name} '{value}' is already"
                             f" in another system: '{value.system}'")
        value.system = self._parent

    # Dunders
    def __getitem__(self, index: int) -> AbstractFeature:
        if index == -1:
            return self._parent.feature
        return super().__getitem__(index)

    def __setitem__(self, index: int,
                    value: AbstractConstraint | AbstractGeometry) -> None:
        """Replaces object in list and removes the old object's system."""
        previous_value = self._values[index] # -1 is not allowed here
        super().__setitem__(index, value)
        self._assign_system(value)
        # Remove the system from exiting element
        previous_value.system = None

class FeatureConstraintList(UniqueCADList):
    """A class managing the mutable list of constraints between features and 
    their dependencies.
    """
    __type_name = "Constraint"

    def __init__(self,
                 parent: FeatureSystem,
                 values: Sequence[AbstractConstraint]) -> None:
        # TODO: Check for constraint dependencies
        for value in values:
            self._raise_if_missing_dependencies(value)
        super().__init__(parent, values)

    # Public Methods
    def insert(self, index: int, value: AbstractConstraint) -> None:
        """Inserts the object into the list and assigns its system to the 
        list's parent.
        """
        super().insert(index, value)
        self._assign_system(value)

    def missing_dependencies(self,
                             value: AbstractConstraint) -> list[AbstractFeature]:
        """Returns missing feature dependencies for a constraint."""
        return [geometry.feature for geometry in value.get_parents()
                if geometry.feature not in self._parent]

    #Private Methods
    def _assign_system(self, value: AbstractConstraint) -> None:
        if value.system is not None:
            msg = (f"{self._type_name} '{value}' is already"
                   f" in another system: '{value.system}'")
            raise ValueError(msg)
        if value.feature is not None:
            msg = (f"{self._type_name} '{value}' is already"
                   f" in another feature: '{value.feature}'")
            raise ValueError(msg)
        value.system = self._parent
        value.feature = self._parent.feature

    def _raise_if_missing_dependencies(self, value: AbstractConstraint):
        """Raises a MissingCADDependencyError when not all of a constraint's 
        dependencies are in the list's system.
        """
        if missing := self.missing_dependencies(value):
            msg = f"Constraint '{value}' missing feature dependency: {missing}"
            raise MissingCADDependencyError(msg)

    # Dunders
    def __setitem__(self, index: int, value: AbstractConstraint) -> None:
        """Replaces object in list and removes the old object's system and 
        feature.
        """
        previous_value = self._values[index] # -1 is not allowed here
        super().__setitem__(index, value)
        self._assign_system(value)
        # Remove the system from exiting element
        previous_value.system = None
        previous_value.feature = None

class FeatureGeometryList(UniqueCADList):
    """A class managing the list of geometry that a feature owns. Feature 
    geometry includes any geometry that would need to be deleted if the 
    feature was deleted.
    """
    __type_name = "Feature Geometry"

    def __init__(self, parent: AbstractFeature,
                 values: Sequence[AbstractGeometry]) -> None:
        super().__init__(parent, values)

    def insert(self, index: int, value: AbstractGeometry) -> None:
        """Inserts the object into the list and assigns its feature to the 
        list's parent.
        """
        super().insert(index, value)
        self._assign_feature(value)

    def _assign_feature(self, value: AbstractGeometry) -> None:
        if value.feature is not None:
            raise ValueError(f"{self._type_name} '{value}' is already"
                             f" in another feature: '{value.feature}'")
        value.feature = self._parent

    def __delitem__(self, index: int) -> None:
        """Deletes object from list and removes its feature."""
        previous_value = self._values[index]
        super().__delitem__(index)
        # Remove the feature from exiting geometry
        previous_value.feature = None

    def __setitem__(self, index: int,
                    value: AbstractConstraint | AbstractGeometry) -> None:
        """Replaces object in list and removes the old object's feature."""
        previous_value = self._values[index]
        super().__setitem__(index, value)
        self._assign_feature(value)
        # Remove the feature from exiting geometry
        previous_value.feature = None

class UniqueSketchElementList(UniqueCADList):
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
        """Assigns the system of the sketch element to the list's parent and the 
        feature to the parent's feature.
        """
        if value.system is not None:
            raise ValueError(f"{self._type_name} '{value}' is already"
                             f" in another system: '{value.system}'")
        value.system = self._parent
        value.feature = self._parent.feature

    # Dunders
    def __delitem__(self, index: int) -> None:
        """Deletes object from list and removes its system."""
        previous_value = self._values[index] # -1 is not allowed here
        super().__delitem__(index)
        # Remove the system from exiting element
        previous_value.system = None
        previous_value.feature = None

    def __setitem__(self, index: int,
                    value: AbstractConstraint | AbstractGeometry) -> None:
        """Replaces object in list and removes the old object's system."""
        previous_value = self._values[index] # -1 is not allowed here
        super().__setitem__(index, value)
        self._assign_system(value)
        # Remove the system from exiting element
        previous_value.system = None
        previous_value.feature = None


class SketchGeometryList(UniqueSketchElementList):
    """A class managing a mutable list of geometry. The list's parent does not 
    contribute to the lists's length, but is accessible at index -1.

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


class SketchConstraintList(UniqueSketchElementList):
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
        
        :raises MissingCADDependencyError: When not all constraint
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
        """Raises a MissingCADDependencyError when not all of a constraint's 
        dependencies are in the list's system.
        """
        if missing := self.missing_dependencies(value):
            raise MissingCADDependencyError(f"'{value}' missing: {missing}")

    # Dunders
    def __setitem__(self, index: int, value: AbstractConstraint) -> None:
        """Sets the index to the constraint.
        
        :raises MissingCADDependencyError: When not all constraint 
            dependencies are in the constraint lists's parent.
        """
        self._raise_if_missing_dependencies(value)
        super().__setitem__(index, value)

    def __len__(self) -> int:
        return len(self._values)

    def __contains__(self, value: AbstractConstraint) -> bool:
        return any(value.uid == element.uid for element in self)
