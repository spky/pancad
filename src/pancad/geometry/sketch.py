"""A module providing a class to represent sketches in 3D space. pancad defines a 
sketch as a set of 2D geometry on a coordinate system's plane oriented in 3D 
space. pancad's sketch definition aims to be as general as possible, so the 
base implementation of this class does not include appearance information since 
that is application specific.
"""
from __future__ import annotations

from collections import namedtuple
from collections.abc import MutableSequence
from itertools import compress
from typing import TYPE_CHECKING, Self, ClassVar
from textwrap import indent
import dataclasses

from pancad.geometry import AbstractFeature, AbstractGeometry, CoordinateSystem
from pancad.geometry.constants import SketchConstraint, ConstraintReference
from pancad.geometry.constraints import make_constraint
from pancad.utils.constraints import parse_pairs
from pancad.utils.initialize import get_pancad_config
from pancad.utils.geometry import (three_dimensions_required,
                                   two_dimensions_required)

if TYPE_CHECKING:
    from uuid import UUID
    from collections.abc import Sequence

    from pancad.geometry import Plane
    from pancad.constraints import AbstractConstraint

DEFAULT_NAME = get_pancad_config()["features"]["default_names"]["sketch"]

SketchGeometry = namedtuple("SketchGeometry", ["geometry", "construction"])

@dataclasses.dataclass
class SketchSettings:
    """A dataclass containing the settings for a Sketch feature.
    
    :param three_system: The 3D CoordinateSystem defining the sketch's position 
        and orientation.
    :param system_plane: A ConstraintReference for one of the three_system's 
        planes that defines which plane the Sketch should appear on.
    :param two_system: The 2D CoordinateSystem that all the sketch's geometry 
        can reference.
    :param name: The name of the feature displayed to the users in CAD.
    :raises ValueError: When the system_plane is not one of the plane_options 
        and when the three/two systems are the wrong dimensions.
    """
    three_system: CoordinateSystem
    system_plane: ConstraintReference
    two_system: CoordinateSystem
    name: str
    plane_options: ClassVar[list[ConstraintReference]] = [
        ConstraintReference.XY, ConstraintReference.XZ, ConstraintReference.YZ
    ]
    def __post_init__(self):
        if self.system_plane not in self.plane_options:
            raise ValueError(f"Expected one of {self.plane_options} for"
                             f" system_plane, got '{self.system_plane}'")
        if self.three_system is not None and len(self.three_system) != 3:
            raise ValueError("three_system must be 3D")
        if len(self.two_system) != 2:
            raise ValueError("two_system must be 2D")

class ConstraintList(MutableSequence):
    """A class managing a mutable list of sketch constraints and their 
    dependencies.
    """
    def __init__(self,
                 system: SketchGeometrySystem,
                 constraints: list[AbstractConstraint]):
        self._system = system
        self._constraints = []
        errors = []
        for constraint in constraints:
            try:
                self.append(constraint)
            except (SketchMissingDependencyError,
                    SketchDupeUidError) as err:
                errors.append(err)
        if errors:
            raise ExceptionGroup("Constraint Addition Errors Encountered",
                                 errors)

    def get_by_uid(self, uid: str | UUID) -> AbstractConstraint:
        """Returns a constraint with the matching uid.
        
        :raises LookupError: When no matching uid is found.
        """
        try:
            return next(c for c in self._constraints if c.uid == uid)
        except StopIteration as err:
            raise LookupError(f"No constraint with uid '{uid}' found.") from err

    def insert(self, index: int, value: AbstractConstraint) -> None:
        """Inserts the constraint into the constraint list.
        
        :raises SketchMissingDependencyError: When not all constraint 
            dependencies are in the constraint lists's associated system.
        """
        if missing := self._missing_dependencies(value):
            raise SketchMissingDependencyError(f"'{value}' missing: {missing}")
        if value in self:
            raise SketchDupeUidError(f"Constraint {value} uid: {value.uid}")
        self._constraints.insert(index, value)

    def _missing_dependencies(self, constraint: AbstractConstraint
                              ) -> list[AbstractGeometry]:
        """Returns missing geometry dependencies for a constraint."""
        return [geometry for geometry in constraint.get_constrained()
                if geometry not in self._system]

    def __getitem__(self, index: int) -> AbstractConstraint:
        return self._constraints[index]

    def __setitem__(self, index: int, value: AbstractConstraint) -> None:
        """Sets the index to the constraint.
        
        :raises LookupError: When not all constraint dependencies are in the 
            constraint lists's associated system.
        """
        if missing := self._missing_dependencies(value):
            raise SketchMissingDependencyError(f"'{value}' missing: {missing}")
        if value in self and self._constraints[index].uid != value.uid:
            raise SketchDupeUidError(f"Constraint {value} uid: {value.uid}")
        self._constraints[index] = value

    def __delitem__(self, index: int) -> None:
        del self._constraints[index]

    def __len__(self) -> int:
        return len(self._constraints)

    def __contains__(self, value: AbstractConstraint) -> bool:
        return any(value.uid == element.uid for element in self)

