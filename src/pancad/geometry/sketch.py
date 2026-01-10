"""A module providing a class to represent sketches in 3D space. pancad defines a 
sketch as a set of 2D geometry on a coordinate system's plane oriented in 3D 
space. pancad's sketch definition aims to be as general as possible, so the 
base implementation of this class does not include appearance information since 
that is application specific.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from pancad.abstract import AbstractFeature, AbstractGeometry
from pancad.constants import ConstraintReference
from pancad.exceptions import SketchGeometryHasConstraintsError
from pancad.geometry.coordinate_system import CoordinateSystem
from pancad.geometry.unique_lists import GeometryList, ConstraintList
from pancad.utils.initialize import get_pancad_config
from pancad.utils.geometry import two_dimensions_required
from pancad.utils.pancad_types import VectorLike

if TYPE_CHECKING:
    from uuid import UUID
    from numbers import Real
    from collections.abc import Sequence
    from typing import Self

    from pancad.abstract import AbstractConstraint, PancadThing
    from pancad.geometry.line import Line
    from pancad.geometry.plane import Plane
    from pancad.geometry.point import Point

DEFAULT_NAME = get_pancad_config()["features"]["default_names"]["sketch"]

class SketchGeometrySystem(AbstractGeometry):
    """A class managing the geometry and constraints inside a Sketch feature. 
    This class can act as a standalone set of 2D geometry or be contained 
    inside a 3D Sketch feature.
    
    :param geometry: A sequence of geometry elements.
    :param constraints: A sequence of constraints applied to the geometry.
    :param construction: A subset of the geometry to make as construction. 
        Defaults to an empty set, indicating all geometry is non-construction.
    """
    def __init__(self,
                 geometry: Sequence[AbstractGeometry]=None,
                 constraints: Sequence[AbstractConstraint]=None,
                 construction: Sequence[AbstractGeometry]=None,
                 uid: str | UUID=None) -> None:
        self.uid = uid
        self._constraints = ConstraintList(self, [])
        self._geometry = GeometryList(self, [])
        self.system = self # SketchGeometrySystems are their own system
        if geometry is None:
            geometry = []
        if constraints is None:
            constraints = []
        self._coordinate_system = CoordinateSystem((0, 0), context=self)
        self._geometry = GeometryList(self, geometry)
        self._constraints = ConstraintList(self, constraints)
        if construction:
            self._construction = set(g.uid for g in construction)
        else:
            self._construction = set()
        references = {ConstraintReference.CORE: self}
        subreferences = [ConstraintReference.ORIGIN,
                         ConstraintReference.X, ConstraintReference.Y]
        for sub in subreferences:
            references[sub] = self._coordinate_system.get_reference(sub)
        super().__init__(references)

    # Properties #
    @property
    def coordinate_system(self) -> CoordinateSystem:
        """The 2D CoordinateSystem placing the system's geometry. Read-only."""
        return self._coordinate_system

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
    @geometry.setter
    def geometry(self, values: Sequence[AbstractGeometry]) -> None:
        new_uids = {geometry.uid for geometry in values}
        old_uids = {geometry.uid for geometry in self.geometry}
        errors = []
        for uid in old_uids - new_uids:
            geometry = self._geometry.get_by_uid(uid)
            try:
                del self._geometry[self._geometry.index(geometry)]
            except SketchGeometryHasConstraintsError as err:
                errors.append(err)
        if errors:
            raise ExceptionGroup("Errors while replacing GeometryList",
                                 errors)
        self._geometry = GeometryList(self, values)

    @property
    def constraints(self) -> ConstraintList:
        """All constraints internal to the system."""
        return self._constraints
    @constraints.setter
    def constraints(self, values: Sequence[AbstractConstraint]) -> None:
        self._constraints = ConstraintList(self, values)

    @property
    def origin(self) -> Point:
        """The origin of the sketch coordinate system."""
        return self.coordinate_system.origin

    @property
    def feature(self) -> AbstractFeature | None:
        """The feature that the SketchGeometrySystem is inside of. 
        For SketchGeometrySystems defined without one this will be None. Intended 
        to only be set by a higher level AbstractFeature object.
        """
        if not hasattr(self, "_feature"):
            return None
        return self._feature
    @feature.setter
    def feature(self, value: AbstractFeature) -> None:
        self._feature = value

    @property
    def x_axis(self) -> Line:
        """The x axis of the sketch coordinate system."""
        return self.coordinate_system.get_axis_line_x()

    @property
    def y_axis(self) -> Line:
        """The y axis of the sketch coordinate system."""
        return self.coordinate_system.get_axis_line_y()

    # Public Methods
    def get_dependencies(self) -> list[AbstractFeature]:
        """Gets all the features this system depends on."""
        dependencies = set()
        for constraint in self.constraints:
            dependencies.update(constraint.get_dependencies())
        return list(dependencies)

    def get_dependents(self, element: AbstractGeometry | AbstractConstraint=None
                       ) -> list[PancadThing]:
        """Gets the dependents in the scope of the system or an element in the 
        system.

        :param element: The element to look for dependents of. When None, all 
            dependents for the system are returned.
        :raises LookupError: When the element is not in the system.
        """
        if element is None:
            # Get all dependents
            dependents = set()
            for value in [*self.geometry, *self.constraints]:
                dependents.update(self.get_dependents(value))
            return list(dependents)
        # Get element filtered dependents
        if element not in self:
            raise LookupError(f"Element '{element}' not in this sketch")
        dependents = []
        for constraint in self.constraints:
            # Check if any constraints depend on the element.
            if any(constrained.uid == element.uid
                   for constrained in constraint.get_parents()):
                dependents.append(constraint)
        return dependents

    def get_applied_constraints(self, geometry: AbstractGeometry
                                ) -> list[AbstractConstraint]:
        """Returns the sketch constraints that are applied to the geometry."""
        constraints = []
        for constraint in self.constraints:
            if any(constrained.uid == geometry.uid
                   for constrained in constraint.get_parents()):
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
        if all(geometry in self for geometry in constraint.get_parents()):
            self.constraints.append(constraint)
        missing = [geometry for geometry in constraint.get_parents()
                   if geometry not in self]
        raise LookupError(f"{repr(constraint)} dependencies missing: {missing}")

    def get_construction_geometry(self) -> list[AbstractGeometry]:
        """Returns the system's construction geometry."""
        return [g for g in self._geometry if g.uid in self._construction]

    def get_non_construction_geometry(self) -> list[AbstractGeometry]:
        """Returns a tuple of the sketch's non-construction geometry."""
        return [g for g in self._geometry if g.uid not in self._construction]

    def update(self, other: SketchGeometrySystem) -> Self:
        """Updates the origin, axes, planes and context of the Sketch to match 
        another Sketch. Does not directly modify the geometry inside the sketch.
        """
        self._coordinate_system.update(other.coordinate_system)
        return self

    # Python Dunders #
    def __len__(self) -> int:
        """SketchGeometrySystems are always 2D."""
        return 2

    def __contains__(self, item: AbstractGeometry | AbstractConstraint) -> bool:
        return item in self.geometry or item in self.constraints

    def __repr__(self) -> str:
        return super().__repr__().format(
            details=f"({len(self._geometry)}g{len(self._constraints)}c)"
        )

