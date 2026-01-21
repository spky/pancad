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
from pancad.geometry.coordinate_system import Pose
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



class Sketch(AbstractFeature):
    """A class representing a sketch feature that places a 2D system of 
    geometry/constraints onto a plane in 3D space.
    
    :param geometry_system: The TwoDSketchSystem containing the geometry and 
        constraints inside the Sketch.
    :param pose: The location and orientation of the Sketch.
    :param system: The feature system that the Sketch's pose is defined in.
    :param name: The name of the Sketch that will be used wherever a CAD 
        application requires a human-readable name for the sketch element.
    :param uid: The unique id of the Sketch. Defaults to None.
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
        """The geometry directly owned by this Sketch. Usually its Pose and 
        GeometrySystem.
        """
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
            dependencies.append(self.system.feature)
        return dependencies

    # Python Dunders #
    def __repr__(self) -> str:
        """Returns the short string representation of the sketch"""
        return super().__repr__().format(details=f"'{self.name}'")
