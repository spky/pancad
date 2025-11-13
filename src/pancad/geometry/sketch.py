"""A module providing a class to represent sketches in 3D space. pancad defines a 
sketch as a set of 2D geometry on a coordinate system's plane oriented in 3D 
space. pancad's sketch definition aims to be as general as possible, so the 
base implementation of this class does not include appearance information since 
that is application specific.
"""
from __future__ import annotations

from functools import reduce, singledispatchmethod
from itertools import compress
from math import degrees
from typing import TYPE_CHECKING, overload, Self, NoReturn

from pancad.geometry import (
    AbstractFeature,
    AbstractGeometry,
    Circle,
    CircularArc,
    CoordinateSystem,
    Ellipse,
    Point,
    Line,
    LineSegment,
)
from pancad.geometry.constants import SketchConstraint, ConstraintReference
from pancad.geometry.constraints import (
    Abstract1GeometryDistance,
    Abstract2GeometryDistance,
    AbstractStateConstraint,
    AbstractSnapTo,
    Angle,
    make_constraint,
)
from pancad.utils.text_formatting import get_table_string

if TYPE_CHECKING:
    from uuid import UUID
    from collections.abc import Sequence
    
    from pancad.geometry import Plane
    from pancad.geometry.constraints import AbstractConstraint

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
    
    PLANE_OPTIONS = (ConstraintReference.XY,
                     ConstraintReference.XZ,
                     ConstraintReference.YZ)
    """Allowable ConstraintReferences for the sketch's plane_reference."""
    
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
                 name: str=None,
                 context: AbstractFeature=None,):
        # Initialize private uid since uid and geometry sync with each other
        self.uid = uid
        self._constraints = tuple()
        self._geometry = tuple()
        self._construction = tuple()
        
        if geometry is None:
            geometry = tuple()
        if constraints is None:
            constraints = tuple()
        if externals is None:
            externals = tuple()
        if construction is None:
            construction = tuple([False] * len(geometry))
        
        self._sketch_cs = CoordinateSystem((0, 0), context=self)
        
        self.coordinate_system = coordinate_system
        
        for geometry_element, is_construction in zip(geometry, construction):
            self.add_geometry(geometry_element, is_construction)
        
        self.externals = externals
        self.plane_reference = plane_reference
        self.constraints = constraints
        self.name = name
        self.context = context
    
    # Getters #
    @property
    def constraints(self) -> tuple[AbstractConstraint]:
        """The tuple of constraints on sketch geometry.
        
        :getter: Returns a tuple of the sketch's constraints.
        :setter: Sets the sketch's constraints after checking that the 
            constraints refer to geometry that is already available in the 
            sketch.
        """
        return self._constraints
    
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
    
    @property
    def context(self) -> AbstractFeature | None:
        return self._context
    
    @property
    def coordinate_system(self) -> CoordinateSystem:
        """The contextual coordinate system that positions and rotates the 
        2D sketch geometry.
        
        :getter: Returns the CoordinateSystem object.
        :setter: Sets the coordinate system.
        """
        return self._coordinate_system
    
    @property
    def externals(self) -> tuple[AbstractGeometry]:
        """The 3D external geometry referenced by the sketch.
        
        :getter: Returns the tuple of external geometry references.
        :setter: Sets the externals tuple after checking that all of the tuple 
            is 3D.
        """
        return self._externals
    
    @property
    def geometry(self) -> tuple[AbstractGeometry]:
        """The 2D geometry in the sketch.
        
        :getter: Returns the tuple of geometry in the sketch.
        :setter: Sets the tuple of geometry in the sketch after checking the new
            lists' validity. Geometry set this way is assumed to always be 
            non-construction.
        """
        return self._geometry
    
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
        return self._plane_reference
    
    # Setters #
    @coordinate_system.setter
    def coordinate_system(self, coordinate_system: CoordinateSystem) -> None:
        self._coordinate_system = coordinate_system
    
    @constraints.setter
    def constraints(self, constraints: Sequence[AbstractConstraint]) -> None:
        for c in constraints:
            self.add_constraint(c)
    
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
    
    @context.setter
    def context(self, context_feature: AbstractFeature | None) -> None:
        self._context = context_feature
    
    @externals.setter
    def externals(self, externals: Sequence[AbstractGeometry]) -> None:
        non_3d_externals = list(
            filter(lambda g: len(g) != 3, externals)
        )
        if non_3d_externals != []:
            raise ValueError(f"3D Geometry only, 2D: {non_3d_externals}")
        else:
            self._externals = tuple(externals)
    
    @geometry.setter
    def geometry(self, geometry: Sequence[AbstractGeometry]) -> None:
        non_2d_geometry = list(
            filter(lambda g: len(g) != 2, geometry)
        )
        if non_2d_geometry != []:
            raise ValueError(f"2D Geometry only, given 3D: {non_2d_geometry}")
        else:
            for g in geometry:
                self.add_geometry(g)
    
    @plane_reference.setter
    def plane_reference(self, reference: ConstraintReference):
        if reference in self.PLANE_OPTIONS:
            self._plane_reference = reference
        else:
            raise ValueError(f"{reference} not recognized as a plane reference,"
                             f"must be one of {list(self.PLANE_OPTIONS)}")
    
    # Public Functions #
    def add_constraint(self, constraint: AbstractConstraint) -> Self:
        """Adds an already generated constraint to the sketch. Sets the 
        constraint's context to the Sketch.
        
        :param constraint: A constraint referring to geometry that is already in 
            the sketch.
        :returns: The updated sketch.
        :raises LookupError: Raised when the constraint's dependencies are not in 
            the sketch.
        """
        dependencies = constraint.get_constrained()
        if all([d in self for d in dependencies]):
            constraint.context = self
            self._constraints = self._constraints + (constraint,)
            return self
        else:
            missing = filter(lambda d: d not in self, dependencies)
            raise LookupError(f"Dependencies for {repr(constraint)} are missing"
                             f" from sketch: {list(missing)}")
    
    @overload
    def add_constraint_by_uid(self,
                              sketch_constraint: SketchConstraint,
                              uid_a: str | UUID,
                              reference_a: ConstraintReference,
                              **kwargs) -> Self: ...
    
    @overload
    def add_constraint_by_uid(self,
                              sketch_constraint: SketchConstraint,
                              uid_a: str | UUID,
                              reference_a: ConstraintReference,
                              uid_b: str | UUID=None,
                              reference_b: ConstraintReference=None,
                              **kwargs) -> Self: ...
    
    @overload
    def add_constraint_by_uid(self,
                              sketch_constraint: SketchConstraint,
                              uid_a: str | UUID,
                              reference_a: ConstraintReference,
                              uid_b: str | UUID=None,
                              reference_b: ConstraintReference=None,
                              uid_c: str | UUID=None,
                              reference_c: ConstraintReference=None,
                              **kwargs) -> Self: ...
    
    def add_constraint_by_uid(
                self, sketch_constraint, uid_a, reference_a,
                uid_b=None, reference_b=None, uid_c=None, reference_c=None,
                **kwargs
            ) -> Self:
        """Adds a sketch constraint between two geometry elements selected by 
        their uids. Prefixes the new constraint's uid with the sketch's uid. All 
        geometry must already be in the sketch's geometry.
        :attr:`~pancad.geometry.constants.ConstraintReference.CS` can be used 
        instead of any of the uid inputs to refer to the sketch's coordinate 
        system.
        
        :param sketch_constraint: The SketchConstraint for the type of 
            constraint to be added.
        :param uid_a: The uid of geometry a.
        :param reference_a: The ConstraintReference to part of geometry a.
        :param uid_b: The uid of geometry b. Only supplied for constraints 
            that require 2 or 3 geometry elements (e.g. coincident, parallel).
        :param reference_b: The ConstraintReference to part of geometry b
        :param uid_c: The uid of geometry c. Only supplied for constraints 
            requiring 3 geometry elements (i.e. symmetry).
        :param reference_c: The ConstraintReference to part of geometry c. The 
            uid of geometry c. Only supplied for constraints requiring 3 
            geometry elements (i.e. symmetry).
        :returns: The updated sketch.
        """
        geometry_a = self.get_geometry_by_uid(uid_a)
        geometry_b = self.get_geometry_by_uid(uid_b)
        geometry_c = self.get_geometry_by_uid(uid_c)
        constraint = make_constraint(sketch_constraint,
                                     geometry_a, reference_a,
                                     geometry_b, reference_b,
                                     geometry_c, reference_c,
                                     **kwargs)
        self.add_constraint(constraint)
        return self
    
    @overload
    def add_constraint_by_index(self,
                                sketch_constraint: SketchConstraint,
                                index_a: int,
                                reference_a: ConstraintReference,
                                **kwargs) -> Self: ...
    
    @overload
    def add_constraint_by_index(self,
                                sketch_constraint: SketchConstraint,
                                index_a: int,
                                reference_a: ConstraintReference,
                                index_b: int=None,
                                reference_b: ConstraintReference=None,
                                **kwargs) -> Self: ...
    
    @overload
    def add_constraint_by_index(self,
                                sketch_constraint: SketchConstraint,
                                index_a: int,
                                reference_a: ConstraintReference,
                                index_b: int=None,
                                reference_b: ConstraintReference=None,
                                index_c: int=None,
                                reference_c: ConstraintReference=None,
                                **kwargs) -> Self: ...
    
    def add_constraint_by_index(
                self, sketch_constraint, index_a, reference_a,
                index_b=None, reference_b=None, index_c=None, reference_c=None,
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
        :param index_a: The index of geometry a.
        :param reference_a: The ConstraintReference to part of geometry a.
        :param index_b: The index of geometry b. Only required for constraints 
            that require 2 or 3 geometry elements (e.g. coincident, parallel).
        :param reference_b: The ConstraintReference to part of geometry b. 
            Required if index_b is provided.
        :param index_c: The index of geometry c. Only required for constraints 
            requiring 3 geometry elements (i.e. symmetry).
        :param reference_c: The ConstraintReference to part of geometry c. 
            Required if index_c is provided.
        :returns: The updated sketch.
        """
        geometry_a = self._get_geometry_by_index(index_a)
        geometry_b = self._get_geometry_by_index(index_b)
        geometry_c = self._get_geometry_by_index(index_c)
        constraint = make_constraint(sketch_constraint,
                                     geometry_a, reference_a,
                                     geometry_b, reference_b,
                                     geometry_c, reference_c,
                                     **kwargs)
        self.add_constraint(constraint)
        return self
    
    def add_geometry(self,
                     geometry: AbstractGeometry,
                     construction: bool=False) -> Self:
        """Adds an already generated geometry element to the sketch. Sets the 
        geometry's context to the Sketch.
        
        :param geometry: A 2D geometry element.
        :param construction: Whether the geometry is construction. Defaults to 
            'False'.
        :returns: The updated sketch.
        """
        if len(geometry) != 2:
            raise ValueError(f"2D Geometry only, given 3D: {geometry}")
        geometry.context = self
        self._geometry = self._geometry + (geometry,)
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
        else:
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
        elif uid == self.uid:
            return self
        elif uid is None:
            return None
        else:
            raise ValueError(f"uid '{uid}' was not found in sketch's geometry")
    
    def get_index_of(self,
                     item: AbstractGeometry | AbstractConstraint | Sketch
                     ) -> int:
        """Returns the index of a geometry, external, or constraint item in 
        their respective tuples. Returns -1 if it's the sketch itself.
        
        :raises LookupError: Raised if the item is not in the sketch geometry, 
            externals, or constraints.
        """
        if any([item is g for g in self.geometry]):
            return [item is g for g in self.geometry].index(True)
        elif any([item is c for c in self.constraints]):
            return [item is c for c in self.constraints].index(True)
        elif any([item is g for g in self.externals]):
            return [item is g for g in self.externals].index(True)
        elif item is self:
            return -1
        else:
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
        match reference:
            case ConstraintReference.CORE:
                return self
            case (ConstraintReference.ORIGIN
                    | ConstraintReference.X
                    | ConstraintReference.Y):
                return self._sketch_cs.get_reference(reference)
            case _:
                raise ValueError(f"{self.__class__}s do not have any"
                                 f" {reference.name} reference geometry")
    
    def get_sketch_coordinate_system(self) -> CoordinateSystem:
        """Returns the sketch's 2D coordinate system."""
        return self._sketch_cs
    
    def update(self, other: Sketch) -> Self:
        """Updates the origin, axes, planes and context of the Sketch to match 
        another Sketch. Does not directly modify the geometry inside the sketch.
        
        :param other: The Sketch to update to.
        :returns: The updated Sketch.
        """
        self._sketch_cs = other._sketch_cs.copy()
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
        elif index is None:
            return None
        else:
            return self.geometry[index]
    
    def _generate_summary(self, title_to_type: dict, element_list: list) -> str:
        """Returns a string summarizing a list of classes of geometry or 
        constraints in table format.
        """
        from textwrap import indent
        summary_strings = []
        UID_KEYS = ["UID", "a UID", "b UID"]
        for title, type_ in title_to_type.items():
            info = []
            for e in filter(lambda e: isinstance(e, type_), element_list):
                element_info = self._get_summary_info(e)
                if not self.STR_VERBOSE:
                    element_info = {k: v for k, v in element_info.items()
                                    if k not in UID_KEYS}
                info.append(element_info)
            if len(info) > 0:
                summary_strings.append(title)
                summary_strings.append(
                    indent(get_table_string(info), "  ")
                )
        summary = "\n".join(summary_strings)
        summary = indent(summary, "  ")
        return summary
    
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
    
    def _validate_constraint_references(self, constraint) -> None:
        """Checks whether a constraint references geometry in the sketch's 
        geometry or externals"""
        references = constraint.get_constrained()
        if not all([self.has_geometry(g) for g in references]):
            raise ValueError(f"The {repr(constraint)} constraint references"
                             " geometry that is not in the sketch."
                             f"\nAll Geometry: {references}")
    
    # Private Dispatch Methods
    @singledispatchmethod
    def _get_summary_info(
                self, geometry: AbstractGeometry | AbstractConstraint
            ) -> NoReturn:
        """Returns the summary info for a given geometry type."""
        raise TypeError(f"{geometry.__class__} not recognized")
    
    @_get_summary_info.register
    def _circle(self, geometry: Circle) -> dict:
        return {"Index": self.get_index_of(geometry),
                "UID": geometry.uid,
                "Center": geometry.center.cartesian,
                "Radius": geometry.radius,
                "Construction": self.construction[self.get_index_of(geometry)]}
    
    @_get_summary_info.register
    def _circular_arc(self, geometry: CircularArc) -> dict:
        return {
            "Index": self.get_index_of(geometry),
            "UID": geometry.uid,
            "Center": geometry.center.cartesian,
            "Radius": geometry.radius,
            "Start": geometry.start.cartesian,
            "End": geometry.end.cartesian,
            "Is Clockwise": geometry.is_clockwise,
            "Construction": self.construction[self.get_index_of(geometry)],
        }
    
    @_get_summary_info.register
    def _ellipse(self, geometry: Ellipse) -> dict:
        return {"Index": self.get_index_of(geometry),
                "UID": geometry.uid,
                "Center": geometry.center.cartesian,
                "Semi-Major Axis Length": geometry.semi_major_axis,
                "Semi-Minor Axis Length": geometry.semi_minor_axis,
                "Semi-Major Axis Angle": degrees(geometry.major_axis_angle),
                "Construction": self.construction[self.get_index_of(geometry)]}
    
    @_get_summary_info.register
    def _line(self, geometry: Line) -> dict:
        return {"Index": self.get_index_of(geometry),
                "UID": geometry.uid,
                "X-Intercept": (geometry.x_intercept, 0),
                "Y-Intercept": (0, geometry.y_intercept),
                "Construction": self.construction[self.get_index_of(geometry)]}
    
    @_get_summary_info.register
    def _line_segment(self, geometry: LineSegment) -> dict:
        return {"Index": self.get_index_of(geometry),
                "UID": geometry.uid,
                "Start": geometry.point_a.cartesian,
                "End": geometry.point_b.cartesian,
                "Construction": self.construction[self.get_index_of(geometry)]}
    
    @_get_summary_info.register
    def _point(self, geometry: Point) -> dict:
        return {"Index": self.get_index_of(geometry),
                "UID": geometry.uid,
                "Location": geometry.cartesian,
                "Construction": self.construction[self.get_index_of(geometry)]}
    
    @_get_summary_info.register
    def _state_constraint(self, constraint: AbstractStateConstraint) -> dict:
        geometry_a, geometry_b = constraint.get_constrained()
        reference_a, reference_b = constraint.get_references()
        return {"Index": self.get_index_of(constraint),
                "Type": constraint.__class__.__name__,
                "a Index": self.get_index_of(geometry_a),
                "a UID": geometry_a.uid,
                "a Type": self.CONSTRAINT_GEOMETRY_TYPE_STR.format(
                    geometry_a.__class__.__name__,
                    reference_a.name.title(),
                ),
                "b Index": self.get_index_of(geometry_b),
                "b UID": geometry_b.uid,
                "b Type": self.CONSTRAINT_GEOMETRY_TYPE_STR.format(
                    geometry_b.__class__.__name__,
                    reference_b.name.title()
                )}
    
    @_get_summary_info.register
    def _state_constraint(self, constraint: AbstractSnapTo) -> dict:
        geometry = constraint.get_constrained()
        references = constraint.get_references()
        if len(geometry) == 1:
            geometry_a = geometry[0]
            reference_a = references[0]
            return {
                "Index": self.get_index_of(constraint),
                "Type": constraint.__class__.__name__,
                "a Index": self.get_index_of(geometry_a),
                "a UID": geometry_a.uid,
                "a Type": self.CONSTRAINT_GEOMETRY_TYPE_STR.format(
                    geometry_a.__class__.__name__,
                    reference_a.name.title()
                ),
                "b Index": None,
                "b UID": None,
                "b Type": None,
            }
        else:
            geometry_a, geometry_b = geometry
            reference_a, reference_b = references
            return {
                "Index": self.get_index_of(constraint),
                "Type": constraint.__class__.__name__,
                "a Index": self.get_index_of(geometry_a),
                "a UID": geometry_a.uid,
                "a Type": self.CONSTRAINT_GEOMETRY_TYPE_STR.format(
                    geometry_a.__class__.__name__,
                    reference_a.name.title()
                ),
                "b Index": self.get_index_of(geometry_b),
                "b UID": geometry_b.uid,
                "b Type": self.CONSTRAINT_GEOMETRY_TYPE_STR.format(
                    geometry_b.__class__.__name__,
                    reference_b.name.title()
                ),
            }
    
    @_get_summary_info.register
    def _1_geo_distance(self, constraint: Abstract1GeometryDistance) -> dict:
        geometry_a = constraint.get_constrained()[0]
        reference_a = constraint.get_references()[0]
        return {
            "Index": self.get_index_of(constraint),
            "Type": constraint.__class__.__name__,
            "a Index": self.get_index_of(geometry_a),
            "a UID": geometry_a.uid,
            "a Type": self.CONSTRAINT_GEOMETRY_TYPE_STR.format(
                geometry_a.__class__.__name__,
                reference_a.name.title()
            ),
            "Value": constraint.get_value_string(),
        }
    
    @_get_summary_info.register
    def _2_geo_distance(self, constraint: Abstract2GeometryDistance) -> dict:
        geometry_a, geometry_b = constraint.get_constrained()
        reference_a, reference_b = constraint.get_references()
        return {
            "Index": self.get_index_of(constraint),
            "Type": constraint.__class__.__name__,
            "a Index": self.get_index_of(geometry_a),
            "a UID": geometry_a.uid,
            "a Type": self.CONSTRAINT_GEOMETRY_TYPE_STR.format(
                geometry_a.__class__.__name__,
                reference_a.name.title()
            ),
            "b Index": self.get_index_of(geometry_b),
            "b UID": geometry_b.uid,
            "b Type": self.CONSTRAINT_GEOMETRY_TYPE_STR.format(
                geometry_b.__class__.__name__,
                reference_b.name.title()
            ),
            "Value": constraint.get_value_string(),
        }
    
    @_get_summary_info.register
    def _angle(self, constraint: Angle) -> dict:
        geometry_a, geometry_b = constraint.get_constrained()
        reference_a, reference_b = constraint.get_references()
        return {
            "Index": self.get_index_of(constraint),
            "a Index": self.get_index_of(geometry_a),
            "a UID": geometry_a.uid,
            "a Type": self.CONSTRAINT_GEOMETRY_TYPE_STR.format(
                geometry_a.__class__.__name__,
                reference_a.name.title()
            ),
            "b Index": self.get_index_of(geometry_b),
            "b UID": geometry_b.uid,
            "b Type": self.CONSTRAINT_GEOMETRY_TYPE_STR.format(
                geometry_b.__class__.__name__,
                reference_b.name.title()
            ),
            "Value": constraint.get_value_string(),
            "Quadrant": constraint.quadrant,
        }
    
    # Python Dunders #
    def __copy__(self) -> Sketch:
        raise NotImplementedError("Sketch copy hasn't been implemented yet,"
                                  " see github issue #53")
    
    def __contains__(self, item: AbstractGeometry):
        contents = [geometry.uid for geometry in self.geometry]
        contents.append(self.uid)
        return item.uid in contents
    
    def __len__(self) -> int:
        """Returns the number of dimensions of the sketch's contextual 
        coordinate system"""
        return len(self.coordinate_system)
    
    def __repr__(self) -> str:
        """Returns the short string representation of the sketch"""
        return f"<Sketch'{self.name}'>"
    
    def __str__(self) -> str:
        """Returns the longer string representation of the sketch"""
        from textwrap import indent
        sketch_summary = []
        sketch_summary.append(f"Sketch '{self.name}'")
        if self.STR_VERBOSE:
            sketch_summary.append(indent(f"Sketch uid: {self.uid}", "  "))
        
        # Location/Plane Summary
        sketch_summary.append(
            indent(self._generate_location_string(), "  ")
        )
        # Geometry Summary #
        sketch_summary.append("Geometry")
        summaries = {
            "Circles": Circle,
            "Circular Arcs": CircularArc,
            "Ellipses": Ellipse,
            "Line Segments": LineSegment,
            "Infinite Lines": Line,
            "Points": Point,
        }
        sketch_summary.append(
            self._generate_summary(summaries, self.geometry)
        )
        
        # Constraint Summary #
        sketch_summary.append("Constraints")
        summaries = {
            "State Constraints": AbstractStateConstraint,
            "Snap To Constraints": AbstractSnapTo,
            "Distance Constraints": Abstract2GeometryDistance,
            "Radius and Diameter Constraints": Abstract1GeometryDistance,
            "Angle Constraints": Angle,
        }
        sketch_summary.append(
            self._generate_summary(summaries, self.constraints)
        )
        sketch_summary.append(self._generate_quantity_string())
        return "\n".join(sketch_summary)