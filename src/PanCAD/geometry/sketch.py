"""A module providing a class to represent sketches in 3D space. PanCAD defines a 
sketch as a set of 2D geometry on a coordinate system's plane oriented in 3D 
space. PanCAD's sketch definition aims to be as general as possible, so the 
base implementation of this class does not include appearance information since 
that is application specific.
"""

from __future__ import annotations

from collections import namedtuple
from functools import reduce
from itertools import compress
import textwrap

from PanCAD.geometry.abstract_feature import AbstractFeature
from PanCAD.geometry.abstract_geometry import AbstractGeometry
from PanCAD.geometry.constraints.state_constraint import AbstractStateConstraint
from PanCAD.geometry.constraints.distance import (
    Abstract2GeometryDistance, Abstract1GeometryDistance, Angle
)
from PanCAD.geometry import (
    Circle, CoordinateSystem, Point, Line, LineSegment, Plane,
)
from PanCAD.geometry.constraints import (
    Coincident, Vertical, Horizontal,
    Distance, HorizontalDistance, VerticalDistance, Diameter, Radius,
)
from PanCAD.geometry.constants import SketchConstraint, ConstraintReference

class Sketch(AbstractFeature):
    """A class representing a set of 2D geometry on a coordinate system plane in 
    3D space.
    
    :param coordinate_system: A coordinate system defining where the sketch's 
        location and orientation. If no coordinate system is provided, the 
        sketch will be placed at the default (0, 0, 0) coordinate system.
    :param plane_reference: A string specifying which plane of the coordinate 
        system to place the geometry on. Options include: XY, XZ, YZ. Defaults
        to XY.
    :param geometry: 2D PanCAD geometry tuple. Defaults to an empty tuple.
    :param construction: Construction boolean tuple where each value determines 
        whether the corresponding geometry element index is construction 
        geometry. Defaults to an empty tuple. Must be the same length as the 
        geometry tuple, but if it is not given then all initially provided 
        geometry is assumed to be non-construction (all False).
    :param constraints: PanCAD constraints tuple. Defaults to an empty tuple.
    :param externals: 3D PanCAD geometry tuple that can be referenced by the 
        constraints. Defaults to an empty tuple.
    :param uid: The unique id of the Sketch. Defaults to None.
    """
    # Class Constants
    UID_SEPARATOR = "_"
    CS_2D_UID = "sketchcs"
    
    # Type Tuples for checking with isinstance()
    GEOMETRY_TYPES = (Circle, Line, LineSegment, Point)
    EXTERNAL_TYPES = (Circle, CoordinateSystem, Line, LineSegment, Point, Plane)
    
    # Type Hints
    GeometryType = reduce(lambda x, y: x | y, GEOMETRY_TYPES)
    ExternalType = reduce(lambda x, y: x | y, EXTERNAL_TYPES)
    ConstraintType = Coincident
    
    # Collections
    GeometryStatus = namedtuple("GeometryStatus", ["geometry", "construction"])
    
    def __init__(self,
                 coordinate_system: CoordinateSystem=None,
                 plane_reference: ConstraintReference=ConstraintReference.XY,
                 geometry: tuple[GeometryType]=None,
                 construction: tuple[bool]=None,
                 constraints: tuple[ConstraintType]=None,
                 externals: tuple[ExternalType]=None,
                 uid: str=None):
        # Initialize private uid since uid and geometry sync with each other
        self._uid = None
        
        if geometry is None:
            geometry = tuple()
        if constraints is None:
            constraints = tuple()
        if externals is None:
            externals = tuple()
        
        self._sketch_cs = CoordinateSystem((0, 0), uid=self.CS_2D_UID)
        
        if coordinate_system is None:
            self.coordinate_system = CoordinateSystem()
        else:
            self.coordinate_system = coordinate_system
            
        self.geometry = geometry
        self.externals = externals
        self.construction = construction
        self.plane_reference = plane_reference
        self.constraints = constraints
        self.uid = uid
    
    # Getters #
    @property
    def constraints(self) -> tuple[ConstraintType]:
        return self._constraints
    
    @property
    def construction(self) -> tuple[bool]:
        """The tuple of booleans indicating whether each index of the geometry 
        tuple is construction geometry.
        """
        return self._construction
    
    @property
    def coordinate_system(self) -> CoordinateSystem:
        """The contextual coordinate system that positions and rotates the 
        sketch.
        
        :getter: Returns the CoordinateSystem object.
        :setter: Sets the sketch coordinate system and syncs the rest of the 
            sketch to the new coordinate system.
        """
        return self._coordinate_system
    
    @property
    def externals(self) -> tuple[ExternalType]:
        """The tuple of 3D external geometry referenced by the sketch.
        
        :getter: Returns the tuple of external geometry references.
        :setter: Checks that all the external geometry is 3D and sets the tuple.
        """
        return self._externals
    
    @property
    def geometry(self) -> tuple[GeometryType]:
        """The tuple of 2D geometry in the sketch.
        
        :getter: Returns the tuple of geometry in the sketch.
        :setter: Sets the tuple of geometry in the sketch after checking the new
            lists' validity.
        """
        return self._geometry
    
    @property
    def plane_reference(self) -> ConstraintReference:
        """The reference of the CoordinateSystem's plane that contains the 
        sketch's geometry. Must be one of the enumeration values in 
        PanCAD.geometry.constants.ConstraintReference.
        
        :getter: Returns the reference of the plane.
        :setter: Checks reference validity and then sets the plane reference.
        """
        return self._plane_reference
    
    @property
    def uid(self) -> str:
        """The unique id of the sketch.
        
        :getter: Returns the unique id of the sketch.
        :setter: Sets the uid of the sketch and syncs all the sketch's contained
            geometry to the sketch's uid.
        """
        return self._uid
    
    # Setters #
    @coordinate_system.setter
    def coordinate_system(self, coordinate_system: CoordinateSystem):
        self._coordinate_system = coordinate_system
    
    @constraints.setter
    def constraints(self, constraints: list[ConstraintType]):
        for c in constraints:
            self._validate_constraint_references(c)
        self._constraints = tuple(constraints)
    
    @construction.setter
    def construction(self, construction: tuple[bool]):
        if construction is None and self.geometry is not None:
            self._construction = tuple(
                [False] * len(self.geometry)
            )
        elif construction is None and self.geometry is None:
            self._construction = tuple()
        elif len(construction) != len(self.geometry):
            raise ValueError("geometry and construction tuple must be the same"
                             " length, given:"
                             f"\n{self.geometry}\n{construction}")
        else:
            self._construction = construction
    
    @externals.setter
    def externals(self, externals: list):
        non_3d_externals = list(
            filter(lambda g: len(g) != 3, externals)
        )
        if non_3d_externals != []:
            raise ValueError(f"3D Geometry only, 2D: {non_3d_externals}")
        self._externals = tuple(externals)
    
    @geometry.setter
    def geometry(self, geometry: list | tuple):
        non_2d_geometry = list(
            filter(lambda g: len(g) != 2, geometry)
        )
        if non_2d_geometry != []:
            raise ValueError(f"2D Geometry only, given 3D: {non_2d_geometry}")
        
        self._geometry = tuple(geometry)
        self._sync_geometry_uid()
    
    @plane_reference.setter
    def plane_reference(self, reference: ConstraintReference):
        reference_planes = (ConstraintReference.XY
                            | ConstraintReference.XZ
                            | ConstraintReference.YZ)
        if reference in reference_planes:
            self._plane_reference = reference
        else:
            raise ValueError(f"{reference} not recognized as a plane reference,"
                             f"must be one of {list(reference_planes)}")
    
    @uid.setter
    def uid(self, uid: str):
        original = self.uid
        if original is not None:
            original_prefix = original + self.UID_SEPARATOR
        self._uid = uid
        for g in self.geometry:
            if original is not None and g.uid.startswith(original_prefix):
                g.uid = self.UID_SEPARATOR.join(
                    [uid, g.uid.replace(original_prefix, "", 1)]
                )
        self._sync_geometry_uid()
        
        if (original is not None
                and self._sketch_cs.uid.startswith(original_prefix)):
            self._sketch_cs.uid = self._sketch_cs.uid.replace(
                original_prefix, self.uid + self.UID_SEPARATOR, 1
            )
        elif self.uid is None:
            pass
        else:
            self._sketch_cs.uid = self.UID_SEPARATOR.join(
                [self.uid, self._sketch_cs.uid]
            )
    
    # Public Functions #
    def add_constraint(self, constraint) -> None:
        dependencies = constraint.get_constrained()
        if all([d in self for d in dependencies]):
            self.constraints = self.constraints + (constraint,)
        else:
            missing = filter(lambda d: d not in self, dependencies)
            raise LookupError(f"Dependencies for {repr(constraint)} are missing"
                             f" from part: {list(missing)}")
    
    def add_constraint_by_uid(
                self, constraint_choice: SketchConstraint,
                uid_a: str, reference_a: ConstraintReference,
                uid_b: str=None, reference_b: ConstraintReference=None,
                uid_c: str=None, reference_c: ConstraintReference=None,
                **kwargs
            ) -> None:
        """Adds a sketch constraint between two geometry elements selected by 
        their uids. Prefixes the new constraint's uid with the sketch's uid. All 
        geometry must already be in the sketch's geometry. ConstraintReference 
        CS can be used instead of any of the geometry inputs to refer to the 
        sketch's coordinate system.
        
        :param constraint_choice: The SketchConstraint of the constraint choice
        :param uid_a: The uid of geometry a.
        :param reference_a: The ConstraintReference to part of geometry a
        :param uid_b: The uid of geometry b. Only supplied for constraints 
            that require 2 or 3 geometry elements (e.g. coincident, parallel), 
            otherwise ignored.
        :param reference_b: The ConstraintReference to part of geometry b
        :param uid_c: The uid of geometry c. Only supplied for constraints 
            requiring 3 geometry elements (i.e. symmetry), otherwise ignored.
        :param reference_c: The ConstraintReference to part of geometry c. The 
            uid of geometry c. Only supplied for constraints requiring 3 
            geometry elements (i.e. symmetry), otherwise ignored.
        """
        geometry_a = self.get_geometry_by_uid(uid_a)
        geometry_b = self.get_geometry_by_uid(uid_b)
        geometry_c = self.get_geometry_by_uid(uid_c)
        self._add_new_constraint(constraint_choice,
                                 geometry_a, reference_a,
                                 geometry_b, reference_b,
                                 geometry_c, reference_c,
                                 **kwargs)
    
    def add_constraint_by_index(
                self, constraint_choice: SketchConstraint,
                index_a: int, reference_a: ConstraintReference,
                index_b: int=None, reference_b: ConstraintReference=None,
                index_c: int=None, reference_c: ConstraintReference=None,
                **kwargs
            ) -> None:
        """Adds a sketch constraint between two geometry elements selected by 
        their indices. Prefixes the new constraint's uid with the sketch's uid. 
        All geometry must already be in the sketch's geometry.
        ConstraintReference CS can be used instead of any of the geometry inputs 
        to refer to the sketch's coordinate system.
        
        :param constraint_choice: The SketchConstraint of the constraint choice
        :param index_a: The index of geometry a.
        :param reference_a: The ConstraintReference to part of geometry a
        :param index_b: The index of geometry b. Only supplied for constraints 
            that require 2 or 3 geometry elements (e.g. coincident, parallel), 
            otherwise ignored.
        :param reference_b: The ConstraintReference to part of geometry b
        :param index_c: The index of geometry c. Only supplied for constraints 
            requiring 3 geometry elements (i.e. symmetry), otherwise ignored.
        :param reference_c: The ConstraintReference to part of geometry c.
        """
        geometry_a = self._get_geometry_by_index(index_a)
        geometry_b = self._get_geometry_by_index(index_b)
        geometry_c = self._get_geometry_by_index(index_c)
        
        self._add_new_constraint(constraint_choice,
                                 geometry_a, reference_a,
                                 geometry_b, reference_b,
                                 geometry_c, reference_c,
                                 **kwargs)
    
    def get_construction_geometry(self) -> tuple[GeometryType]:
        """Returns a tuple of the sketch's construction geometry."""
        return tuple(compress(self.geometry, self.construction))
    
    def get_dependencies(self) -> tuple[ExternalType]:
        """Returns a tuple of the sketch's external dependencies"""
        return (self.coordinate_system,) + self.externals
    
    def get_geometry_status(self) -> iter[GeometryStatus]:
        """Returns an iterator of GeometryStatus namedtuples that contains the 
        geometry and whether the geometry is construction geometry
        """
        for geometry, construction in zip(self.geometry, self.construction):
            yield self.GeometryStatus(geometry, construction)
    
    def get_geometry_by_uid(self, uid: str|ConstraintReference) -> GeometryType:
        """Returns an element of geometry if a geometry with that uid matches 
        the one given.
        
        :param uid: The uid of the geometry. Can also be ConstraintReference.CS 
            to the sketch's 2D coordinate system since the 2D coordinate system 
            is not in the sketch's geometry tuple.
        :returns: A geometry element with uid or the sketch's 2D coordinate 
            system.
        """
        geometry_uids = [g.uid for g in self.geometry]
        if uid in geometry_uids:
            return self.geometry[geometry_uids.index(uid)]
        elif uid is ConstraintReference.CS:
            return self.get_sketch_coordinate_system()
        elif uid is None:
            return None
        else:
            raise ValueError(f"uid '{uid}' was not found in sketch's geometry")
    
    def get_index_of(self, item: object) -> int:
        """Returns the index of a geometry, constraint, or external item in 
        their respective lists. Raises an error if its not in any of them."""
        if any([item is g for g in self.geometry]):
            return [item is g for g in self.geometry].index(True)
        elif any([item is c for c in self.constraints]):
            return [item is c for c in self.constraints].index(True)
        elif any([item is g for g in self.externals]):
            return [item is g for g in self.externals].index(True)
        
        sketch_cs = self.get_sketch_coordinate_system()
        cs_ref_geometry = [sketch_cs]
        cs_ref_geometry.extend([sketch_cs.get_reference(r)
                                for r in sketch_cs.get_all_references()])
        if any([item is g for g in cs_ref_geometry]):
            return item.__class__.__name__
        else:
            raise LookupError(f"Item {item} is not in sketch")
    
    def get_non_construction_geometry(self) -> tuple[GeometryType]:
        """Returns a tuple of the sketch's non-construction geometry."""
        non_construction = [not c for c in self.construction]
        return tuple(compress(self.geometry, non_construction))
    
    def get_plane(self):
        """Returns the plane that contains the sketch geometry.
        
        :returns: The sketch's plane.
        """
        return self.coordinate_system.get_reference(self.plane_reference)
    
    def get_sketch_coordinate_system(self) -> CoordinateSystem:
        """Returns the sketch's 2D coordinate system."""
        return self._sketch_cs
    
    def has_geometry(self, geometry: GeometryType) -> bool:
        """Checks whether the given geometry is in the sketch's geometry 
        tuple. Compares memory locations, not just equality."""
        constrainable_geometry = (self._sketch_cs,) + self.geometry
        return any(geometry is cg for cg in constrainable_geometry)
    
    # Private Functions #
    def _get_geometry_by_index(self, index: int | ConstraintReference | None
                               ) -> GeometryType | None:
        """Returns the geometry at the index of the sketch's geometry tuple.
        
        :param index: The index of the geometry in the geometry tuple, or 
            ConstraintReference.CS to reference the sketch's coordinate system
        :returns: The geometry at index or the sketch's 2D coordinate system.
        """
        if index is ConstraintReference.CS:
            return self._sketch_cs
        elif index is None:
            return None
        else:
            return self.geometry[index]
    
    def _validate_constraint_references(self, constraint) -> None:
        """Checks whether a constraint references geometry in the sketch's 
        geometry or externals"""
        references = constraint.get_constrained()
        if not all([self.has_geometry(g) for g in references]):
            raise ValueError(f"The {repr(constraint)} constraint references"
                             " geometry that is not in the sketch."
                             f"\nAll Geometry: {references}")
    
    def _new_constraint_uid(self) -> str:
        """Figures out and returns the next constraint uid"""
        constraint_uid = str(len(self.constraints))
        if self.uid is not None:
            constraint_uid = self.UID_SEPARATOR.join(self.uid, constraint_uid)
        return constraint_uid
    
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
        constraint_uid = self._new_constraint_uid()
        
        match constraint_choice:
            case SketchConstraint.COINCIDENT:
                new_constraint = Coincident(a, reference_a, b, reference_b,
                                            uid=constraint_uid)
            case SketchConstraint.HORIZONTAL:
                new_constraint = Horizontal(a, reference_a, b, reference_b,
                                            uid=constraint_uid)
            case SketchConstraint.VERTICAL:
                new_constraint = Vertical(a, reference_a, b, reference_b,
                                          uid=constraint_uid)
            case SketchConstraint.DISTANCE:
                new_constraint = Distance(
                    a, reference_a, b, reference_b, uid=constraint_uid, **kwargs
                )
            case SketchConstraint.DISTANCE_HORIZONTAL:
                new_constraint = HorizontalDistance(
                    a, reference_a, b, reference_b, uid=constraint_uid, **kwargs
                )
            case SketchConstraint.DISTANCE_VERTICAL:
                new_constraint = VerticalDistance(
                    a, reference_a, b, reference_b, uid=constraint_uid, **kwargs
                )
            case SketchConstraint.DISTANCE_RADIUS:
                new_constraint = Radius(
                    a, reference_a, uid=constraint_uid, **kwargs
                )
            case SketchConstraint.DISTANCE_DIAMETER:
                new_constraint = Diameter(
                    a, reference_a, uid=constraint_uid, **kwargs
                )
            case _:
                raise ValueError("Constraint choice not recognized")
        self.constraints += (new_constraint,)
    
    def _sync_geometry_uid(self):
        """Prepends the geometry uids with the sketch's uid unless it was 
        specially overridden."""
        if self.uid is not None:
            for i, g in enumerate(self.geometry):
                if g.uid is None or g.uid == "" or g.uid.isnumeric():
                    uid_parts = [self.uid, str(i)]
                else:
                    # Leave the geometry uid unchanged if it is not a number,
                    # none or empty string. Assumed to be a special user defined 
                    # uid
                    uid_parts = [g.uid]
                g.uid = self.UID_SEPARATOR.join(uid_parts)
    
    # Python Dunders #
    def __copy__(self) -> Sketch:
        raise NotImplementedError("Sketch copy hasn't been implemented yet,"
                                  " see github issue #53")
    
    def __contains__(self, item):
        contents = (self.get_sketch_coordinate_system(),) + self.geometry
        return any([item is c for c in contents])
    
    def __len__(self) -> int:
        """Returns the number of dimensions of the sketch's contextual 
        coordinate system"""
        return len(self.coordinate_system)
    
    def __repr__(self) -> str:
        """Returns the short string representation of the sketch"""
        n_geo = len(self.geometry)
        n_cons = len(self.constraints)
        n_ext = len(self.externals)
        return f"<PanCADSketch'{self.uid}'(g{n_geo},c{n_cons},e{n_ext})>"
    
    def __str__(self) -> str:
        """Returns the longer string representation of the sketch"""
        n_geo = len(self.geometry)
        n_cons = len(self.constraints)
        n_ext = len(self.externals)
        
        # Geometry Summary
        # LineSegment: index, uid, start, end
        # Point: index, uid, location
        # Line: index, uid, x-intercept, y-intercept
        # Circle: index, uid, center location, radius
        
        # Constraint Summary
        # *Geometry names need to include the parent
        # Snapto Constraints, one geometry: index, uid, geometry index, geometry
        # Snapto Constraints, two geometry: index, uid, index a geometry a, index b, geometry b
        # State Constraints: index, uid, index a, geometry a, index b, geometry b
        # Distance Constraints: index, uid, index a, geometry a, index b, geometry b, value, unit
        sketch_summary = []
        
        sketch_summary.append(f"Sketch '{self.uid}'")
        
        # Geometry Summary #
        sketch_summary.append("Geometry")
        geometry_summary = []
        geometry_info = []
        for g in filter(lambda g: isinstance(g, Circle), self.geometry):
            geometry_info.append(
                {"Index": self.get_index_of(g), "UID": g.uid,
                 "Center": g.center.cartesian, "Radius": g.radius,
                 "Construction": self.construction[self.get_index_of(g)],}
            )
        if len(geometry_info) > 0:
            geometry_summary.append("Circles")
            geometry_summary.append(get_table_string(geometry_info))
        
        geometry_info = []
        for g in filter(lambda g: isinstance(g, LineSegment), self.geometry):
            geometry_info.append(
                {"Index": self.get_index_of(g), "UID": g.uid,
                 "Start": g.point_a.cartesian, "End": g.point_b.cartesian,
                 "Construction": self.construction[self.get_index_of(g)],}
            )
        if len(geometry_info) > 0:
            geometry_summary.append("Line Segments")
            geometry_summary.append(get_table_string(geometry_info))
        
        geometry_info = []
        for g in filter(lambda g: isinstance(g, Line), self.geometry):
            geometry_info.append(
                {"Index": self.get_index_of(g), "UID": g.uid,
                 "X-Intercept": (g.x_intercept, 0),
                 "Y-Intercept": (0, g.y_intercept),
                 "Construction": self.construction[self.get_index_of(g)],}
            )
        if len(geometry_info) > 0:
            geometry_summary.append("Infinite Lines")
            geometry_summary.append(get_table_string(geometry_info))
        
        geometry_info = []
        for g in filter(lambda g: isinstance(g, Point), self.geometry):
            geometry_info.append(
                {"Index": self.get_index_of(g), "UID": g.uid,
                 "Location": g.cartesian,
                 "Construction": self.construction[self.get_index_of(g)],}
            )
        if len(geometry_info) > 0:
            geometry_summary.append("Points")
            geometry_summary.append(get_table_string(geometry_info))
        
        geometry_summary = "\n".join(geometry_summary)
        geometry_summary = textwrap.indent(geometry_summary, "  ")
        sketch_summary.append(geometry_summary)
        
        # Constraint Summary #
        sketch_summary.append("Constraints")
        constraint_summary = []
        constraint_info = []
        for c in filter(lambda c: isinstance(c, AbstractStateConstraint),
                        self.constraints):
            constraint_info.append(
                {"Index": self.get_index_of(c), "Type": c.__class__.__name__,
                 "a Index": self.get_index_of(c.get_constrained()[0]),
                 "a UID": c.get_constrained()[0].uid,
                 "a Type": (c.get_constrained()[0].__class__.__name__ 
                            + "_" + c.get_references()[0].name.title()),
                 "b Index": self.get_index_of(c.get_constrained()[1]),
                 "b UID": c.get_constrained()[1].uid,
                 "b Type": (c.get_constrained()[1].__class__.__name__ 
                            + "_" + c.get_references()[1].name.title()),}
            )
        if len(constraint_info) > 0:
            constraint_summary.append("State Constraints")
            constraint_summary.append(get_table_string(constraint_info))
        
        constraint_info = []
        for c in filter(lambda c: isinstance(c, Abstract2GeometryDistance),
                        self.constraints):
            constraint_info.append(
                {"Index": self.get_index_of(c), "Type": c.__class__.__name__,
                 "a Index": self.get_index_of(c.get_constrained()[0]),
                 "a UID": c.get_constrained()[0].uid,
                 "a Type": (c.get_constrained()[0].__class__.__name__ 
                            + "_" + c.get_references()[0].name.title()),
                 "b Index": self.get_index_of(c.get_constrained()[1]),
                 "b UID": c.get_constrained()[1].uid,
                 "b Type": (c.get_constrained()[1].__class__.__name__ 
                            + "_" + c.get_references()[1].name.title()),
                 "Value": c.get_value_string(),}
            )
        if len(constraint_info) > 0:
            constraint_summary.append("Distance Constraints")
            constraint_summary.append(get_table_string(constraint_info))
        
        constraint_info = []
        for c in filter(lambda c: isinstance(c, Abstract1GeometryDistance),
                        self.constraints):
            constraint_info.append(
                {"Index": self.get_index_of(c), "Type": c.__class__.__name__,
                 "a Index": self.get_index_of(c.get_constrained()[0]),
                 "a UID": c.get_constrained()[0].uid,
                 "a Type": (c.get_constrained()[0].__class__.__name__ 
                            + "_" + c.get_references()[0].name.title()),
                 "Value": c.get_value_string(),}
            )
        if len(constraint_info) > 0:
            constraint_summary.append("Radius and Diameter Constraints")
            constraint_summary.append(get_table_string(constraint_info))
        
        constraint_info = []
        for c in filter(lambda c: isinstance(c, Angle),
                        self.constraints):
            constraint_info.append(
                {"Index": self.get_index_of(c), "Type": c.__class__.__name__,
                 "a Index": self.get_index_of(c.get_constrained()[0]),
                 "a UID": c.get_constrained()[0].uid,
                 "a Type": (c.get_constrained()[0].__class__.__name__ 
                            + "_" + c.get_references()[0].name.title()),
                 "b Index": self.get_index_of(c.get_constrained()[1]),
                 "b UID": c.get_constrained()[1].uid,
                 "b Type": (c.get_constrained()[1].__class__.__name__ 
                            + "_" + c.get_references()[1].name.title()),
                 "Value": c.get_value_string(),
                 "Quadrant": c.quadrant,}
            )
        if len(constraint_info) > 0:
            constraint_summary.append("Angle Constraints")
            constraint_summary.append(get_table_string(constraint_info))
        
        constraint_summary = "\n".join(constraint_summary)
        constraint_summary = textwrap.indent(constraint_summary, "  ")
        sketch_summary.append(constraint_summary)
        
        return "\n".join(sketch_summary)

def get_table_string(data: list[dict], column_map: dict=None, delimiter: str="  ") -> str:
    string_rows = []
    if column_map is None:
        
        column_map = {key: key for key in data[0]}
    
    for column, key in column_map.items():
        column_width = len(column)
        rows = [column]
        rows.extend([info[key] for info in data])
        lengths = list(map(lambda s: len(str(s)), rows))
        if max(lengths) > column_width:
            column_width = max(lengths)
        
        rows = ["{0: <{1}}".format(str(s), column_width) for s in rows]
        if len(string_rows) == 0:
            string_rows = rows
        else:
            for i, row in enumerate(rows):
                string_rows[i] = delimiter.join([string_rows[i], row])
    return "\n".join(string_rows)