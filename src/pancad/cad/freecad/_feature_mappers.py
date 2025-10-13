"""A module providing classes to map pancad files to FreeCAD files."""
from __future__ import annotations

from collections.abc import MutableMapping
from functools import singledispatchmethod
from textwrap import indent
from typing import Self, NoReturn, TYPE_CHECKING
from uuid import UUID
from xml.etree import ElementTree

from pancad.geometry import (
    AbstractFeature,
    AbstractGeometry,
    FeatureContainer,
    PancadThing,
    Sketch,
)
from pancad.geometry.constants import ConstraintReference
from pancad.geometry.constraints import AbstractConstraint

from ._application_types import (
    FreeCADBody,
    FreeCADConstraint,
    FreeCADFeature,
    FreeCADGeometry,
    FreeCADCADObject,
    FreeCADOrigin,
)
from .constants import (
    ConstraintType,
    EdgeSubPart,
    InternalAlignmentType,
    ListName,
    ObjectType,
    SketchNumber,
)
from ._map_typing import (
    FeatureID,
    FreeCADID,
    SketchElementID,
    SketchSubGeometryID,
    SubFeatureID,
)

if TYPE_CHECKING:
    from types import GenericAlias
    
    from pancad import PartFile
    
    from ._application_types import FreeCADDocument
    from ._map_typing import InternalAlignmentMap, SubFeatureMap, SubGeometryMap