class GeometryList(MutableSequence):
    """A class managing a mutable list of sketch geometry."""
    def __init__(self,
                 system: SketchGeometrySystem,
                 geometry: Sequence[AbstractGeometry]) -> None:
        self._system = system
        self._geometry = []
        errors = []
        for element in geometry:
            try:
                self.append(element)
            except SketchDupeUidError as err:
                errors.append(err)
        if errors:
            raise ExceptionGroup("Geometry Addition Errors Encountered", errors)

    def insert(self, index: int, value: AbstractGeometry) -> None:
        """Inserts the geometry into the geometry list."""
        self._geometry.insert(index, value)

    def __getitem__(self, index: int) -> AbstractGeometry:
        return self._geometry[index]

    def __setitem__(self, index: int, value: AbstractGeometry) -> None:
        """Sets the index to the geometry. Deletes any constraints on the 
        geometry previously at that index.
        """
        if value in self and self._geometry[index].uid != value.uid:
            raise SketchDupeUidError(f"Geometry {value} uid: {value.uid}")
        if constraints := self._system.get_applied_constraints(value):
            raise SketchGeometryHasConstraintsError(
                f"Geometry index {index} ({self[index]})"
                f"still has constraints: {constraints}"
            )
        self._geometry[index] = value

    def __delitem__(self, index: int) -> None:
        """Deletes the geometry in the system.
        
        :raises ValueError: Raised if the geometry still has constraints applied 
            to it.
        """
        if constraints := self._system.constraints.applied_to(self[index]):
            raise SketchGeometryHasConstraintsError(
                f"Geometry index {index} ({self[index]})"
                f"still has constraints: {constraints}"
            )
        del self._geometry[index]

    def __len__(self) -> int:
        return len(self._geometry)

    def __contains__(self, value: AbstractGeometry) -> bool:
        return any(value.uid == element.uid for element in self)

class SketchGeometrySystem:
    """A class managing the geometry and constraints inside a Sketch.
    
    :param geometry: A sequence of geometry elements.
    :param constraints: A sequence of constraints applied to the geometry.
    :param construction: A subset of the geometry to make as construction. 
        Defaults to an empty set, indicating all geometry is non-construction.
    """
    def __init__(self,
                 geometry: Sequence[AbstractGeometry],
                 constraints: Sequence[AbstractConstraint],
                 construction: Sequence[AbstractGeometry]=None,
                 context: Sketch=None) -> None:
        self.coordinate_system = CoordinateSystem((0, 0), context=context)
        self._geometry = GeometryList(self, geometry)
        self._constraints = ConstraintList(self, constraints)
        if construction:
            self._construction = set(g.uid for g in construction)
        else:
            self._construction = set()

    @property
    def construction(self) -> list[bool]:
        """A list of booleans indicating whether each index of the geometry tuple 
        is construction geometry.
        
        :getter: Returns a list of bools corresponding to each geometry index.
        :setter: Sets the construction tuple after checking that it is the same 
            length as the geometry tuple.
        :raises ValueError: Raised when the construction tuple and geometry tuple 
            are not the same length.
        """
        return [g.uid in self._construction for g in self.geometry]

    @property
    def geometry(self) -> GeometryList:
        """All geometry internal to the system."""
        return self._geometry

    @property
    def constraints(self) -> ConstraintList:
        """All constraints internal to the system."""
        return self._constraints
    @constraints.setter
    def constraints(self, values: Sequence[AbstractConstraint]) -> None:
        self._constraints = ConstraintList(self, values)

    def get_applied_constraints(self, geometry: AbstractGeometry
                                ) -> list[AbstractConstraint]:
        """Returns the sketch constraints that are applied to the geometry."""
        constraints = []
        for constraint in self.constraints:
            if any(constrained.uid == geometry.uid
                   for constrained in constraint.get_constrained()):
                constraints.append(constraint)
        return constraints

    @two_dimensions_required
    def add_geometry(self, geometry: AbstractGeometry,
                     construction: bool=False) -> None:
        """Adds an already generated geometry element to the sketch.
        
        :param geometry: A 2D geometry element.
        :param construction: Sets whether the geometry is construction. Defaults
            to 'False'.
        """
        self._geometry.append(geometry)
        if construction:
            self._construction.add(geometry.uid)

    def add_constraint(self, constraint: AbstractConstraint) -> None:
        """Adds an already generated constraint to the system.
        
        :param constraint: A constraint referring to geometry that is already in 
            the system.
        :raises LookupError: Raised when the constraint's dependencies are not in 
            the sketch.
        """
        if all(geometry in self for geometry in constraint.get_constrained()):
            self.constraints.append(constraint)
        missing = [geometry for geometry in constraint.get_constrained()
                   if geometry not in self]
        raise LookupError(f"{repr(constraint)} dependencies missing: {missing}")

    def get_construction_geometry(self) -> list[AbstractGeometry]:
        """Returns the system's construction geometry."""
        return [g for g in self._geometry if g.uid in self._construction]

    def get_non_construction_geometry(self) -> list[AbstractGeometry]:
        """Returns a tuple of the sketch's non-construction geometry."""
        return [g for g in self._geometry if g.uid not in self._construction]

    def __contains__(self, item: AbstractGeometry | AbstractConstraint) -> bool:
        contents = [*self.geometry, *self.constraints, self.coordinate_system]
        return any(item.uid == element.uid for element in contents)