class Pose(AbstractGeometry):
    """The position and orientation of a 3D object."""
    def __init__(self, coordinate_system: CoordinateSystem,
                 *, uid: str=None) -> None:
        self.uid = uid
        if (dimensions := len(coordinate_system)) != 3:
            raise ValueError("Expected 3D coordinate system,"
                             f" got {dimensions}D: {coordinate_system}")
        self._coordinate_system = coordinate_system
        super().__init__(
            {
                ConstraintReference.CORE: self,
                ConstraintReference.ORIGIN: self._coordinate_system.origin,
                ConstraintReference.FRONT: self._coordinate_system.get_xy_plane(),
                ConstraintReference.RIGHT: self._coordinate_system.get_xz_plane(),
                ConstraintReference.TOP: self._coordinate_system.get_yz_plane(),
                ConstraintReference.CS: self._coordinate_system,
            }
        )

    @classmethod
    def from_yaw_pitch_roll(cls, position: Point | VectorLike,
                            yaw: Real=0, pitch: Real=0, roll: Real=0,
                            **kwargs) -> None:
        """Initializes a Pose from yaw, pitch, and roll angles in radians."""
        coordinate_system = CoordinateSystem(position, yaw, pitch, roll)
        return cls(coordinate_system, **kwargs)

    @property
    def coordinate_system(self) -> CoordinateSystem:
        """Internal coordinate_system representing the the Pose."""
        return self.get_reference(ConstraintReference.CS)

    @property
    def origin(self) -> Point:
        """The origin point of the Pose's internal coordinate_system."""
        return self.get_reference(ConstraintReference.ORIGIN)

    @property
    def front(self) -> Plane:
        """Front plane of the Pose."""
        return self.get_reference(ConstraintReference.FRONT)

    @property
    def right(self) -> Plane:
        """Right plane of the Pose."""
        return self.get_reference(ConstraintReference.RIGHT)

    @property
    def top(self) -> Plane:
        """Top plane of the Pose."""
        return self.get_reference(ConstraintReference.TOP)

    def update(self, other: Pose) -> Self:
        """Updates the position and orientation of the Pose to the other Pose."""
        self.coordinate_system.update(other.coordinate_system)
        return self

    def __len__(self) -> int:
        """Returns the number of dimensions of the Pose. Poses are always 3D."""
        return 3

    def __repr__(self) -> str:
        origin = str(tuple(self.origin)).replace(" ", "")
        return super().__repr__().format(details=f"{origin}")

class Sketch(AbstractFeature):
    """A class representing a sketch feature that places a 2D system of 
    geometry/constraints onto a plane in 3D space.
    
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
    CONSTRAINT_GEOMETRY_TYPE_STR = "{0}-{1}"
    """Sets the format of constraint constrained geometry summaries."""

    def __init__(self, system: SketchGeometrySystem, pose: Pose,
                 *, name: str=DEFAULT_NAME, context: AbstractFeature=None,
                 uid: str=None):
        self.uid = uid
        self._pose = pose
        self.name = name
        self._system = system
        system.feature = self
        self.context = context

    # Properties #
    @property
    def pose(self) -> Pose:
        """The location and orientation of the 2D sketch coordinate system."""
        return self._pose
    @pose.setter
    def pose(self, value: Pose) -> None:
        self._pose.update(value)

    @property
    def system(self) -> SketchGeometrySystem:
        """The Sketch's 2D geometry system of geometry/constraint elements."""
        return self._system

    # Public Functions #
    def get_dependencies(self) -> tuple[AbstractGeometry]:
        dependencies = [dep for dep in self.system.get_dependencies()
                        if dep.uid != self.uid]
        if self.context is not None:
            dependencies.append(self.context)
        return dependencies

    # Python Dunders #
    def __repr__(self) -> str:
        """Returns the short string representation of the sketch"""
        return super().__repr__().format(details=f"'{self.name}'")
