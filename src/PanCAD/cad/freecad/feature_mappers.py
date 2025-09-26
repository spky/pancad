"""A module providing functions to map PanCAD features to FreeCAD features."""

from collections import defaultdict
from collections.abc import MutableMapping
from functools import singledispatch, singledispatchmethod
from typing import Self, NoReturn
from types import GenericAlias
from uuid import UUID
from xml.etree import ElementTree

from PanCAD.cad.freecad import (App, Sketcher, Part,
                                FreeCADBody,
                                FreeCADConstraint,
                                FreeCADFeature,
                                FreeCADGeometry,
                                FreeCADCADObject,
                                FreeCADOrigin,)
from PanCAD.cad.freecad.constants import (EdgeSubPart,
                                          ConstraintType,
                                          InternalAlignmentType,
                                          ListName,
                                          ObjectType,)
from PanCAD.cad.freecad.sketch_geometry import get_freecad_sketch_geometry
from PanCAD.cad.freecad.sketch_constraints import translate_constraint
from PanCAD.geometry import (PanCADThing,
                             AbstractGeometry,
                             AbstractFeature,
                             Circle,
                             CoordinateSystem,
                             Ellipse,
                             FeatureContainer,
                             LineSegment,
                             Sketch,
                             Extrude)
from PanCAD.geometry.constraints import AbstractConstraint
from PanCAD.geometry.constants import ConstraintReference

SketchGeometry = LineSegment | Circle
ToFreeCADLike = dict[AbstractGeometry
                     | AbstractFeature
                     | tuple[AbstractFeature | AbstractGeometry,
                             ConstraintReference],
                     object]
FromFreeCADLike = dict[object,
                       AbstractGeometry
                       | AbstractFeature
                       | tuple[AbstractFeature | AbstractGeometry,
                               ConstraintReference]]

# FreeCAD ID Typing
FeatureID = int
"""The ID that FreeCAD assigns to Features, usually a 4 digit integer."""
GeometryIndex = int
"""The index of a geometry element in a FreeCAD sketch's Geometry or ExternalGeo 
list. FreeCAD allows ExternalGeo elements to be referenced by constraints using 
negative numbers in addition to the normal Geometry elements in constraints.
"""
ConstraintIndex = int
"""The index of a constraint element in a FreeCAD sketch's Constraints list."""
SketchElementID = tuple[FeatureID, ListName, GeometryIndex]
"""The ID for a FreeCAD geometry or constraint element in a sketch."""
FreeCADID = FeatureID | SketchElementID
"""The unique ID for a FreeCADCADObject."""
SketchSubGeometryID = tuple[FeatureID,
                            ListName,
                            GeometryIndex,
                            ConstraintReference,]
"""The ID for a FreeCAD geometry element acting as the subgeometry of another
geometry element in the same sketch. The FeatureID has to be for a sketch.
"""
SubGeometryMap = dict[ConstraintReference, GeometryIndex]
"""Maps a constraint reference to another sketch index in the same sketch."""

SubFeatureID = tuple[FeatureID, ConstraintReference]
SubFeatureMap = dict[ConstraintReference, FreeCADID]

FreeCADIDMap = dict[FreeCADID, FreeCADCADObject]
"""Maps FreeCAD IDs to their corresponding FreeCADCADObject."""

@singledispatch
def map_freecad(pancad: AbstractGeometry,
                freecad: Part.Feature | App.DocumentObject | Sketcher.Sketch,
                from_freecad=False) -> ToFreeCADLike | FromFreeCADLike:
    """Returns a dict that maps pancad (geometry or feature, reference) tuples
    to a freecad object.
    
    :param pancad: A PanCAD object.
    :param freecad: A FreeCAD object.
    :param from_freecad: Reverses the dictionary if True. Defaults to False.
    :param parent_sketch: The sketch the pancad object is in. Only used for
        sketch geometry. Not to be used for other options.
    :param index: The sketch index of the pancad object. Only used for sketch
        geometry.
    :returns: A dict mapping the geometry and its sub geometry to the freecad
        object.
    """
    raise TypeError(f"Unsupported PanCAD element: {pancad}")