class Sketch(AbstractFeature, AbstractGeometry):
    """A class representing a set of 2D geometry placed onto a coordinate system 
    plane in 3D space.
    
    :param coordinate_system: A coordinate system defining the sketch's position 
        and orientation. Defaults to an unrotated coordinate system centered at 
        (0, 0, 0).
    :param plane_reference: The ConstraintReference to one of the 
        coordinate_system's planes. Defaults to
        :attr:`~pancad.geometry.constants.ConstraintReference.XY`.
    :param geometry: A sequence of 2D pancad geometry. Defaults to an empty 
        tuple.
    :param construction: A sequence of booleans that determines whether the 
        corresponding geometry index is construction. Defaults to a tuple 
        of all 'False' that is the same length as geometry.
    :param constraints: A sequence of constraints on sketch geometry. Defaults 
        to an empty tuple.
    :param externals: A sequence of geometry external to this sketch that can be 
        referenced by the constraints. Defaults to an empty tuple.
    :param uid: The unique id of the Sketch. Defaults to None.
    :param name: The name of the Sketch that will be used wherever a CAD 
        application requires a human-readable name for the sketch element.
    :param context: The feature that acts as the context for this feature, 
        usually a :class:`~pancad.geometry.FeatureContainer`
    """
    # Class Constants
    REFERENCES = (ConstraintReference.ORIGIN,
                  ConstraintReference.X,
                  ConstraintReference.Y)
    """All relevant ConstraintReferences for Sketch."""
    CONSTRAINT_GEOMETRY_TYPE_STR = "{0}-{1}"
    """Sets the format of constraint constrained geometry summaries."""

    def __init__(self,
                 coordinate_system: CoordinateSystem=None,
                 plane_reference: ConstraintReference=ConstraintReference.XY,
                 geometry: Sequence[AbstractGeometry]=None,
                 construction: Sequence[bool]=None,
                 constraints: Sequence[AbstractConstraint]=None,
                 externals: Sequence[AbstractGeometry]=None,
                 uid: str=None,
                 name: str=DEFAULT_NAME,
                 context: AbstractFeature=None,):
        # Initialize private uid since uid and geometry sync with each other
        self.uid = uid
        two_system = CoordinateSystem((0, 0), context=self)
        self._settings  = SketchSettings(coordinate_system, plane_reference,
                                         two_system, name)
        self._constraints = tuple()
        if geometry is None:
            geometry = tuple()
        if constraints is None:
            constraints = tuple()
        if externals is None:
            externals = tuple()
        self.geometry = geometry
        self.externals = externals
        self.construction = construction
        self.constraints = constraints
        self.context = context
        super().__init__()

    # Properties #
    @property
    def constraints(self) -> tuple[AbstractConstraint]:
        """The tuple of constraints on sketch geometry.
        
        :getter: Returns a tuple of the sketch's constraints.
        :setter: Sets the sketch's constraints after checking that the 
            constraints refer to geometry that is already available in the 
            sketch.
        """
        return self._constraints
    @constraints.setter
    def constraints(self, constraints: Sequence[AbstractConstraint]) -> None:
        for c in constraints:
            self.add_constraint(c)

    @property
    def construction(self) -> tuple[bool]:
        """The booleans indicating whether each index of the geometry tuple is 
        construction geometry.
        
        :getter: Returns the tuple of construction booleans.
        :setter: Sets the construction tuple after checking that it is the same 
            length as the geometry tuple.
        :raises ValueError: Raised when the construction tuple and geometry tuple 
            are not the same length.
        """
        return self._construction
    @construction.setter
    def construction(self, construction: Sequence[bool]) -> None:
        if construction is None and self.geometry is not None:
            self._construction = tuple([False] * len(self.geometry))
        elif construction is None and self.geometry is None:
            self._construction = tuple()
        elif len(construction) != len(self.geometry):
            raise ValueError("geometry and construction must be equal length,"
                             f" given:\n{self.geometry}\n{construction}")
        else:
            self._construction = tuple(construction)

    @property
    def context(self) -> AbstractFeature | None:
        return self._context
    @context.setter
    def context(self, context_feature: AbstractFeature | None) -> None:
        self._context = context_feature

    @property
    def coordinate_system(self) -> CoordinateSystem:
        """The contextual coordinate system that positions and rotates the 
        2D sketch geometry.
        
        :getter: Returns the CoordinateSystem object.
        :setter: Sets the coordinate system.
        """
        return self._settings.three_system
    @coordinate_system.setter
    @three_dimensions_required
    def coordinate_system(self, coordinate_system: CoordinateSystem) -> None:
        self._settings.three_system = coordinate_system

    @property
    def externals(self) -> tuple[AbstractGeometry]:
        """The 3D external geometry referenced by the sketch.
        
        :getter: Returns the tuple of external geometry references.
        :setter: Sets the externals tuple after checking that all of the tuple 
            is 3D.
        """
        return self._externals
    @externals.setter
    def externals(self, externals: Sequence[AbstractGeometry]) -> None:
        if non_3d_externals := list(filter(lambda g: len(g) != 3, externals)):
            raise ValueError(f"3D Geometry only, 2D: {non_3d_externals}")
        self._externals = tuple(externals)

    @property
    def geometry(self) -> tuple[AbstractGeometry]:
        """The 2D geometry in the sketch.
        
        :getter: Returns the tuple of geometry in the sketch.
        :setter: Sets the tuple of geometry in the sketch after checking the new
            lists' validity.
        """
        return self._geometry
    @geometry.setter
    def geometry(self, geometry: Sequence[AbstractGeometry]) -> None:
        if non_2d_geometry := list(filter(lambda g: len(g) != 2, geometry)):
            raise ValueError(f"2D Geometry only, given 3D: {non_2d_geometry}")
        self._geometry = tuple(geometry)

    @property
    def name(self) -> str:
        return self._settings.name
    @name.setter
    def name(self, value: str) -> None:
        dataclasses.replace(self._settings, name=value)

    @property
    def plane_reference(self) -> ConstraintReference:
        """The ConstraintReference for the CoordinateSystem plane that contains 
        the sketch's geometry. Must be one of the enumeration values in 
        :class:`~pancad.geometry.constants.ConstraintReference`.
        
        :getter: Returns the reference of the plane.
        :setter: Checks reference validity and then sets the plane reference.
        :raises ValueError: Raised when provided a constraint reference not 
            allowed to be a plane reference in the sketch
        """
        return self._settings.system_plane
    @plane_reference.setter
    def plane_reference(self, reference: ConstraintReference):
        dataclasses.replace(self._settings, system_plane=reference)

    # Public Functions #
    def add_constraint(self, constraint: AbstractConstraint) -> Self:
        """Adds an already generated constraint to the sketch.
        
        :param constraint: A constraint referring to geometry that is already in 
            the sketch.
        :returns: The updated sketch.
        :raises LookupError: Raised when the constraint's dependencies are not in 
            the sketch.
        """
        dependencies = constraint.get_constrained()
        if all(d in self for d in dependencies):
            self._constraints = self._constraints + (constraint,)
            return self
        missing = filter(lambda d: d not in self, dependencies)
        raise LookupError(f"Dependencies for {repr(constraint)} are missing"
                         f" from sketch: {list(missing)}")

    def add_constraint_by_uid(
                self, type_: SketchConstraint,
                *uid_pairs: (tuple[str | UUID, ConstraintReference]
                             | str
                             | UUID
                             | ConstraintReference),
                **kwargs
            ) -> Self:
        """Adds a sketch constraint between two geometry elements selected by 
        their uids. Prefixes the new constraint's uid with the sketch's uid. All 
        geometry must already be in the sketch's geometry.
        :attr:`~pancad.geometry.constants.ConstraintReference.CS` can be used 
        instead of any of the uid inputs to refer to the sketch's coordinate 
        system.
        
        :param type_: The SketchConstraint of the constraint to be added.
        :param uid_pairs: Pairs of (UUID, ConstraintReference) for each geometry
        :returns: The updated sketch.
        """
        reference_pairs = []
        for uid, reference in parse_pairs(uid_pairs):
            reference_pairs.extend([self.get_geometry_by_uid(uid), reference])
        constraint = make_constraint(type_, *reference_pairs, **kwargs)
        self.add_constraint(constraint)
        return self

    def add_constraint_by_index(
                self, type_: SketchConstraint,
                *index_pairs: (tuple[int, ConstraintReference]
                               | int
                               | ConstraintReference),
                **kwargs
            ) -> Self:
        """Adds a sketch constraint between two geometry elements selected by 
        their indices. Prefixes the new constraint's uid with the sketch's uid. 
        All geometry must already be in the sketch's geometry.
        :attr:`~pancad.geometry.constants.ConstraintReference.CS` can be used 
        instead of any of the index inputs to refer to the sketch's coordinate 
        system.
        
        :param sketch_constraint: The SketchConstraint of the new constraint 
            type.
        :param index_pairs: Pairs of (int, ConstraintReference) for each geometry
        :returns: The updated sketch.
        """
        reference_pairs = []
        for index, reference in parse_pairs(index_pairs):
            reference_pairs.extend(
                [self._get_geometry_by_index(index), reference]
            )
        constraint = make_constraint(type_, *reference_pairs, **kwargs)
        self.add_constraint(constraint)
        return self

    def add_geometry(self,
                     geometry: AbstractGeometry,
                     construction: bool=False) -> Self:
        """Adds an already generated geometry element to the sketch.
        
        :param geometry: A 2D geometry element.
        :param construction: Whether the geometry is construction. Defaults to 
            'False'.
        :returns: The updated sketch.
        """
        if len(geometry) != 2:
            raise ValueError(f"2D Geometry only, given 3D: {geometry}")
        self.geometry = self.geometry + (geometry,)
        self.construction = self.construction + (construction,)
        return self

    def get_all_references(self) -> tuple[ConstraintReference]:
        """Returns all ConstraintReferences applicable to Sketches. See 
        :attr:`Sketch.REFERENCES`.
        """
        return self.REFERENCES

    def get_construction_geometry(self) -> tuple[AbstractGeometry]:
        """Returns the sketch's construction geometry."""
        return tuple(compress(self.geometry, self.construction))

    def get_dependencies(self) -> tuple[AbstractGeometry]:
        if self.coordinate_system is None:
            return self.externals
        return (self.coordinate_system,) + self.externals

    def get_geometry_by_uid(self,
                            uid: str | ConstraintReference) -> AbstractGeometry:
        """Returns a sketch geometry element based on its uid.
        
        :param uid: The uid of the geometry or
            :attr:`~pancad.geometry.constants.ConstraintReference.CS` to 
            reference the sketch's 2D coordinate system.
        :returns: The geometry element with the specified uid.
        """
        geometry_uids = [g.uid for g in self.geometry]
        if uid in geometry_uids:
            return self.geometry[geometry_uids.index(uid)]
        if uid == self.uid:
            return self
        raise ValueError(f"uid '{uid}' was not found in sketch's geometry")

    def get_index_of(self,
                     item: AbstractGeometry | AbstractConstraint | Sketch
                     ) -> int:
        """Returns the index of a geometry, external, or constraint item in 
        their respective tuples. Returns -1 if it's the sketch itself.
        
        :raises LookupError: Raised if the item is not in the sketch geometry, 
            externals, or constraints.
        """
        if any(item is g for g in self.geometry):
            return [item is g for g in self.geometry].index(True)
        if any(item is c for c in self.constraints):
            return [item is c for c in self.constraints].index(True)
        if any(item is g for g in self.externals):
            return [item is g for g in self.externals].index(True)
        if item is self:
            return -1
        raise LookupError(f"Item {item} is not in sketch")

    def get_non_construction_geometry(self) -> tuple[AbstractGeometry]:
        """Returns a tuple of the sketch's non-construction geometry."""
        non_construction = [not c for c in self.construction]
        return tuple(compress(self.geometry, non_construction))

    def get_plane(self) -> Plane:
        """Returns the plane that contains the sketch geometry."""
        return self.coordinate_system.get_reference(self.plane_reference)

    def get_reference(self, reference: ConstraintReference) -> AbstractGeometry:
        """Returns reference geometry for use in external modules like 
        constraints.
        
        :param reference: A ConstraintReference enumeration value applicable to 
            Sketches. See :attr:`Sketch.REFERENCES`.
        :returns: The geometry corresponding to the reference.
        """
        if reference == ConstraintReference.CORE:
            return self
        try:
            return self._settings.two_system.get_reference(reference)
        except ValueError as err:
            raise ValueError("Unexpected ConstraintReference for Sketch's 2D or"
                             " the sketch's 3D references"
                             f" CoordinateSystem: {reference}") from err

    def get_sketch_coordinate_system(self) -> CoordinateSystem:
        """Returns the sketch's 2D coordinate system."""
        return self._settings.two_system

    def update(self, other: Sketch) -> Self:
        """Updates the origin, axes, planes and context of the Sketch to match 
        another Sketch. Does not directly modify the geometry inside the sketch.
        
        :param other: The Sketch to update to.
        :returns: The updated Sketch.
        """
        self._settings.two_system.update(other.get_sketch_coordinate_system())
        self.plane_reference = other.plane_reference
        self.context = other.context
        return self

    # Private Functions #
    def _get_geometry_by_index(self,
                               index: int | None) -> AbstractGeometry | None:
        """Returns the geometry at the index of the sketch's geometry tuple.
        
        :param index: The index of the geometry in the geometry tuple, or 
            ConstraintReference.CS to reference the sketch's coordinate system
        :returns: The geometry at index or the sketch's 2D coordinate system.
        """
        if index == -1:
            return self
        return self.geometry[index]

    # def _generate_summary(self, title_to_type: dict, element_list: list) -> str:
        # """Returns a string summarizing a list of classes of geometry or
        # constraints in table format.
        # """
        # from textwrap import indent
        # summary_strings = []
        # UID_KEYS = ["UID", "a UID", "b UID"]
        # for title, type_ in title_to_type.items():
            # info = []
            # for e in filter(lambda e: isinstance(e, type_), element_list):
                # element_info = self._get_summary_info(e)
                # if not self.STR_VERBOSE:
                    # element_info = {k: v for k, v in element_info.items()
                                    # if k not in UID_KEYS}
                # info.append(element_info)
            # if len(info) > 0:
                # summary_strings.append(title)
                # summary_strings.append(
                    # indent(get_table_string(info), "  ")
                # )
        # summary = "\n".join(summary_strings)
        # summary = indent(summary, "  ")
        # return summary

    def _generate_location_string(self) -> str:
        """Returns a string describing where the sketch is located."""
        if self.coordinate_system is None:
            system_name = None
        else:
            system_name = self.coordinate_system.name
        location_str = (f"On the {self.plane_reference.name} plane"
                        f" in coordinate system  with name '{system_name}'")
        return location_str

    def _generate_quantity_string(self) -> str:
        """Returns a string describing how many elements are in the sketch."""
        n_geo = len(self.geometry)
        n_cons = len(self.constraints)
        n_ext = len(self.externals)
        return (f"[{n_geo} geometries,"
                f" {n_cons} constraints,"
                f" {n_ext} externals]")

    # def _validate_constraint_references(self, constraint) -> None:
        # """Checks whether a constraint references geometry in the sketch's
        # geometry or externals"""
        # references = constraint.get_constrained()
        # if not all([self.has_geometry(g) for g in references]):
            # raise ValueError(f"The {repr(constraint)} constraint references"
                             # " geometry that is not in the sketch."
                             # f"\nAll Geometry: {references}")

    # # Private Dispatch Methods
    # @singledispatchmethod
    # def _get_summary_info(
                # self, geometry: AbstractGeometry | AbstractConstraint
            # ) -> NoReturn:
        # """Returns the summary info for a given geometry type."""
        # raise TypeError(f"{geometry.__class__} not recognized")

    # @_get_summary_info.register
    # def _circle(self, geometry: Circle) -> dict:
        # return {"Index": self.get_index_of(geometry),
                # "UID": geometry.uid,
                # "Center": geometry.center.cartesian,
                # "Radius": geometry.radius,
                # "Construction": self.construction[self.get_index_of(geometry)]}

    # @_get_summary_info.register
    # def _circular_arc(self, geometry: CircularArc) -> dict:
        # return {
            # "Index": self.get_index_of(geometry),
            # "UID": geometry.uid,
            # "Center": geometry.center.cartesian,
            # "Radius": geometry.radius,
            # "Start": geometry.start.cartesian,
            # "End": geometry.end.cartesian,
            # "Is Clockwise": geometry.is_clockwise,
            # "Construction": self.construction[self.get_index_of(geometry)],
        # }

    # @_get_summary_info.register
    # def _ellipse(self, geometry: Ellipse) -> dict:
        # return {"Index": self.get_index_of(geometry),
                # "UID": geometry.uid,
                # "Center": geometry.center.cartesian,
                # "Semi-Major Axis Length": geometry.semi_major_axis,
                # "Semi-Minor Axis Length": geometry.semi_minor_axis,
                # "Semi-Major Axis Angle": degrees(geometry.major_axis_angle),
                # "Construction": self.construction[self.get_index_of(geometry)]}

    # @_get_summary_info.register
    # def _line(self, geometry: Line) -> dict:
        # return {"Index": self.get_index_of(geometry),
                # "UID": geometry.uid,
                # "X-Intercept": (geometry.x_intercept, 0),
                # "Y-Intercept": (0, geometry.y_intercept),
                # "Construction": self.construction[self.get_index_of(geometry)]}

    # @_get_summary_info.register
    # def _line_segment(self, geometry: LineSegment) -> dict:
        # return {"Index": self.get_index_of(geometry),
                # "UID": geometry.uid,
                # "Start": geometry.point_a.cartesian,
                # "End": geometry.point_b.cartesian,
                # "Construction": self.construction[self.get_index_of(geometry)]}

    # @_get_summary_info.register
    # def _point(self, geometry: Point) -> dict:
        # return {"Index": self.get_index_of(geometry),
                # "UID": geometry.uid,
                # "Location": geometry.cartesian,
                # "Construction": self.construction[self.get_index_of(geometry)]}

    # @_get_summary_info.register
    # def _state_constraint(self, constraint: AbstractStateConstraint) -> dict:
        # geometry_a, geometry_b = constraint.get_constrained()
        # reference_a, reference_b = constraint.get_references()
        # return {"Index": self.get_index_of(constraint),
                # "Type": constraint.__class__.__name__,
                # "a Index": self.get_index_of(geometry_a),
                # "a UID": geometry_a.uid,
                # "a Type": self.CONSTRAINT_GEOMETRY_TYPE_STR.format(
                    # geometry_a.__class__.__name__,
                    # reference_a.name.title(),
                # ),
                # "b Index": self.get_index_of(geometry_b),
                # "b UID": geometry_b.uid,
                # "b Type": self.CONSTRAINT_GEOMETRY_TYPE_STR.format(
                    # geometry_b.__class__.__name__,
                    # reference_b.name.title()
                # )}

    # @_get_summary_info.register
    # def _state_constraint(self, constraint: AbstractSnapTo) -> dict:
        # geometry = constraint.get_constrained()
        # references = constraint.get_references()
        # if len(geometry) == 1:
            # geometry_a = geometry[0]
            # reference_a = references[0]
            # return {
                # "Index": self.get_index_of(constraint),
                # "Type": constraint.__class__.__name__,
                # "a Index": self.get_index_of(geometry_a),
                # "a UID": geometry_a.uid,
                # "a Type": self.CONSTRAINT_GEOMETRY_TYPE_STR.format(
                    # geometry_a.__class__.__name__,
                    # reference_a.name.title()
                # ),
                # "b Index": None,
                # "b UID": None,
                # "b Type": None,
            # }
        # else:
            # geometry_a, geometry_b = geometry
            # reference_a, reference_b = references
            # return {
                # "Index": self.get_index_of(constraint),
                # "Type": constraint.__class__.__name__,
                # "a Index": self.get_index_of(geometry_a),
                # "a UID": geometry_a.uid,
                # "a Type": self.CONSTRAINT_GEOMETRY_TYPE_STR.format(
                    # geometry_a.__class__.__name__,
                    # reference_a.name.title()
                # ),
                # "b Index": self.get_index_of(geometry_b),
                # "b UID": geometry_b.uid,
                # "b Type": self.CONSTRAINT_GEOMETRY_TYPE_STR.format(
                    # geometry_b.__class__.__name__,
                    # reference_b.name.title()
                # ),
            # }

    # @_get_summary_info.register
    # def _1_geo_distance(self, constraint: Abstract1GeometryDistance) -> dict:
        # geometry_a = constraint.get_constrained()[0]
        # reference_a = constraint.get_references()[0]
        # return {
            # "Index": self.get_index_of(constraint),
            # "Type": constraint.__class__.__name__,
            # "a Index": self.get_index_of(geometry_a),
            # "a UID": geometry_a.uid,
            # "a Type": self.CONSTRAINT_GEOMETRY_TYPE_STR.format(
                # geometry_a.__class__.__name__,
                # reference_a.name.title()
            # ),
            # "Value": constraint.get_value_string(),
        # }

    # @_get_summary_info.register
    # def _2_geo_distance(self, constraint: Abstract2GeometryDistance) -> dict:
        # geometry_a, geometry_b = constraint.get_constrained()
        # reference_a, reference_b = constraint.get_references()
        # return {
            # "Index": self.get_index_of(constraint),
            # "Type": constraint.__class__.__name__,
            # "a Index": self.get_index_of(geometry_a),
            # "a UID": geometry_a.uid,
            # "a Type": self.CONSTRAINT_GEOMETRY_TYPE_STR.format(
                # geometry_a.__class__.__name__,
                # reference_a.name.title()
            # ),
            # "b Index": self.get_index_of(geometry_b),
            # "b UID": geometry_b.uid,
            # "b Type": self.CONSTRAINT_GEOMETRY_TYPE_STR.format(
                # geometry_b.__class__.__name__,
                # reference_b.name.title()
            # ),
            # "Value": constraint.get_value_string(),
        # }

    # @_get_summary_info.register
    # def _angle(self, constraint: Angle) -> dict:
        # geometry_a, geometry_b = constraint.get_constrained()
        # reference_a, reference_b = constraint.get_references()
        # return {
            # "Index": self.get_index_of(constraint),
            # "a Index": self.get_index_of(geometry_a),
            # "a UID": geometry_a.uid,
            # "a Type": self.CONSTRAINT_GEOMETRY_TYPE_STR.format(
                # geometry_a.__class__.__name__,
                # reference_a.name.title()
            # ),
            # "b Index": self.get_index_of(geometry_b),
            # "b UID": geometry_b.uid,
            # "b Type": self.CONSTRAINT_GEOMETRY_TYPE_STR.format(
                # geometry_b.__class__.__name__,
                # reference_b.name.title()
            # ),
            # "Value": constraint.get_value_string(),
            # "Quadrant": constraint.quadrant,
        # }

    # Python Dunders #
    def __copy__(self) -> Sketch:
        raise NotImplementedError("Sketch copy hasn't been implemented yet,"
                                  " see github issue #53")

    def __contains__(self, item: AbstractGeometry):
        contents = [geometry.uid for geometry in self.geometry]
        contents.append(self.uid)
        return item.uid in contents

    def __len__(self) -> int:
        """Sketches are always 3 dimensional"""
        return 3

    def __repr__(self) -> str:
        """Returns the short string representation of the sketch"""
        return f"<Sketch'{self.name}'>"

    def __str__(self) -> str:
        """Returns the longer string representation of the sketch"""
        sketch_summary = []
        sketch_summary.append(f"Sketch '{self.name}'")
        if self.STR_VERBOSE:
            sketch_summary.append(indent(f"Sketch uid: {self.uid}", "  "))
        # Location/Plane Summary
        sketch_summary.append(
            indent(self._generate_location_string(), "  ")
        )
        # Geometry Summary #
        # sketch_summary.append("Geometry")
        # summaries = {
            # "Circles": Circle,
            # "Circular Arcs": CircularArc,
            # "Ellipses": Ellipse,
            # "Line Segments": LineSegment,
            # "Infinite Lines": Line,
            # "Points": Point,
        # }
        # sketch_summary.append(
            # self._generate_summary(summaries, self.geometry)
        # )
        # Constraint Summary #
        # sketch_summary.append("Constraints")
        # summaries = {
            # "State Constraints": AbstractStateConstraint,
            # "Snap To Constraints": AbstractSnapTo,
            # "Distance Constraints": Abstract2GeometryDistance,
            # "Radius and Diameter Constraints": Abstract1GeometryDistance,
            # "Angle Constraints": Angle,
        # }
        # sketch_summary.append(
            # self._generate_summary(summaries, self.constraints)
        # )
        sketch_summary.append(self._generate_quantity_string())
        return "\n".join(sketch_summary)

class SketchDupeUidError(ValueError):
    """Raised when an element with an already added uid is added to a sketch 
    element list.
    """

class SketchMissingDependencyError(LookupError):
    """Raised when attempting to add a constraint to a sketch missing its 
    dependencies.
    """

class SketchGeometryHasConstraintsError(ValueError):
    """Raised when attempting to remove geometry from a sketch while it still has 
    detectable constraints.
    """