class FreeCADMap(MutableMapping):
    """A class implementing a mapping to and from pancad and FreeCAD elements.
    
    :param document: The FreeCAD document being mapped to or from.
    :param part_file: The pancad PartFile being mapped to or from.
    """
    PREFIX = " "
    """The string added before lines in map summaries."""
    
    from ._feature_translation import (
        _freecad_add_to_sketch,
        _freecad_to_pancad_feature,
        _freecad_to_pancad_geometry,
        _pancad_to_freecad_feature,
        _pancad_to_freecad_geometry,
    )
    from ._element_links import (
        _link_features,
        _link_geometry,
    )
    from ._constraint_translation import (
        _freecad_to_pancad_add_constraints,
        _freecad_to_pancad_constraint,
        _link_constraints,
        _pancad_to_freecad_add_constraints,
        _pancad_to_freecad_constraint,
    )
    
    def __init__(self, document: FreeCADDocument, part_file: PartFile) -> None:
        self._document = document
        self._part_file = part_file
        self._pancad_to_freecad = dict()
        # Maps from pancad objects to their associated FreeCAD objects
        self._freecad_to_pancad = dict()
        # Maps from FreeCAD IDs to their associated pancad objects
        
        self._id_map = _FreeCADIDMap()
        # Maps FreeCAD IDs to their objects
        self._feature_map = _FreeCADFeatureMap(self._id_map)
        # Maps freecad ids to their features and subfeatures
        self._geometry_map = _FreeCADSketchGeometryMap(self._id_map,
                                                       self._feature_map)
        # Maps freecad sketch ids to their contained geometry
        self._constraint_map = _FreeCADSketchConstraintMap(self._id_map,
                                                           self._feature_map,
                                                           self._geometry_map)
    
    # Public Methods #
    def add_freecad_feature(self, feature: FreeCADFeature) -> Self:
        """Adds a FreeCAD feature to the map by generating and linking new 
        pancad objects. Returns the updated map.
        """
        pancad_feature = self._freecad_to_pancad_feature(feature)
        self[pancad_feature] = feature
        if feature.TypeId == ObjectType.BODY:
            children = [feature.Origin] + feature.Group
            for child in children:
                self.add_freecad_feature(child)
        elif feature.TypeId == ObjectType.SKETCH:
            self._link_features(pancad_feature, feature)
            self._freecad_to_pancad_add_constraints(feature, pancad_feature)
        return self
    
    def freecad_to_pancad_summary(self) -> str:
        """Returns a string summary of the mapping from freecad to pancad. 
        Intended to be the reversed viewpoint of FreeCADMap's __str__.
        """
        strings = []
        for freecad_id, (geometry, reference) in self._freecad_to_pancad.items():
            freecad_repr = self._freecad_repr(freecad_id)
            strings.append(
                indent(
                    f"{freecad_repr}: {repr(geometry)}, {reference.name}",
                    self.PREFIX
                )
            )
            strings[-1] = strings[-1] + ","
        strings[0] = strings[0].removeprefix(self.PREFIX)
        return "{" + "\n".join(strings) + "}"
    
    @singledispatchmethod
    def add_pancad_feature(self, feature: AbstractFeature) -> Self:
        """Adds a pancad feature to the map by generating and linking new 
        FreeCAD objects. Returns the updated map.
        """
        freecad_feature = self._pancad_to_freecad_feature(feature)
        self[feature] = freecad_feature
        return self
    
    def get_freecad_id(self,
                       key: PancadThing,
                       reference: ConstraintReference=ConstraintReference.CORE,
                       ) -> FreeCADID:
        """Returns the FreeCADID mapped to the pancad object and constraint 
        reference.
        
        :param key: The pancad object.
        :param reference: The ConstraintReference for the portion of the pancad 
            object. Defaults to CORE to provide the parent FreeCAD object.
        :returns: The associated FreeCADID.
        """
        _, freecad_id = self._pancad_to_freecad[key.uid]
        if isinstance(key, AbstractFeature):
            return self._feature_map.get_freecad_id(freecad_id, reference)
        elif isinstance(key, AbstractGeometry):
            return self._geometry_map.get_freecad_id(freecad_id + (reference,))
        else:
            return freecad_id
    
    def get_pancad(self, freecad_id: FreeCADID) -> tuple[PancadThing,
                                                         ConstraintReference]:
        """Returns the pancad object and constraint reference mapped to the 
        FreeCAD ID.
        """
        return self._freecad_to_pancad[freecad_id]
    
    def get_references(self,
                       key: AbstractFeature | AbstractGeometry
                       ) -> list[ConstraintReference]:
        """Returns a tuple of the references available for the key.
        
        :raises TypeError: Raised if provided an object that is not a feature or 
            geometry.
        """
        if isinstance(key, AbstractFeature):
            feature = self[key]
            return self._feature_map.get_references(feature.ID)
        elif isinstance(key, AbstractGeometry):
            freecad_id = self.get_freecad_id(key)
            return self._geometry_map.get_references(freecad_id)
        else:
            raise TypeError("Can only return references for Features and"
                            f" Geometry, provided {key.__class__}")
    
    # Public Static Methods #
    @staticmethod
    def get_id_type(key: int | tuple) -> GenericAlias:
        """Returns the FreeCADID type of the input key."""
        # Check if Feature
        if isinstance(key, int):
            return FeatureID
        elif not isinstance(key, tuple):
            raise TypeError(f"Key must be int or tuple, given {key.__class__}")
        
        feature_id, dispatch, *_ = key
        if not isinstance(feature_id, int):
            raise TypeError(f"Key {key} 1st element must be int to reference"
                            " a FreeCAD feature ID")
        
        # Check if key is a SubFeature
        if dispatch in ConstraintReference and len(key) == 2:
            return SubFeatureID
        elif dispatch in ListName:
            list_name = dispatch
        else:
            raise TypeError(f"Key {key} 2nd element must be"
                            " ConstraintReference or ListName")
        _, _, index, *_ = key
        if not isinstance(index, int):
            raise TypeError(f"Key {key} 3rd element must be int")
        
        # Check for list type
        if len(key) == 3:
            return SketchElementID
        elif len(key) == 4 and key[-1] in ConstraintReference:
            return SketchSubGeometryID
        else:
            raise TypeError(f"Key {key} 4th element must be a"
                            " ConstraintReference to be a"
                            " SketchSubGeometryID")
    
    # Private Methods
    @add_pancad_feature.register
    def _feature_container(self, container: FeatureContainer) -> Self:
        body = self._pancad_to_freecad_feature(container)
        self[container] = body
        for subfeature in container.features:
            self.add_pancad_feature(subfeature)
        return self
    
    @add_pancad_feature.register
    def _sketch(self, sketch: Sketch) -> Self:
        freecad_sketch = self._pancad_to_freecad_feature(sketch)
        self._link_features(sketch, freecad_sketch)
        self._pancad_to_freecad_add_constraints(sketch, freecad_sketch)
        return self
    
    def _freecad_repr(self, freecad_id: FreeCADID) -> str:
        """Returns a string representing the freecad object in map summaries."""
        freecad_object = self._id_map[freecad_id]
        type_id = freecad_object.TypeId.split("::")[-1]
        default_repr = repr(type_id).replace("<", "") \
                                    .replace(">", "") \
                                    .replace("'", "")
        if hasattr(freecad_object, "Label"):
            # Features
            return f"<ID:{freecad_id} '{freecad_object.Label}'{default_repr}>"
        elif hasattr(freecad_object, "Type"):
            # Constraints
            sketch_id, list_name, index = freecad_id
            id_str = f"({sketch_id},{list_name.value},{index})"
            constrained = self._constraint_map.get_constrained_ids(freecad_id)
            geometry_strings = []
            for geometry_id in constrained:
                sketch_id, list_name, index = geometry_id
                geometry_strings.append(
                    f"({sketch_id},{list_name.value},{index})"
                )
            geometry_str = "".join(geometry_strings)
            return (f"<ID:{id_str}-{geometry_str}'{freecad_object.Type}'"
                    f"{default_repr}>")
        else:
            # Geometry
            sketch_id, list_name, index = freecad_id
            id_str = f"({sketch_id},{list_name.value},{index})"
            return f"<ID:{id_str} {default_repr}>"
    
    def _get_pancad_by_uid(self, uid: UUID) -> PancadThing:
        """Returns a pancad object from the map that has the uid."""
        pancad_object, *_ = self._pancad_to_freecad[uid]
        return pancad_object
    
    # Python Dunders #
    def __contains__(self, key: PancadThing) -> bool:
        if isinstance(key, PancadThing):
            return key.uid in self._pancad_to_freecad
        else:
            return key in self._pancad_to_freecad
    
    def __delitem__(self, key) -> None:
        del self._pancad_to_freecad[key.uid]
    
    def __getitem__(self,
                    key: (PancadThing
                          | tuple[AbstractFeature | AbstractGeometry,
                                  ConstraintReference]
                          | UUID),
                    ) -> FreeCADCADObject:
        """Get item will only ever return FreeCAD objects from pancad objects
        and FreeCADIDs.
        """
        if isinstance(key, int):
            return self._feature_map[key]
        elif isinstance(key, tuple):
            # A tuple leads to a specific portion of a feature or geometry
            dispatch_key, *_ = key
            if isinstance(dispatch_key, PancadThing):
                # Get the freecad id corresponding to the PancadThing
                pancad_object, reference = key
                _, freecad_id = self._pancad_to_freecad[pancad_object.uid]
                if isinstance(freecad_id, int):
                    # Make a sub feature id
                    freecad_id = (freecad_id, reference)
                else:
                    # Make a sub geometry id
                    freecad_id = freecad_id + (reference,)
            elif isinstance(dispatch_key, UUID):
                uid, reference = key
                pancad_object = self._get_pancad_by_uid(uid)
                _, freecad_id = self._pancad_to_freecad[pancad_object.uid]
                if isinstance(freecad_id, int):
                    # Make a sub feature id
                    freecad_id = (freecad_id, reference)
                else:
                    # Make a sub geometry id
                    freecad_id = freecad_id + (reference,)
            else:
                # Just pass the id along
                freecad_id = dispatch_key
            
            freecad_id_type = self.get_id_type(freecad_id)
            if freecad_id_type in (FeatureID, SubFeatureID):
                return self._feature_map[freecad_id]
            elif freecad_id_type in (SketchElementID, SketchSubGeometryID):
                return self._geometry_map[freecad_id]
            else:
                raise TypeError(f"Key {key} type not recognized")
        elif isinstance(key, AbstractFeature):
            # An AbstractFeature by itself returns its CORE ConstraintReference
            _, feature_id = self._pancad_to_freecad[key.uid]
            return self._feature_map[feature_id, ConstraintReference.CORE]
        elif isinstance(key, AbstractGeometry):
            # An AbstractGeometry by itself returns its CORE ConstraintReference
            _, freecad_id = self._pancad_to_freecad[key.uid]
            return self._geometry_map[*freecad_id, ConstraintReference.CORE]
        elif isinstance(key, AbstractConstraint):
            _, freecad_id = self._pancad_to_freecad[key.uid]
            return self._constraint_map[freecad_id]
        elif isinstance(key, UUID):
            # A UUID by itself returns the CORE ConstraintReference of the
            # pancad object it refers to.
            pancad_object = self._get_pancad_by_uid(key)
            return self[pancad_object]
        else:
            raise ValueError(f"Key class {key.__class__} not recognized")
    
    def __iter__(self):
        self._iter_index = 0
        return self
    
    def __len__(self) -> int:
        return len(self._pancad_to_freecad)
    
    def __next__(self):
        if self._iter_index < len(self):
            i = self._iter_index
            self._iter_index += 1
            parent, _ = self._pancad_to_freecad[
                list(self._pancad_to_freecad)[i]
            ]
            return parent
        else:
            raise StopIteration
    
    def __setitem__(self, key: AbstractFeature, value: FreeCADFeature) -> None:
        if isinstance(key, AbstractFeature):
            self._link_features(key, value)
        else:
            raise TypeError("Given a non-feature element"
                            f" {value.__class__}. Geometry can only be"
                            " set as part of a feature (like Sketch).")
    
    def __repr__(self) -> str:
        from os.path import basename
        return (f"<FreeCADMap:'{self._part_file.filename}'"
                f"*'{basename(self._document.FileName)}'>")
    
    def __str__(self) -> str:
        """Returns a string summary of the FreeCAD mapping between pancad and 
        FreeCAD.
        """
        strings = []
        for key, value in self.items():
            if isinstance(key, (AbstractFeature, AbstractGeometry)):
                # Summarize Features and Geometry
                geometry_strings = []
                for reference in self.get_references(key):
                    freecad_id = self.get_freecad_id(key, reference)
                    freecad_repr = self._freecad_repr(freecad_id)
                    geometry_strings.append(
                        indent(f"{repr(key)}, {reference.name}: {freecad_repr}",
                               self.PREFIX)
                    )
                strings.append(",\n".join(geometry_strings))
            else:
                # Summarize Constraints
                freecad_id = self.get_freecad_id(key)
                freecad_repr = self._freecad_repr(freecad_id)
                strings.append(
                    indent(f"{repr(key)}: {freecad_repr}", self.PREFIX)
                )
            strings[-1] = strings[-1] + ","
        if strings:
            # Encapsulate output in curly brackets
            strings[0] = strings[0].removeprefix(self.PREFIX)
            return "{" + "\n".join(strings) + "}"
        else:
            return (f"{{Empty {self._part_file.filename} to"
                    f" {self._document.FileName} Mapping}}")