def _get_ordered_map(feature_map: dict, from_freecad: bool) -> dict:
    """Reverses or returns a mapping dictionary based on whether the map is to
    or from freecad.

    :param feature_map: A dictionary mapping PanCAD elements to FreeCAD
        elements.
    :param from_freecad: Whether the map is intended to go from FreeCAD or to
        FreeCAD. If True, the map is reversed.
    :returns: The correctly ordered mapping dictionary.
    """
    if from_freecad:
        return {freecad: pancad for pancad, freecad in feature_map.items()}
    else:
        return feature_map

@map_freecad.register
def _coordinate_system(coordinate_system: CoordinateSystem,
                       origin: App.DocumentObject,
                       from_freecad: bool=False) -> dict:
    map_to_freecad = { # Assumes FreeCAD maintains the same order in the future
        (coordinate_system, ConstraintReference.ORIGIN): origin,
        (coordinate_system, ConstraintReference.X): origin.OriginFeatures[0],
        (coordinate_system, ConstraintReference.Y): origin.OriginFeatures[1],
        (coordinate_system, ConstraintReference.Z): origin.OriginFeatures[2],
        (coordinate_system, ConstraintReference.XY): origin.OriginFeatures[3],
        (coordinate_system, ConstraintReference.XZ): origin.OriginFeatures[4],
        (coordinate_system, ConstraintReference.YZ): origin.OriginFeatures[5],
    }
    return _get_ordered_map(map_to_freecad, from_freecad)

@map_freecad.register
def _extrude(pancad_extrude: Extrude,
             freecad_extrude: Part.Feature,
             from_freecad: bool=False) -> dict:
    map_to_freecad = {pancad_extrude: freecad_extrude}
    return _get_ordered_map(map_to_freecad, from_freecad)

@map_freecad.register
def _sketch(pancad_sketch: Sketch,
            freecad_sketch: Sketcher.Sketch,
            from_freecad: bool=False) -> dict:
    map_to_freecad = {(pancad_sketch, ConstraintReference.CORE): freecad_sketch}
    return _get_ordered_map(map_to_freecad, from_freecad)

@map_freecad.register
def _sketch_geometry(pancad_geometry: SketchGeometry,
                     freecad_geometry: object,
                     from_freecad: bool,
                     parent_sketch: Sketch,
                     index: int) -> dict:
    map_to_freecad = {(parent_sketch, "geometry", index): freecad_geometry}
    return _get_ordered_map(map_to_freecad, from_freecad)

