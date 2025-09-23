"""A module providing a class to represent sketches in 3D space. PanCAD defines a 
sketch as a set of 2D geometry on a coordinate system's plane oriented in 3D 
space. PanCAD's sketch definition aims to be as general as possible, so the 
base implementation of this class does not include appearance information since 
that is application specific.
"""

from __future__ import annotations

from collections.abc import Sequence
from functools import reduce, singledispatchmethod
from itertools import compress
from math import degrees
from typing import overload, Self, NoReturn

from PanCAD.geometry import (
    AbstractFeature, AbstractGeometry,
    Circle, CoordinateSystem, Ellipse, Point, Line, LineSegment, Plane,
)
from PanCAD.geometry.constants import SketchConstraint, ConstraintReference
from PanCAD.geometry.constraints import (
    AbstractConstraint,
    Abstract1GeometryDistance, Abstract2GeometryDistance,
    AbstractStateConstraint, AbstractSnapTo,
    Coincident, Vertical, Horizontal, Equal, Parallel, Perpendicular,
    Angle, Distance,
    HorizontalDistance, VerticalDistance,
    Diameter, Radius,
)
from PanCAD.utils.text_formatting import get_table_string

class Sketch(AbstractFeature, AbstractGeometry):
    """A class representing a set of 2D geometry placed onto a coordinate system 
    plane in 3D space.
    
    :param coordinate_system: A coordinate system defining the sketch's position 
        and orientation. Defaults to an unrotated coordinate system centered at 
        (0, 0, 0).
    :param plane_reference: The ConstraintReference to one of the 
        coordinate_system's planes. Defaults to
        :attr:`~PanCAD.geometry.constants.ConstraintReference.XY`.
    :param geometry: A sequence of 2D PanCAD geometry. Defaults to an empty 
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
    """
    # Class Constants
    REFERENCES = (ConstraintReference.ORIGIN,
                  ConstraintReference.X,
                  ConstraintReference.Y)
    
    PLANE_OPTIONS = (ConstraintReference.XY,
                     ConstraintReference.XZ,
                     ConstraintReference.YZ)
    """Allowable ConstraintReferences for the sketch's plane_reference."""
    
    # Type Tuples for checking with isinstance()
    GEOMETRY_TYPES = (Circle, Ellipse, Line, LineSegment, Point)
    EXTERNAL_TYPES = (Circle, CoordinateSystem, Ellipse,
                      Line, LineSegment, Point, Plane)
    CONSTRAINT_TYPES = (Coincident, Vertical, Horizontal,
                        Equal, Parallel, Perpendicular,
                        Angle, Distance, Diameter, Radius,
                        HorizontalDistance, VerticalDistance)
    
    # Type Hints
    GeometryType = reduce(lambda x, y: x | y, GEOMETRY_TYPES)
    """Allowed sketch geometry types."""
    ExternalType = reduce(lambda x, y: x | y, EXTERNAL_TYPES)
    """Allowed external geometry types."""
    ConstraintType = reduce(lambda x, y: x | y, CONSTRAINT_TYPES)
    """Allowed constraint types."""
    
    def __init__(self,
                 coordinate_system: CoordinateSystem=None,
                 plane_reference: ConstraintReference=ConstraintReference.XY,
                 geometry: Sequence[GeometryType]=None,
                 construction: Sequence[bool]=None,
                 constraints: Sequence[ConstraintType]=None,
                 externals: Sequence[ExternalType]=None,
                 uid: str=None,
                 name: str=None,
                 context: AbstractFeature=None,):
        # Initialize private uid since uid and geometry sync with each other
        self.uid = uid
        self._constraints = tuple()
        
        if geometry is None:
            geometry = tuple()
        if constraints is None:
            constraints = tuple()
        if externals is None:
            externals = tuple()
        
        self._sketch_cs = CoordinateSystem((0, 0), context=self)
        
        self.coordinate_system = coordinate_system
        # if coordinate_system is None:
            # self.coordinate_system = CoordinateSystem()
        # else:
            # self.coordinate_system = coordinate_system
            
        self.geometry = geometry
        self.externals = externals
        self.construction = construction
        self.plane_reference = plane_reference
        self.constraints = constraints
        self.name = name
        self.context = context
    
    # Getters #
    @property
    def constraints(self) -> tuple[ConstraintType]:
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
    def externals(self) -> tuple[ExternalType]:
        """The 3D external geometry referenced by the sketch.
        
        :getter: Returns the tuple of external geometry references.
        :setter: Sets the externals tuple after checking that all of the tuple 
            is 3D.
        """
        return self._externals
    
    @property
    def geometry(self) -> tuple[GeometryType]:
        """The 2D geometry in the sketch.
        
        :getter: Returns the tuple of geometry in the sketch.
        :setter: Sets the tuple of geometry in the sketch after checking the new
            lists' validity.
        """
        return self._geometry
    
    @property
    def plane_reference(self) -> ConstraintReference:
        """The ConstraintReference for the CoordinateSystem plane that contains 
        the sketch's geometry. Must be one of the enumeration values in 
        :class:`~PanCAD.geometry.constants.ConstraintReference`.
        
        :getter: Returns the reference of the plane.
        :setter: Checks reference validity and then sets the plane reference.
        """
        return self._plane_reference
    
    # Setters #
    @coordinate_system.setter
    def coordinate_system(self, coordinate_system: CoordinateSystem) -> None:
        self._coordinate_system = coordinate_system
    
    @constraints.setter
    def constraints(self, constraints: Sequence[ConstraintType]) -> None:
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
    def externals(self, externals: Sequence[ExternalType]) -> None:
        non_3d_externals = list(
            filter(lambda g: len(g) != 3, externals)
        )
        if non_3d_externals != []:
            raise ValueError(f"3D Geometry only, 2D: {non_3d_externals}")
        else:
            self._externals = tuple(externals)
    
    @geometry.setter
    def geometry(self, geometry: Sequence[GeometryType]) -> None:
        non_2d_geometry = list(
            filter(lambda g: len(g) != 2, geometry)
        )
        if non_2d_geometry != []:
            raise ValueError(f"2D Geometry only, given 3D: {non_2d_geometry}")
        else:
            self._geometry = tuple(geometry)
    
    @plane_reference.setter
    def plane_reference(self, reference: ConstraintReference):
        if reference in self.PLANE_OPTIONS:
            self._plane_reference = reference
        else:
            raise ValueError(f"{reference} not recognized as a plane reference,"
                             f"must be one of {list(self.PLANE_OPTIONS)}")
    
    # Public Functions #
    def add_constraint(self, constraint: ConstraintType) -> Self:
        """Adds an already generated constraint to the sketch.
        
        :param constraint: A constraint referring to geometry that is already in 
            the sketch.
        :returns: The updated sketch.
        """
        dependencies = constraint.get_constrained()
        if all([d in self for d in dependencies]):
            self._constraints = self._constraints + (constraint,)
            return self
        else:
            missing = filter(lambda d: d not in self, dependencies)
            raise LookupError(f"Dependencies for {repr(constraint)} are missing"
                             f" from part: {list(missing)}")
    
    @overload
    def add_constraint_by_uid(self,
                              sketch_constraint: SketchConstraint,
                              uid_a: str | ConstraintReference,
                              reference_a: ConstraintReference,
                              **kwargs) -> Self: ...
    
    @overload
    def add_constraint_by_uid(self,
                              sketch_constraint: SketchConstraint,
                              uid_a: str | ConstraintReference,
                              reference_a: ConstraintReference,
                              uid_b: str | ConstraintReference=None,
                              reference_b: ConstraintReference=None,
                              **kwargs) -> Self: ...
    
    @overload
    def add_constraint_by_uid(self,
                              sketch_constraint: SketchConstraint,
                              uid_a: str | ConstraintReference,
                              reference_a: ConstraintReference,
                              uid_b: str | ConstraintReference=None,
                              reference_b: ConstraintReference=None,
                              uid_c: str | ConstraintReference=None,
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
        :attr:`~PanCAD.geometry.constants.ConstraintReference.CS` can be used 
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
        self._add_new_constraint(sketch_constraint,
                                 geometry_a, reference_a,
                                 geometry_b, reference_b,
                                 geometry_c, reference_c,
                                 **kwargs)
        return self
    
    @overload
    def add_constraint_by_index(self,
                                sketch_constraint: SketchConstraint,
                                index_a: int | ConstraintReference,
                                reference_a: ConstraintReference,
                                **kwargs) -> Self: ...
    
    @overload
    def add_constraint_by_index(self,
                                sketch_constraint: SketchConstraint,
                                index_a: int | ConstraintReference,
                                reference_a: ConstraintReference,
                                index_b: int | ConstraintReference=None,
                                reference_b: ConstraintReference=None,
                                **kwargs) -> Self: ...
    
    @overload
    def add_constraint_by_index(self,
                                sketch_constraint: SketchConstraint,
                                index_a: int | ConstraintReference,
                                reference_a: ConstraintReference,
                                index_b: int | ConstraintReference=None,
                                reference_b: ConstraintReference=None,
                                index_c: int | ConstraintReference=None,
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
        :attr:`~PanCAD.geometry.constants.ConstraintReference.CS` can be used 
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
        
        self._add_new_constraint(sketch_constraint,
                                 geometry_a, reference_a,
                                 geometry_b, reference_b,
                                 geometry_c, reference_c,
                                 **kwargs)
        return self
    
    def add_geometry(self,
                     geometry: GeometryType,
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
    
    def get_construction_geometry(self) -> tuple[GeometryType]:
        """Returns the sketch's construction geometry."""
        return tuple(compress(self.geometry, self.construction))
    
    def get_dependencies(self) -> tuple[ExternalType]:
        if self.coordinate_system is None:
            return self.externals
        else:
            return (self.coordinate_system,) + self.externals
    
    def get_geometry_by_uid(self,
                            uid: str | ConstraintReference) -> GeometryType:
        """Returns a sketch geometry element based on its uid.
        
        :param uid: The uid of the geometry or
            :attr:`~PanCAD.geometry.constants.ConstraintReference.CS` to 
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
                     item: GeometryType | ExternalType | ConstraintType | Sketch
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
    
    def get_non_construction_geometry(self) -> tuple[GeometryType]:
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
        return self._sketch_cs.get_reference(reference)
    
    def get_sketch_coordinate_system(self) -> CoordinateSystem:
        """Returns the sketch's 2D coordinate system."""
        return self._sketch_cs
    
    def has_geometry(self, geometry: GeometryType) -> bool:
        """Checks whether the given geometry is in the sketch's geometry 
        tuple. Compares memory locations, not just equality.
        
        :param geometry: The geometry element to check for.
        :returns: Whether the element is in the sketch geometry.
        """
        constrainable_geometry = (self._sketch_cs,) + self.geometry
        return any(geometry is cg for cg in constrainable_geometry)
    
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
    def _get_geometry_by_index(self, index: int | None) -> GeometryType | None:
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
        for title, type_ in title_to_type.items():
            info = []
            for e in filter(lambda e: isinstance(e, type_), element_list):
                info.append(self._get_summary_info(e))
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
            system_uid = None
        else:
            system_uid = self.coordinate_system.uid
        location_str = (f"On the {self.plane_reference.name} plane"
                        f" in coordinate system  with uid '{system_uid}'")
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
    
    def _add_new_constraint(
                self, constraint_choice: SketchConstraint,
                a: GeometryType, reference_a: ConstraintReference,
                b: GeometryType=None, reference_b: ConstraintReference=None,
                c: GeometryType=None, reference_c: ConstraintReference=None,
                **kwargs
            ) -> None:
        """Adds a new constraint to the constraint tuple. Assumes that a, b, and 
        c are in the geometry tuple and has been checked before calling this 
        private function.
        """
        
        match constraint_choice:
            case SketchConstraint.ANGLE:
                new_constraint = Angle(a, reference_a, b, reference_b, **kwargs)
            case SketchConstraint.COINCIDENT:
                new_constraint = Coincident(a, reference_a, b, reference_b,)
            case SketchConstraint.HORIZONTAL:
                new_constraint = Horizontal(a, reference_a, b, reference_b,)
            case SketchConstraint.DISTANCE:
                new_constraint = Distance(a, reference_a,
                                          b, reference_b, **kwargs)
            case SketchConstraint.DISTANCE_DIAMETER:
                new_constraint = Diameter(a, reference_a, **kwargs)
            case SketchConstraint.DISTANCE_HORIZONTAL:
                new_constraint = HorizontalDistance(a, reference_a,
                                                    b, reference_b, **kwargs)
            case SketchConstraint.DISTANCE_RADIUS:
                new_constraint = Radius(a, reference_a, **kwargs)
            case SketchConstraint.DISTANCE_VERTICAL:
                new_constraint = VerticalDistance(
                    a, reference_a, b, reference_b, **kwargs
                )
            case SketchConstraint.EQUAL:
                new_constraint = Equal(a, reference_a, b, reference_b,)
            case SketchConstraint.PARALLEL:
                new_constraint = Parallel(a, reference_a, b, reference_b,)
            case SketchConstraint.PERPENDICULAR:
                new_constraint = Perpendicular(a, reference_a, b, reference_b,)
            case SketchConstraint.SYMMETRIC:
                raise NotImplementedError("Symmetric not yet implemented, #85")
            case SketchConstraint.TANGENT:
                raise NotImplementedError("Tangent not yet implemented, #82")
            case SketchConstraint.VERTICAL:
                new_constraint = Vertical(a, reference_a, b, reference_b,)
            case _:
                raise ValueError(f"Constraint choice {constraint_choice}"
                                 " not recognized")
        self.add_constraint(new_constraint)
    
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
        TYPE_STR = "{0}_{1}"
        return {"Index": self.get_index_of(constraint),
                "Type": constraint.__class__.__name__,
                "a Index": self.get_index_of(geometry_a),
                "a UID": geometry_a.uid,
                "a Type": TYPE_STR.format(geometry_a.__class__.__name__,
                                          reference_a.name.title()),
                "b Index": self.get_index_of(geometry_b),
                "b UID": geometry_b.uid,
                "b Type": TYPE_STR.format(geometry_b.__class__.__name__,
                                          reference_b.name.title())}
    
    @_get_summary_info.register
    def _state_constraint(self, constraint: AbstractSnapTo) -> dict:
        geometry = constraint.get_constrained()
        references = constraint.get_references()
        TYPE_STR = "{0}_{1}"
        if len(geometry) == 1:
            geometry_a = geometry[0]
            reference_a = references[0]
            return {"Index": self.get_index_of(constraint),
                    "Type": constraint.__class__.__name__,
                    "a Index": self.get_index_of(geometry_a),
                    "a UID": geometry_a.uid,
                    "a Type": TYPE_STR.format(geometry_a.__class__.__name__,
                                              reference_a.name.title()),
                    "b Index": None,
                    "b UID": None,
                    "b Type": None,}
        else:
            geometry_a, geometry_b = geometry
            reference_a, reference_b = references
            return {"Index": self.get_index_of(constraint),
                    "Type": constraint.__class__.__name__,
                    "a Index": self.get_index_of(geometry_a),
                    "a UID": geometry_a.uid,
                    "a Type": TYPE_STR.format(geometry_a.__class__.__name__,
                                              reference_a.name.title()),
                    "b Index": self.get_index_of(geometry_b),
                    "b UID": geometry_b.uid,
                    "b Type": TYPE_STR.format(geometry_b.__class__.__name__,
                                              reference_b.name.title())}
    
    @_get_summary_info.register
    def _1_geo_distance(self, constraint: Abstract1GeometryDistance) -> dict:
        geometry_a = constraint.get_constrained()[0]
        reference_a = constraint.get_references()[0]
        TYPE_STR = "{0}_{1}"
        return {"Index": self.get_index_of(constraint),
                "Type": constraint.__class__.__name__,
                "a Index": self.get_index_of(geometry_a),
                "a UID": geometry_a.uid,
                "a Type": TYPE_STR.format(geometry_a.__class__.__name__,
                                          reference_a.name.title()),
                "Value": constraint.get_value_string()}
    
    @_get_summary_info.register
    def _2_geo_distance(self, constraint: Abstract2GeometryDistance) -> dict:
        geometry_a, geometry_b = constraint.get_constrained()
        reference_a, reference_b = constraint.get_references()
        TYPE_STR = "{0}_{1}"
        return {"Index": self.get_index_of(constraint),
                "Type": constraint.__class__.__name__,
                "a Index": self.get_index_of(geometry_a),
                "a UID": geometry_a.uid,
                "a Type": TYPE_STR.format(geometry_a.__class__.__name__,
                                          reference_a.name.title()),
                "b Index": self.get_index_of(geometry_b),
                "b UID": geometry_b.uid,
                "b Type": TYPE_STR.format(geometry_b.__class__.__name__,
                                          reference_b.name.title()),
                "Value": constraint.get_value_string()}
    
    @_get_summary_info.register
    def _angle(self, constraint: Angle) -> dict:
        geometry_a, geometry_b = constraint.get_constrained()
        reference_a, reference_b = constraint.get_references()
        TYPE_STR = "{0}_{1}"
        return {"Index": self.get_index_of(constraint),
                "a Index": self.get_index_of(geometry_a),
                "a UID": geometry_a.uid,
                "a Type": TYPE_STR.format(geometry_a.__class__.__name__,
                                          reference_a.name.title()),
                "b Index": self.get_index_of(geometry_b),
                "b UID": geometry_b.uid,
                "b Type": TYPE_STR.format(geometry_b.__class__.__name__,
                                          reference_b.name.title()),
                "Value": constraint.get_value_string(),
                "Quadrant": constraint.quadrant,}
    
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
        n_geo = len(self.geometry)
        n_cons = len(self.constraints)
        n_ext = len(self.externals)
        return f"<Sketch'{self.name}'(g{n_geo},c{n_cons},e{n_ext})>"
    
    def __str__(self) -> str:
        """Returns the longer string representation of the sketch"""
        from textwrap import indent
        sketch_summary = []
        sketch_summary.append(f"Sketch '{self.name}'")
        sketch_summary.append(
            indent(f"Sketch uid: {self.uid}", "  ")
        )
        
        # Location/Plane Summary
        sketch_summary.append(
            indent(self._generate_location_string(), "  ")
        )
        # Geometry Summary #
        sketch_summary.append("Geometry")
        summaries = {
            "Circles": Circle,
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