class _FreeCADIDMap(MutableMapping):
    """Used to map internally generated FreeCADIDs to Features, Geometry and 
    Constraints.
    """
    def __init__(self) -> None:
        self._id_to_object = dict()
    
    # Python Dunders #
    def __contains__(self, key: FreeCADID) -> bool:
        """Returns if a FreeCAD ID is in the map."""
        return key in self._id_to_object
    
    def __delitem__(self, key: FreeCADID) -> None:
        """Delete the feature in the key along with its subfeatures."""
        del self._id_to_object[FreeCADID]
    
    def __getitem__(self, key: FreeCADID) -> FreeCADCADObject:
        """Get the subfeature of a feature."""
        return self._id_to_object[key]
    
    def __iter__(self):
        return iter(self._id_to_object)
    
    def __len__(self) -> int:
        return len(self._id_to_object)
    
    def __setitem__(self, key: FreeCADID, value: FreeCADCADObject) -> None:
        self._id_to_object[key] = value
    
    def __str__(self) -> str:
        output_strings = []
        for freecad_id, value in self._id_to_object.items():
            output_strings.append(f"{freecad_id}: {value}")
        return "{" + ",\n ".join(output_strings) + "}"

class _FreeCADFeatureMap(MutableMapping):
    """Used to map features and their subfeatures in FreeCAD according to their
    feature id. Designed so that individual constraint reference mappings cannot 
    be directly modified, only the feature and subfeatures as a group.
    """
    def __init__(self, id_map: _FreeCADIDMap) -> None:
        self._features = dict()
        self._id_map = id_map
    
    # Public Methods #
    def get_freecad_id(self,
                       feature_id: FeatureID,
                       reference: ConstraintReference) -> FreeCADID:
        """Return the FreeCADID associated with the subgeometry of the Feature.
        
        :param feature_id: The ID assigned by FreeCAD to the feature.
        :param reference: The ConstraintReference of a subfeature associated 
            with the feature.
        """
        item = self._features[feature_id][reference]
        if isinstance(item, tuple):
            return item
        else:
            return self._features[feature_id][reference]
    
    def get_references(self,
                       feature_id: FeatureID) -> list[ConstraintReference]:
        """Returns a list of references to subgeometry available for the 
        FreeCAD feature.
        """
        return list(self._features[feature_id])
    
    def set_geometry_map(self, geometry_map: MutableMapping) -> Self:
        """Sets the internal reference to the higher level geometry map."""
        self._geometry_map = geometry_map
        return self
    
    def set_constraint_map(self,
                           constraint_map: MutableMapping) -> Self:
        """Sets the internal reference to the higher level constraint map."""
        self._constraint_map = constraint_map
        return self
    
    # Python Dunders #
    def __contains__(self, key: FeatureID | SubFeatureID) -> bool:
        """Returns if a feature id is in the map or if a pairing of a feature
        id and constraint reference are in the map.
        """
        if isinstance(key, tuple):
            feature_id, reference = key
            if feature_id in self._features:
                return reference in self._features[feature_id]
            else:
                return False
        elif isinstance(key, int):
            # Return if a sketch with the id of key has an element in the map
            return any([key == feature_id for feature_id in self._features])
        else:
            raise TypeError(f"Unrecognized input type {key.__class__}")
    
    def __delitem__(self, feature_id: FeatureID) -> None:
        del self._features[feature_id]
    
    def __getitem__(self, key: FeatureID | SubFeatureID) -> FreeCADCADObject:
        """Get the FreeCAD subfeature feature object of a feature."""
        if isinstance(key, int):
            # ConstraintReference is assumed to be CORE if no reference in the 
            # id.
            feature_id = key
            reference = ConstraintReference.CORE
        else:
            # Assumed to be a 2 long sequence
            feature_id, reference = key
        
        return self._id_map[self._features[feature_id][reference]]
    
    def __iter__(self):
        return iter(self._features)
    
    def __len__(self) -> int:
        return len(self._features)
    
    def __setitem__(self,
                    feature_id: FeatureID,
                    subfeatures: SubFeatureMap) -> None:
        self._features[feature_id] = subfeatures
    
    def __str__(self) -> str:
        """Provides a summary of the feature map."""
        output_strings = []
        for feature_id, subfeatures in self._features.items():
            output_strings.append(f"{feature_id}:")
            for reference, feature in subfeatures.items():
                output_strings.append(f"{{{reference}: {feature}}}")
        return "\n".join(output_strings)