class FreeCADMap(MutableMapping):
    """A class implementing a custom mapping between PanCAD elements and FreeCAD
    elements.
    
    :param document: The freecad document being mapped to or from.
    :param writing_map: Sets whether the map is for writing to FreeCAD or
        reading from FreeCAD. A writing map will have PanCAD objects as keys and
        FreeCAD objects as values, and a reading map will reverse those roles.
    """
    
    def __init__(self, document: App.Document, writing_map: bool=True) -> None:
        self._writing_map = writing_map
        self._document = document
    
        self._pancad_to_freecad = dict()
        # Maps from PanCAD objects to their associated FreeCAD objects
        self._freecad_to_pancad = dict()
        # Maps from FreeCAD IDs to their associated PanCAD objects
        
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
    
    # Python Dunders #
    def __contains__(self, key: PanCADThing) -> bool:
        if isinstance(key, PanCADThing):
            return key.uid in self._pancad_to_freecad
        else:
            return key in self._pancad_to_freecad
    
    def __delitem__(self, key) -> None:
        del self._pancad_to_freecad[key.uid]
    
    def __getitem__(self,
                    key: PanCADThing | tuple[PanCADThing, ConstraintReference],
                    ) -> FreeCADCADObject:
        """Get item will only ever return FreeCAD objects from PanCAD objects
        and FreeCADIDs.
        """
        if isinstance(key, int):
            return self._feature_map[key]
        elif isinstance(key, tuple):
            # A tuple leads to a specific portion of a feature or geometry
            dispatch_key, *_ = key
            if isinstance(dispatch_key, PanCADThing):
                # Get the freecad id corresponding to the PanCADThing
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
            # PanCAD object it refers to.
            pancad_object = self._get_pancad_by_uid(key)
            return self[pancad_object]
        else:
            raise ValueError(f"Key class {key.__class__} not recognized")
    
    def __iter__(self):
        self._iter_index = 0
        return self
    
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

    def __len__(self) -> int:
        return len(self._pancad_to_freecad)

    def __setitem__(self,
                    key: PanCADThing,
                    value: FreeCADCADObject) -> None:
        # Writing **TO** FreeCAD
        if isinstance(key, AbstractFeature):
            self._link_pancad_to_freecad_feature(key, value)
        else:
            raise TypeError("Given a non-feature element"
                            f" {value.__class__}. Geometry can only be"
                            " set as part of a feature (like Sketch).")
    
    def __str__(self) -> str:
        from textwrap import indent
        PREFIX = " "
        strings = []
        for key, value in self.items():
            if isinstance(key, (AbstractFeature, AbstractGeometry)):
                geometry_strings = []
                for reference in self.get_references(key):
                    freecad_id = self.get_freecad_id(key, reference)
                    freecad_repr = self._freecad_repr(freecad_id)
                    geometry_strings.append(
                        indent(f"{repr(key)}, {reference.name}: {freecad_repr}",
                               PREFIX)
                    )
                strings.append(",\n".join(geometry_strings))
            else:
                freecad_id = self.get_freecad_id(key)
                freecad_repr = self._freecad_repr(freecad_id)
                strings.append(
                    indent(f"{repr(key)}: {freecad_repr}", PREFIX)
                )
            strings[-1] = strings[-1] + ","
        strings[0] = strings[0].removeprefix(PREFIX)
        return "{" + "\n".join(strings) + "}"
    
    # Public Methods #
    
    ### Adding FreeCAD Features ###
    def add_freecad_feature(self, feature: FreeCADFeature) -> Self:
        match feature.TypeId:
            # Poor man's singledispatchmethod using the FreeCAD TypeId
            case ObjectType.BODY:
                self._add_freecad_body(feature)
            case ObjectType.SKETCH:
                pass
            case ObjectType.PAD:
                pass
            case ObjectType.ORIGIN:
                pass
        return self
    
    def _add_freecad_body(self, feature: FreeCADFeature):
        
        if feature.Parents:
            parents = []
            for freecad_object, _ in feature.Parents:
                if freecad_object.ID not in parents:
                    parents.append(freecad_object.ID)
            
            # if len(parents) > 1:
                # raise ValueError("Unknown situation where FreeCAD object has"
                                 # " two unique parents! Please make a github"
                                 # " issue so it can be supported.")
            # elif 
            
        else:
            context = None
        container = FeatureContainer(name=feature.Label)
    
    ### Adding PanCAD Features ###
    @singledispatchmethod
    def add_pancad_feature(self, feature: AbstractFeature) -> NoReturn:
        raise TypeError(f"Unrecognized feature type: {feature}")
    
    @add_pancad_feature.register
    def _feature_container(self, container: FeatureContainer) -> Self:
        body = self._document.addObject(ObjectType.BODY, container.name)
        self[container] = body
        if (len(container.features) > 0
            and isinstance(container.features[0], CoordinateSystem)):
            # If the first feature in the feature container is a coordinate
            # system, it can be assumed that this is a valid context for other
            # features to be added into.
            features = iter(container.features)
            coordinate_system = next(features)
            self[coordinate_system] = body.Origin
            for feature in features:
                self.add_pancad_feature(feature)
            return self
    
    @add_pancad_feature.register
    def _sketch(self, sketch: Sketch) -> Self:
        self[sketch] = self._document.addObject(ObjectType.SKETCH, sketch.name)
        return self
    
    @add_pancad_feature.register
    def _extrude(self, extrude: Extrude) -> Self:
        self[extrude] = self._document.addObject(ObjectType.PAD, extrude.name)
        return self
    
    def get_pancad(self, freecad_id: FreeCADID) -> tuple[PanCADThing,
                                                         ConstraintReference]:
        """Returns the PanCAD object and constraint reference mapped to the 
        FreeCAD ID.
        """
        freecad_id_type = self.get_id_type(freecad_id)
        
        if freecad_id_type in (FeatureID, SubFeatureID):
            self._feature_map[freecad_id]
        elif freecad_id_type in (SketchElementID, SketchSubGeometryID):
            self._geometry_map[freecad_id]
        else:
            raise TypeError(f"Key {key} type not recognized")
    
    def get_references(self, key: PanCADThing) -> list[ConstraintReference]:
        """Returns a tuple of the references available for the key."""
        if isinstance(key, AbstractFeature):
            feature = self[key]
            return self._feature_map.get_references(feature.ID)
        elif isinstance(key, AbstractGeometry):
            freecad_id = self.get_freecad_id(key)
            return self._geometry_map.get_references(freecad_id)
        else:
            raise TypeError("Can only return references for Features and"
                            " Geometry")
    
    def get_freecad_id(self,
                       key: PanCADThing,
                       reference: ConstraintReference=ConstraintReference.CORE,
                       ) -> FreeCADID:
        _, freecad_id = self._pancad_to_freecad[key.uid]
        if isinstance(key, AbstractFeature):
            return self._feature_map.get_freecad_id(freecad_id, reference)
        elif isinstance(key, AbstractGeometry):
            return self._geometry_map.get_freecad_id(freecad_id + (reference,))
        else:
            return freecad_id
    
    def freecad_to_pancad_summary(self) -> str:
        """Returns a string summary of the mapping from freecad to pancad. 
        Intended to be the reversed viewpoint of __str__.
        """
        from textwrap import indent
        PREFIX = " "
        strings = []
        for freecad_id, (uid, reference) in self._freecad_to_pancad.items():
            freecad_repr = self._freecad_repr(freecad_id)
            pancad_object = self._get_pancad_by_uid(uid)
            strings.append(
                indent(
                    f"{freecad_repr}: {repr(pancad_object)}, {reference.name}",
                    PREFIX
                )
            )
            strings[-1] = strings[-1] + ","
        strings[0] = strings[0].removeprefix(PREFIX)
        return "{" + "\n".join(strings) + "}"
    
    # Public static methods
    @staticmethod
    def get_id_type(key: int | tuple) -> GenericAlias:
        """Returns the type of the input key."""
        
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
    
    
    # Private Methods #
    
    def _get_pancad_by_uid(self, uid: UUID) -> PanCADThing:
        """Returns a PanCAD object from the map that has the uid."""
        pancad_object, *_ = self._pancad_to_freecad[uid]
        return pancad_object
    
    def _freecad_repr(self, freecad_id: FreeCADID) -> str:
        """Returns a string representing the freecad object."""
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
    
    @singledispatchmethod
    def _link_pancad_to_freecad_feature(self,
                                        key: PanCADThing,
                                        value: FreeCADCADObject):
        """Adds a PanCAD parent and FreeCAD child feature pairing to the map.
        Each key is the PanCAD element's uid, mapped to a tuple with the PanCAD
        parent will be the first element and the FreeCAD feature ID as the
        second element.
        """
        raise TypeError(f"Unrecognized PanCAD geometry type {key.__class__}")

    @_link_pancad_to_freecad_feature.register
    def _coordinate_system(self,
                           key: CoordinateSystem,
                           origin: FreeCADOrigin) -> None:
        subelements = {ConstraintReference.CORE: origin.ID,
                       ConstraintReference.ORIGIN: origin.ID}
        subreferences = [ConstraintReference.X,
                         ConstraintReference.Y,
                         ConstraintReference.Z,
                         ConstraintReference.XY,
                         ConstraintReference.XZ,
                         ConstraintReference.YZ]
        for i, reference in enumerate(subreferences):
            subreference_id = origin.OriginFeatures[i].ID
            self._id_map[subreference_id] = origin.OriginFeatures[i]
            subelements.update({reference: subreference_id})
        
        self._id_map[origin.ID] = origin
        self._feature_map[origin.ID] = subelements
        self._pancad_to_freecad[key.uid] = (key, origin.ID)
        
        # Map back to PanCAD
        reversed_subelements = dict()
        for reference, feature_id in subelements.items():
            if feature_id not in reversed_subelements:
                # Will skip the ORIGIN reference since that is a duplicate.
                reversed_subelements.update({feature_id: (key.uid, reference)})
        self._freecad_to_pancad.update(reversed_subelements)

    @_link_pancad_to_freecad_feature.register
    def _extrude(self, key: Extrude, pad: Part.Feature) -> None:
        # Add to corresponding parent
        parent = self[key.context]
        parent.addObject(pad)
        # Sync properties with PanCAD
        pad.Profile = (self[key.profile], [""])
        pad.Length = key.length
        pad.ReferenceAxis = (self[key.profile], ["N_Axis"])
        self[key.profile].Visibility = False
        # Add to maps
        self._id_map[pad.ID] = pad
        self._feature_map[pad.ID] = {ConstraintReference.CORE: pad.ID}
        self._pancad_to_freecad[key.uid] = (key, pad.ID)
        self._freecad_to_pancad[pad.ID] = (key.uid, ConstraintReference.CORE)
    
    @_link_pancad_to_freecad_feature.register
    def _feature_container(self,
                           key: FeatureContainer,
                           body: Part.BodyBase) -> None:
        self._id_map[body.ID] = body
        self._feature_map[body.ID] = {ConstraintReference.CORE: body.ID}
        self._pancad_to_freecad[key.uid] = (key, body.ID)
        self._freecad_to_pancad[body.ID] = (key.uid, ConstraintReference.CORE)
    
    @_link_pancad_to_freecad_feature.register
    def _sketch(self, key: Sketch, sketch: Sketcher.Sketch) -> None:
        # Sync properties with PanCAD
        sketch_plane = self[key.coordinate_system, key.plane_reference]
        sketch.AttachmentSupport = (sketch_plane, [""])
        sketch.MapMode = "FlatFace"
        sketch.Label = key.name
        parent = self[key.context]
        parent.addObject(sketch)
        
        # Map Feature
        self._id_map[sketch.ID] = sketch
        self._pancad_to_freecad[key.uid] = (key, sketch.ID)
        
        y_axis_id = (sketch.ID, ListName.EXTERNALS, 1)
        x_axis_id = (sketch.ID, ListName.EXTERNALS, 0)
        subelements = {ConstraintReference.CORE: sketch.ID,
                       ConstraintReference.ORIGIN: x_axis_id,
                       ConstraintReference.X: x_axis_id,
                       ConstraintReference.Y: y_axis_id,}
        self._feature_map[sketch.ID] = subelements
        self._freecad_to_pancad.update(
            {freecad_id: (key.uid, reference)
             for reference, freecad_id in subelements.items()}
        )
        
        # Map the geometry inside of the sketch
        line_references = [ConstraintReference.CORE, ConstraintReference.START,
                           ConstraintReference.END]
        y_references = dict()
        x_references = dict()
        for reference in line_references:
            x_references[reference] = 0
            y_references[reference] = 1
        self._id_map[x_axis_id] = sketch.ExternalGeo[0]
        self._id_map[y_axis_id] = sketch.ExternalGeo[1]
        self._geometry_map[x_axis_id] = x_references
        self._geometry_map[y_axis_id] = y_references
        
        for geometry, construction in zip(key.geometry, key.construction):
            self._link_pancad_to_freecad_geometry(geometry,
                                                  sketch,
                                                  construction)
        
        for constraint in key.constraints:
            constraint_index = len(sketch.Constraints)
            new_constraint = translate_constraint(key, constraint)
            sketch.addConstraint(new_constraint)
            constraint_id = (sketch.ID, ListName.CONSTRAINTS, constraint_index)
            constrained_ids = tuple()
            for parent, reference in zip(constraint.get_constrained(),
                                         constraint.get_references()):
                sketch_geometry_id = self.get_freecad_id(parent, reference)
                constrained_ids = constrained_ids + (
                    (*sketch_geometry_id, reference),
                )
            self._pancad_to_freecad[constraint.uid] = (constraint,
                                                       constraint_id)
            self._freecad_to_pancad[constraint_id] = (constraint.uid,
                                                      ConstraintReference.CORE)
            self._id_map[constraint_id] = new_constraint
            self._constraint_map[constraint_id] = constrained_ids
    
    @singledispatchmethod
    def _link_pancad_to_freecad_geometry(self,
                                         pancad_geometry: AbstractGeometry,
                                         sketch: Sketcher.Sketch,
                                         construction: bool,
                                         geometry_index: int) -> NoReturn:
        
        """Adds the PanCAD geometry to the FreeCAD sketch while also mapping 
        the relations between the new geometry and constraints to PanCAD 
        geometry.
        
        :param pancad_geometry: A PanCAD AbstractGeometry object.
        :param sketch: A FreeCAD sketch.
        :param construction: Sets the geometry to construction is True, 
            non-construction if False.
        :param geometry_index: The index to set the geometry to in the 
            FreeCAD sketch.
        :param constraint_id: The index for the next constraint, if any will 
            be added.
        :returns: The new geometry_index.
        """
        raise TypeError(f"Geometry class {pancad_geometry.__class__}"
                        " not recognized")
    
    @_link_pancad_to_freecad_geometry.register
    def _ellipse(self,
                 pancad_geometry: Ellipse,
                 sketch: Sketcher.Sketch,
                 construction: bool) -> None:
        geometry_index = len(sketch.Geometry)
        geometry = get_freecad_sketch_geometry(pancad_geometry)
        ellipse_id = (sketch.ID, ListName.GEOMETRY, geometry_index)
        sketch.addGeometry(geometry, construction)
        sketch.exposeInternalGeometry(geometry_index)
        
        # Map newly created Internal Geometry
        subgeometry = dict()
        ellipse_references = [
            (ConstraintReference.CORE, geometry_index),
            (ConstraintReference.CENTER, geometry_index),
            (ConstraintReference.X, geometry_index + 1),
            (ConstraintReference.X_MAX, geometry_index + 1),
            (ConstraintReference.X_MIN, geometry_index + 1),
            (ConstraintReference.Y, geometry_index + 2),
            (ConstraintReference.Y_MAX, geometry_index + 2),
            (ConstraintReference.Y_MIN, geometry_index + 2),
            (ConstraintReference.FOCAL_PLUS, geometry_index + 3),
            (ConstraintReference.FOCAL_MINUS, geometry_index + 4),
        ]
        DUPLICATED_REFERENCES = [ConstraintReference.CENTER,
                                 ConstraintReference.X_MAX,
                                 ConstraintReference.X_MIN,
                                 ConstraintReference.Y_MAX,
                                 ConstraintReference.Y_MIN,]
        # References that refer to the same geometry as already defined 
        # references, only there for PanCAD to know what to read so it won't 
        # have a FreeCAD to PanCAD mapping
        
        for reference, sub_index in ellipse_references:
            sub_id = (sketch.ID, ListName.GEOMETRY, sub_index)
            self._id_map[sub_id] = sketch.Geometry[sub_index]
            self._geometry_map[sub_id] = {ConstraintReference.CORE: sub_index}
            subgeometry[reference] = sub_index
            
            if reference not in  DUPLICATED_REFERENCES:
                self._freecad_to_pancad[sub_id] = (pancad_geometry.uid,
                                                   reference)
        
        self._constraint_map.assign_internal_constraints(sketch.ID)
        self._id_map[ellipse_id] = geometry
        self._geometry_map[ellipse_id] = subgeometry
        self._pancad_to_freecad[pancad_geometry.uid] = (pancad_geometry,
                                                        ellipse_id)
    
    @_link_pancad_to_freecad_geometry.register
    def _one_to_one(self,
                    pancad_geometry: LineSegment | Circle,
                    sketch: Sketcher.Sketch,
                    construction: bool) -> None:
        # Handles cases where the geometry in PanCAD is one to one with 
        # geometry in FreeCAD.
        geometry_index = len(sketch.Geometry)
        geometry = get_freecad_sketch_geometry(pancad_geometry)
        sketch.addGeometry(geometry, construction)
        geometry_id = (sketch.ID, ListName.GEOMETRY, geometry_index)
        self._id_map[geometry_id] = geometry
        self._pancad_to_freecad[pancad_geometry.uid] = (pancad_geometry,
                                                        geometry_id)
        self._freecad_to_pancad[geometry_id] = (pancad_geometry.uid,
                                                ConstraintReference.CORE)
        reference_map = dict()
        for reference in pancad_geometry.get_all_references():
            reference_map[reference] = geometry_index
        self._geometry_map[geometry_id] = reference_map

