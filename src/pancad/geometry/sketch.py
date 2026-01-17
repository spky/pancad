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
from pancad.geometry.unique_lists import FeatureGeometryList
from pancad.geometry.system import TwoDSketchSystem
from pancad.utils.initialize import get_pancad_config
from pancad.utils.geometry import two_dimensions_required
from pancad.utils.pancad_types import VectorLike

if TYPE_CHECKING:
    from uuid import UUID
    from numbers import Real
    from collections.abc import Sequence
    from typing import Self

    from pancad.abstract import (
        AbstractConstraint, PancadThing, AbstractFeatureSystem
    )
    from pancad.geometry.line import Line
    from pancad.geometry.plane import Plane
    from pancad.geometry.point import Point

DEFAULT_NAME = get_pancad_config()["features"]["default_names"]["sketch"]

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
    
    :param system: The system of features containing the Sketch.
    :param pose: The location and orientation of the Sketch.
    :param geometry_system: The 
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

    def __init__(self, geometry_system: TwoDSketchSystem, pose: Pose,
                 *,
                 system: AbstractFeatureSystem=None,
                 name: str=DEFAULT_NAME,
                 uid: str=None):
        super().__init__(system, name)
        self.uid = uid
        self._pose = pose
        self._geometry_system = geometry_system
        self._feature_geometry = FeatureGeometryList(
            self, [self._pose, self._geometry_system]
        )

    # Properties #
    @property
    def pose(self) -> Pose:
        """The location and orientation of the 2D sketch coordinate system."""
        return self._pose
    @pose.setter
    def pose(self, value: Pose) -> None:
        self._pose.update(value)

    @property
    def feature_geometry(self) -> FeatureGeometryList:
        """The geometry directly owned by this Sketch."""
        return self._feature_geometry

    @property
    def geometry_system(self) -> TwoDSketchSystem:
        """The Sketch's 2D geometry system of geometry/constraint elements."""
        return self._geometry_system

    # Public Functions #
    def get_dependencies(self) -> tuple[AbstractFeature]:
        dependencies = [dep for dep in self.geometry_system.get_dependencies()
                        if dep.uid != self.uid]
        if self.system is not None:
            dependencies.append(self.system)
        return dependencies

    # Python Dunders #
    def __repr__(self) -> str:
        """Returns the short string representation of the sketch"""
        return super().__repr__().format(details=f"'{self.name}'")