class _FreeCADSketchGeometryMap(MutableMapping):
    """Used to map geometry in FreeCAD sketches according to their owning sketch 
    id and its equivalent constraint index and constraint references. Individual 
    constraint reference mappings cannot be directly modified, only the grouped 
    geometry.
    """
    def __init__(self,
                 id_map: _FreeCADIDMap,
                 feature_map: _FreeCADFeatureMap) -> None:
        self._id_map = id_map
        self._feature_map = feature_map
        self._feature_map.set_geometry_map(self)
        self._sketches = dict()
    
    # Public Methods #
    def get_freecad_id(self, key: SketchSubGeometryID) -> SketchElementID:
        """Returns the FreeCADID of a portion of the geometry. Example: The 
        major axis of an ellipse.
        """
        sketch_id, list_name, index, reference = key
        subgeometry_index = self._sketches[sketch_id][list_name][index][
            reference
        ]
        return (sketch_id, list_name, subgeometry_index)
    
    def get_references(self,
                       key: SketchElementID) -> tuple[ConstraintReference]:
        """Returns the ConstraintReferences associated with the provided 
        FreeCAD SketchElementID for a FreeCAD geometry object.
        """
        sketch_id, list_name, index = key
        return list(self._sketches[sketch_id][list_name][index])
    
    # Python Dunders #
    def __contains__(self,
                     key: FeatureID | SketchElementID | SketchSubGeometryID
                     ) -> bool:
        if isinstance(key, tuple):
            sketch_id, list_name, index, *_ = key
            if (sketch_id not in self._sketches
                    or list_name not in self._sketches[sketch_id]
                    or index not in self._sketches[sketch_id][list_name]):
                return False
            
            id_type = FreeCADMap.get_id_type(key)
            if id_type == SketchElementID:
                # Check if the geometry as a whole is in the map
                return True
            elif id_type == SketchSubGeometryID:
                # Check if the specific sub geometry is in the map
                *_, reference = key
                return reference in self._sketches[sketch_id][list_name][index]
            else:
                raise ValueError(f"Tuple key must be "
                                 f"{SketchElementID} or {SketchSubGeometryID}")
        elif isinstance(key, int):
            # Return if a sketch with the id of key has an element in the map
            return any([key == sketch_id for sketch_id, _ in self._sketches])
        else:
            raise TypeError(f"Unrecognized input type {key.__class__}")
    
    def __delitem__(self, key: SketchElementID) -> None:
        sketch_id, list_name, index = key
        del self._sketches[sketch_id][list_name][index]
    
    def __getitem__(self,
                    key: SketchElementID | SketchSubGeometryID
                    ) -> FreeCADCADObject:
        """Get the subgeometry of sketch geometry."""
        if FreeCADMap.get_id_type(key) == SketchElementID:
            # A reference to just the geometry index returns the CORE reference.
            sketch_id, list_name, index = key
            reference = ConstraintReference.CORE
        else:
            sketch_id, list_name, index, reference = key
        
        sub_index = self._sketches[sketch_id][list_name][index][reference]
        return self._id_map[sketch_id, list_name, sub_index]
    
    def __iter__(self):
        return iter(self._sketches)
    
    def __len__(self) -> int:
        return len(self._sketches)
    
    def __setitem__(self,
                    key: SketchElementID,
                    subgeometry: SubGeometryMap) -> None:
        """Sets a mapping of sub geometry to the parent geometry's id.
        
        :raises ValueError: Raised if the subgeometry does not have a CORE 
            ConstraintReference in it to map back to the parent.
        """
        if not isinstance(key, tuple):
            raise ValueError("Key must be tuple of sketch id and index."
                             f" Given {key}")
        
        sketch_id, list_name, index = key
        if sketch_id not in self._sketches:
            # When the sketch id is new, initialize a sketch dict
            self._sketches[sketch_id] = dict()
            self._sketches[sketch_id][ListName.EXTERNALS] = dict()
            self._sketches[sketch_id][ListName.GEOMETRY] = dict()
        
        if index not in self._sketches[sketch_id][list_name]:
            # When the index is new, initialize a index dict in the named list
            self._sketches[sketch_id][list_name][index] = dict()
        
        if ConstraintReference.CORE in subgeometry:
            self._sketches[sketch_id][list_name][index] = subgeometry
        else:
            raise ValueError("Subgeometry must contain a"
                             f" {ConstraintReference.CORE} reference")
    
    def __str__(self) -> str:
        output_strings = []
        for sketch, values in self._sketches.items():
            output_strings.append(f"{sketch}:")
            for index, geometry in values.items():
                output_strings.append(f"{{{index}: {geometry}}}")
        return "\n".join(output_strings)