class _FreeCADIDMap(MutableMapping):
    """Used to map FreeCAD IDs to Features, Geometry and Constraints."""
    
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
    feature id. Individual constraint reference mappings cannot be directly
    modified, only the grouped feature and subfeatures all at once.
    """
    
    def __init__(self, id_map: _FreeCADIDMap) -> None:
        self._features = dict()
        self._id_map = id_map
    
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
        """Delete the feature in the key along with its subfeatures."""
        del self._features[feature_id]
    
    def __getitem__(self, key: FeatureID | SubFeatureID) -> FreeCADCADObject:
        """Get the subfeature of a feature."""
        if isinstance(key, int):
            # ConstraintReference is assumed to be CORE
            feature_id = key
            reference = ConstraintReference.CORE
        else:
            feature_id, reference = key
        
        return self._id_map[self._features[feature_id][reference]]
    
    def __iter__(self):
        return iter(self._features)
    
    def __len__(self) -> int:
        return len(self._features)
    
    def __setitem__(self,
                    feature_id: int,
                    subfeatures: SubFeatureMap) -> None:
        self._features[feature_id] = subfeatures
    
    def __str__(self) -> str:
        output_strings = []
        for feature_id, subfeatures in self._features.items():
            output_strings.append(f"{feature_id}:")
            for reference, feature in subfeatures.items():
                output_strings.append(f"{{{reference}: {feature}}}")
        return "\n".join(output_strings)
    
    # Public Methods #
    def get_freecad_id(self,
                       feature_id: int,
                       reference: ConstraintReference) -> FreeCADID:
        item = self._features[feature_id][reference]
        if isinstance(item, tuple):
            return item
        else:
            return self._features[feature_id][reference]
    
    def get_references(self, feature_id: int) -> list[ConstraintReference]:
        """Returns a list of references available for the feature_id."""
        return list(self._features[feature_id])
    
    def set_geometry_map(self, geometry_map: MutableMapping) -> Self:
        """Sets the internal reference to the geometry map."""
        self._geometry_map = geometry_map
    
    def set_constraint_map(self,
                           constraint_map: MutableMapping) -> Self:
        """Sets the internal reference to the constraint map."""
        self._constraint_map = constraint_map

class _FreeCADSketchGeometryMap(MutableMapping):
    """Used to map geometry and constraints in FreeCAD sketches according to
    their owning sketch id and its equivalent constraint index and constraint
    references. Individual constraint reference mappings cannot be directly
    modified, only the grouped geometry.
    """
    
    def __init__(self,
                 id_map: _FreeCADIDMap,
                 feature_map: _FreeCADFeatureMap,) -> None:
        self._id_map = id_map
        self._feature_map = feature_map
        self._feature_map.set_geometry_map(self)
        self._sketches = dict()
    
    # Public Methods #
    def get_freecad_id(self, key: SketchSubGeometryID) -> SketchElementID:
        sketch_id, list_name, index, reference = key
        subgeometry_index = self._sketches[sketch_id][list_name][index][
            reference
        ]
        return (sketch_id, list_name, subgeometry_index)
    
    def get_sketch_indices(self, sketch_id: int) -> dict:
        """Returns a dictionary of indices to the constraint or geometry in the
        sketch.
        """
        return self._sketches[sketch_id]
    
    def get_references(self,
                       key: SketchElementID) -> tuple[ConstraintReference]:
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
            elif len(key) == 3:
                # Check if the geometry as a whole is in the map
                return True
            elif len(key) == 4:
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
        """Delete the geometry in the key along with its subgeometry."""
        sketch_id, list_name, index = key
        del self._sketches[sketch_id][list_name][index]
    
    def __getitem__(self, key: SketchElementID | SketchSubGeometryID
                    ) -> FreeCADCADObject:
        """Get the subgeometry of sketch geometry."""
        if len(key) == 3:
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
                             " ConstraintReference.CORE reference")
    
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
        if key in self:
            return key
        else:
            raise LookupError(f"Key {key} is not in the map")
    
    def assign_internal_constraints(self, sketch_id: FeatureID) -> Self:
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
            
            parent_geometry_index = constraint.Second
            content = ElementTree.fromstring(constraint.Content)
            internal_alignment_type = InternalAlignmentType(
                int(content.attrib["InternalAlignmentType"])
            )
            
            if parent_geometry_index not in internals:
                internals[parent_geometry_index] = dict()
            internals[parent_geometry_index].update(
                {internal_alignment_type: index}
            )
    
    def get_constrained(self,
                        key: SketchElementID) -> tuple[FreeCADCADObject]:
        """Returns the freecad geometry constrained by this constraint."""
        constrained_ids = self.get_constrained_ids(key)
        constrained = [
            self._id_map[freecad_id] for freecad_id in constrained_ids
        ]
        return tuple(constrained)
    
    def get_constrained_ids(self,
                            key: SketchElementID) -> tuple[SketchElementID]:
        """Returns the ids of the geometry constrained by this constraint."""
        if key not in self:
            raise LookupError(f"No constraint found for {key}")
        
        sketch_id, _, index = key
        constraint = self._feature_map[sketch_id].Constraints[index]
        constrained = []
        indices = [constraint.First, constraint.Second, constraint.Third]
        for index in indices:
            if index != -2000:
                freecad_id = self._index_to_freecad_id(sketch_id, index)
                constrained.append(freecad_id)
            else:
                break
        return constrained
    
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
                    value: SketchSubGeometryID) -> None:
        sketch_id, list_name, index = key
        self._check_list_name(list_name)
        if sketch_id not in self._sketches:
            self._add_new_sketch(sketch_id)
        self._sketches[sketch_id][list_name][index] = value
    
    def __str__(self) -> str:
        from textwrap import indent
        PREFIX = "  "
        output_strings = []
        for sketch, lists in self._sketches.items():
            sketch_strings = []
            sketch_strings.append(f"{sketch}:")
            for list_name, mapping in lists.items():
                list_strings = []
                list_strings.append(indent(f"{list_name.value}:", PREFIX))
                for index, value in mapping.items():
                    list_strings.append(indent(f"{index}: {value}", 2*PREFIX))
                if len(list_strings) == 1:
                    list_strings.append(indent("None", 2*PREFIX))
                sketch_strings.append("\n".join(list_strings))
            output_strings.append("\n".join(sketch_strings))
        return "{" + "\n".join(output_strings) + "}"
    
    # Private Methods #
    def _add_new_sketch(self, sketch_id: FeatureID):
        self._sketches[sketch_id] = dict()
        self._sketches[sketch_id][ListName.CONSTRAINTS] = dict()
        self._sketches[sketch_id][ListName.INTERNAL_ALIGNMENT] = dict()
    
    def _check_list_name(self, name: ListName) -> NoReturn:
        if name != ListName.CONSTRAINTS:
            raise ValueError(f"ListName {list_name} not recognized")
    
    def _index_to_freecad_id(self, sketch_id: FeatureID, index: int):
        """Returns the freecad id associated with a constraint geometry 
        index. Positive numbers are in the Geometry list and negative 
        numbers are in the ExternalGeo list.
        """
        if index < 0:
            return (sketch_id, ListName.EXTERNALS, -(index + 1))
        else:
            return (sketch_id, ListName.GEOMETRY, index)