class _FreeCADSketchConstraintMap(MutableMapping):
    """Used to map FreeCAD sketch constraints according to their owning
    sketch id and its constraint index.
    """
    PREFIX = "  "
    def __init__(self,
                 id_map: _FreeCADIDMap,
                 feature_map: _FreeCADFeatureMap,
                 sketch_map: _FreeCADSketchGeometryMap) -> None:
        self._id_map = id_map
        self._feature_map = feature_map
        self._feature_map.set_constraint_map(self)
        self._sketch_map = sketch_map
        self._sketches = dict()
    
    # Public Methods #
    def get_freecad_id(self, key: SketchElementID) -> SketchElementID:
        """Returns the FreeCADID of a constraint if it's in the map. For the 
        most part constraints will just echo the id back.
        """
        if key in self:
            return key
        else:
            raise LookupError(f"Key {key} is not in the map")
    
    def assign_internal_constraints(self, sketch_id: FeatureID) -> None:
        """Looks through the sketch and assigns the internal constraints to 
        their geometries. Used to make sure sketch mappings are up to date 
        after geometry like ellipses have been added.
        """
        sketch = self._id_map[sketch_id]
        if sketch_id not in self._sketches:
            self._add_new_sketch(sketch_id)
        
        internals = self._sketches[sketch_id][ListName.INTERNAL_ALIGNMENT]
        for index, constraint in enumerate(sketch.Constraints):
            if constraint.Type != ConstraintType.INTERNAL_ALIGNMENT:
                continue
            constraint_id = (sketch_id, ListName.INTERNAL_ALIGNMENT, index)
            self._id_map[constraint_id] = constraint
            parent_geometry_index = constraint.Second
            content = ElementTree.fromstring(constraint.Content)
            internal_alignment_type = InternalAlignmentType(
                int(content.attrib["InternalAlignmentType"])
            )
            
            if parent_geometry_index not in internals:
                internals[parent_geometry_index] = dict()
            internals[parent_geometry_index].update(
                {internal_alignment_type: constraint.First}
            )
    
    def get_constrained(self,
                        key: SketchElementID
                        ) -> tuple[FreeCADFeature | FreeCADGeometry]:
        """Returns the freecad geometry constrained by this constraint."""
        constrained_ids = self.get_constrained_ids(key)
        constrained = [self._id_map[freecad_id]
                       for freecad_id in constrained_ids]
        return tuple(constrained)
    
    def get_constrained_ids(self,
                            key: SketchElementID) -> tuple[SketchElementID]:
        """Returns the ids of the geometry constrained by the constraint with the 
        key id. Does not depend on the constraint being linked since this needs 
        to be run prior to linking objects.
        """
        sketch_id, _, index = key
        constraint = self._feature_map[sketch_id].Constraints[index]
        constrained = []
        indices = [constraint.First, constraint.Second, constraint.Third]
        for index in indices:
            if index != SketchNumber.UNUSED_CONSTRAINT_POSITION:
                # FreeCAD sets an index to magic number when not used.
                freecad_id = self._index_to_freecad_id(sketch_id, index)
                constrained.append(freecad_id)
            else:
                break
        return constrained
    
    def get_constrained_sub_parts(self,
                                  key: SketchElementID) -> tuple[EdgeSubPart]:
        """Returns the positions as defined by FreeCAD of the constraint 
        constraining its geometry. Does not depend on the constraint being 
        previously linked.
        """
        sketch_id, _, index = key
        constraint = self._feature_map[sketch_id].Constraints[index]
        positions = [constraint.FirstPos,
                     constraint.SecondPos,
                     constraint.ThirdPos]
        constrained_ids = self.get_constrained_ids(key)
        return tuple(map(EdgeSubPart, positions[:len(constrained_ids)]))
    
    def get_internal_geometry(self,
                              key: SketchElementID) -> InternalAlignmentMap:
        """Returns the internal geometry associated with the geometry element.
        """
        sketch_id, list_name, index = key
        # Refresh internals to make sure they have been assigned
        self.assign_internal_constraints(sketch_id)
        return self._sketches[sketch_id][ListName.INTERNAL_ALIGNMENT][index]
    
    def get_internal_alignment_type(self,
                                    key: SketchElementID
                                    ) -> InternalAlignmentType:
        """Returns the id of an internal geometry's parent geometry. Does 
        not depend on the constraint being previously linked.
        """
        sketch_id, list_name, index = key
        # Refresh internals to make sure they have been assigned
        self.assign_internal_constraints(sketch_id)
        internals = self._sketches[sketch_id][ListName.INTERNAL_ALIGNMENT]
        for _, internal_dict in internals.items():
            type_dict = {i: type_ for type_, i in internal_dict.items()}
            if index in type_dict:
                return type_dict[index]
        raise LookupError(f"{key} does not have parent geometry")
    
    def get_parent_geometry_id(self, key: SketchElementID) -> SketchElementID:
        """Returns the id of an internal geometry's parent geometry. Example: An 
        Ellipse's major axis line segment's FreeCADID would return the Ellipse's 
        FreeCADID. Does not depend on the constraint being previously linked.
        """
        sketch_id, list_name, index = key
        # Refresh internals to make sure they have been assigned
        self.assign_internal_constraints(sketch_id)
        internals = self._sketches[sketch_id][ListName.INTERNAL_ALIGNMENT]
        for parent_index, internal_dict in internals.items():
            internal_geometry_indices = [i for _, i in internal_dict.items()]
            if index in internal_geometry_indices:
                return (sketch_id, ListName.GEOMETRY, parent_index)
        raise LookupError(f"{key} does not have parent geometry")
    
    def is_internal_geometry(self, key: SketchElementID) -> bool:
        """Returns whether the geometry is FreeCAD internal geometry defining a 
        parent geometry element. Example: An Ellipse would return False, but its 
        major axis line segment would return True.
        """
        sketch_id, list_name, index = key
        # Refresh internals to make sure they have been assigned
        self.assign_internal_constraints(sketch_id)
        internal_geometry_indices = []
        internals = self._sketches[sketch_id][ListName.INTERNAL_ALIGNMENT]
        for _, internal_dict in internals.items():
            internal_geometry_indices.extend(
                [i for _, i in internal_dict.items()]
            )
        return index in internal_geometry_indices
    
    @staticmethod
    def get_constraint_index(freecad_id: SketchElementID) -> int:
        """Returns the index that a FreeCAD constraint would need to be defined. 
        Makes sure to use negative indices for ExternalGeo references.
        """
        _, list_name, index = freecad_id
        if list_name == ListName.EXTERNALS:
            return -index - 1
        else:
            return index
    
    # Private Methods #
    def _add_new_sketch(self, sketch_id: FeatureID):
        self._sketches[sketch_id] = dict()
        self._sketches[sketch_id][ListName.CONSTRAINTS] = dict()
        self._sketches[sketch_id][ListName.INTERNAL_ALIGNMENT] = dict()
    
    def _check_list_name(self, name: ListName) -> NoReturn:
        if name != ListName.CONSTRAINTS:
            raise ValueError(f"ListName {list_name} not recognized")
    
    # Private Static Methods #
    @staticmethod
    def _index_to_freecad_id(sketch_id: FeatureID, index: int):
        """Returns the freecad id associated with a constraint geometry 
        index. Positive numbers are in the Geometry list and negative 
        numbers are in the ExternalGeo list.
        """
        if index < 0:
            return (sketch_id, ListName.EXTERNALS, -(index + 1))
        else:
            return (sketch_id, ListName.GEOMETRY, index)
    
    # Python Dunders #
    def __contains__(self, key: FeatureID | SketchElementID) -> bool:
        if isinstance(key, tuple):
            sketch_id, list_name, index = key
            return (sketch_id in self._sketches
                    and list_name in self._sketches[sketch_id]
                    and index in self._sketches[sketch_id][list_name])
        elif isinstance(key, int):
            # Return if a sketch with the id of key has an element in the map
            return any([key == sketch_id for sketch_id, _ in self._sketches])
        else:
            raise TypeError(f"Unrecognized input type {key.__class__}")
    
    def __delitem__(self, key: SketchElementID) -> None:
        """Delete the geometry in the key along with its subgeometry."""
        sketch_id, list_name, index = key
        del self._sketches[sketch_id][list_name][index]
    
    def __getitem__(self, key: SketchElementID) -> FreeCADConstraint:
        """Get the constraint from the FreeCAD sketch."""
        if key in self:
            # Only return if it's in the map, even if it's in the FreeCAD
            # sketch.
            sketch_id, _, index = key
            return self._feature_map[sketch_id].Constraints[index]
        else:
            raise LookupError(f"No constraint found for {key}")
    
    def __iter__(self):
        return iter(self._sketches)
    
    def __len__(self) -> int:
        return len(self._sketches)
    
    def __setitem__(self,
                    key: SketchElementID,
                    value: tuple[SketchSubGeometryID]) -> None:
        sketch_id, list_name, index = key
        self._check_list_name(list_name)
        if sketch_id not in self._sketches:
            self._add_new_sketch(sketch_id)
        self._sketches[sketch_id][list_name][index] = value
    
    def __str__(self) -> str:
        output_strings = []
        for sketch, lists in self._sketches.items():
            sketch_strings = []
            sketch_strings.append(f"{sketch}:")
            for list_name, mapping in lists.items():
                list_strings = []
                list_strings.append(indent(f"{list_name.value}:", self.PREFIX))
                for index, value in mapping.items():
                    list_strings.append(indent(f"{index}: {value}",
                                               2*self.PREFIX))
                if len(list_strings) == 1:
                    list_strings.append(indent("None", 2*self.PREFIX))
                sketch_strings.append("\n".join(list_strings))
            output_strings.append("\n".join(sketch_strings))
        return "{" + "\n".join(output_strings) + "}"