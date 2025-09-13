"""A module providing functions to map PanCAD features to FreeCAD features."""

from collections import defaultdict
from collections.abc import MutableMapping
from functools import singledispatch, singledispatchmethod
from typing import Self
from uuid import UUID

from PanCAD.cad.freecad import App, Sketcher, Part, FreeCADFeature
from PanCAD.cad.freecad.constants import ObjectType
from PanCAD.cad.freecad.sketch_geometry import get_freecad_sketch_geometry
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
        
        self._mapping = dict()
        # Map from the PanCAD/FreeCAD object to the FreeCAD/PanCAD one
        self._feature_map = _FreeCADFeatureMap()
        # Maps freecad ids to their features
        self._geometry_map = _FreeCADSketchGeometryMap(self._feature_map)
        # Maps freecad sketch ids to their contained geometry
    
    # Python Dunders #
    def __contains__(self, key: object | PanCADThing) -> bool:
        if isinstance(key, PanCADThing):
            return key.uid in self._mapping
        else:
            return key in self._mapping
    
    def __delitem__(self, key) -> None:
        del self._mapping[key.uid]
    
    def __getitem__(self,
                    key: PanCADThing | tuple[PanCADThing, ConstraintReference],
                    ) -> object:
        if isinstance(key, tuple):
            # A tuple leads to a specific portion of a feature or geometry
            pancad_object, reference = key
            _, freecad_id = self._mapping[pancad_object.uid]
            if isinstance(freecad_id, int):
                # An int leads to a FreeCAD feature with an ID
                return self._feature_map[freecad_id, reference]
            elif isinstance(freecad_id, tuple):
                # A tuple leads to FreeCAD geometry inside of a sketch
                feature_id, geometry_index  = freecad_id
                return self._geometry_map[feature_id, geometry_index, reference]
        elif isinstance(key, AbstractFeature):
            # An AbstractFeature by itself returns its CORE ConstraintReference
            _, feature_id = self._mapping[key.uid]
            return self._feature_map[feature_id, ConstraintReference.CORE]
        elif isinstance(key, AbstractGeometry):
            # An AbstractGeometry by itself returns its CORE ConstraintReference
            _, (feature_id, geometry_index) = self._mapping[key.uid]
            return self._geometry_map[feature_id,
                                      geometry_index,
                                      ConstraintReference.CORE]
        elif isinstance(key, UUID):
            # A UUID by itself returns the CORE ConstraintReference of the 
            # PanCAD object it refers to.
            pancad_object = self._get_pancad_by_uid(key)
            return self[pancad_object]
        else:
            raise ValueError(f"Key class {key.__class__} not recognized")
        return value
    
    def __iter__(self):
        self._iter_index = 0
        return self
    
    def __next__(self):
        if self._iter_index < len(self):
            i = self._iter_index
            self._iter_index += 1
            parent, _ = self._mapping[list(self._mapping)[i]]
            return parent
        else:
            raise StopIteration
    
    def __len__(self) -> int:
        return len(self._mapping)
    
    def __setitem__(self,
                    key: object | PanCADThing,
                    value: PanCADThing | object) -> None:
        if self._writing_map:
            # Writing **TO** FreeCAD
            if isinstance(key, AbstractFeature):
                self._link_pancad_to_freecad_feature(key, value)
            else:
                raise TypeError("Given a non-feature element"
                                f" {value.__class__}. Geometry can only be"
                                " set as part of a feature (like Sketch).")
        else:
            if not isinstance(key, PanCADThing):
                self._mapping[key] = (key, value)
            else:
                raise TypeError("Reading map keys cannot be PanCAD objects,"
                                f" given: {key}")
    
    def __str__(self) -> str:
        strings = []
        for key, value in self.items():
            for reference in self.get_references(key):
                freecad_id = self.get_freecad_id(key, reference)
                freecad_repr = self._freecad_repr(freecad_id, self[key, reference])
                strings.append(f" {repr(key)}, {reference}: {freecad_repr},")
        strings[-1] = strings[-1] + "}"
        return "\n".join(strings)
    
    # Public Methods #
    @singledispatchmethod
    def add_pancad_feature(self, feature: AbstractFeature) -> Self:
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
    
    def get_references(self, key: PanCADThing) -> list[ConstraintReference]:
        """Returns a tuple of the references available for the key."""
        if isinstance(key, AbstractFeature):
            feature = self[key]
            return self._feature_map.get_references(feature.ID)
        elif isinstance(key, AbstractGeometry):
            freecad_id = self.get_freecad_id(key)
            return self._geometry_map.get_references(freecad_id)
    
    def get_freecad_id(self,
                       key: PanCADThing,
                       reference: ConstraintReference=ConstraintReference.CORE,
                       ) -> int | tuple[int, int]:
        _, freecad_id = self._mapping[key.uid]
        if isinstance(key, AbstractFeature):
            return self._feature_map.get_freecad_id(freecad_id, reference)
        else:
            return self._geometry_map.get_freecad_id(freecad_id + (reference,))
    
    # Private Methods #
    def _get_pancad_by_uid(self, uid: UUID) -> PanCADThing:
        """Returns a PanCAD object from the map that has the uid."""
        pancad_object, *_ = self._mapping[uid]
        return pancad_object
    
    def _freecad_repr(self,
                      freecad_id: int | tuple[int, int, ConstraintReference],
                      freecad_object: object) -> str:
        """Returns a string representing the freecad object."""
        default_repr = repr(freecad_object).replace("<", "").replace(">", "")
        
        if hasattr(freecad_object, "Label"):
            return f"<ID:{freecad_id} '{freecad_object.Label}' {default_repr}>"
        else:
            return f"<ID:{freecad_id} {default_repr}>"
            
    
    @singledispatchmethod
    def _link_pancad_to_freecad_feature(self, key, value: object):
        """Adds a PanCAD parent and FreeCAD child feature pairing to the map. 
        Each key is the PanCAD element's uid, mapped to a tuple with the PanCAD 
        parent will be the first element and the FreeCAD feature ID as the 
        second element.
        """
        raise TypeError(f"Unrecognized PanCAD geometry type {key.__class__}")
    
    @_link_pancad_to_freecad_feature.register
    def _coordinate_system(self, key: CoordinateSystem, origin: object) -> None:
        subfeatures = {ConstraintReference.CORE: origin,
                       ConstraintReference.ORIGIN: origin,
                       ConstraintReference.X: origin.OriginFeatures[0],
                       ConstraintReference.Y: origin.OriginFeatures[1],
                       ConstraintReference.Z: origin.OriginFeatures[2],
                       ConstraintReference.XY: origin.OriginFeatures[3],
                       ConstraintReference.XZ: origin.OriginFeatures[4],
                       ConstraintReference.YZ: origin.OriginFeatures[5],}
        self._feature_map[origin.ID] = subfeatures
        self._mapping[key.uid] = (key, origin.ID)
    
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
        self._feature_map[pad.ID] = {ConstraintReference.CORE: pad}
        self._mapping[key.uid] = (key, pad.ID)
    
    @_link_pancad_to_freecad_feature.register
    def _feature_container(self,
                           key: FeatureContainer,
                           body: Part.BodyBase) -> None:
        self._feature_map[body.ID] = {ConstraintReference.CORE: body}
        self._mapping[key.uid] = (key, body.ID)
    
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
        self._feature_map[sketch.ID] = {ConstraintReference.CORE: sketch}
        self._mapping[key.uid] = (key, sketch.ID)
        
        # Map the geometry inside of the sketch
        self._geometry_map[sketch.ID, -2] = {
            # ConstraintReference.CORE: sketch.ExternalGeo[1]
            ConstraintReference.CORE: -2
        }
        self._geometry_map[sketch.ID, -1] = {
            # ConstraintReference.CORE: sketch.ExternalGeo[0]
            ConstraintReference.CORE: -1
        }
        geometry_index = 0
        internal_constraint_index = 0
        for geometry, construction in zip(key.geometry, key.construction):
            new_geometry = get_freecad_sketch_geometry(geometry)
            sketch.addGeometry(new_geometry, construction)
            
            if isinstance(geometry, Ellipse):
                sketch.exposeInternalGeometry(geometry_index)
                ellipse_id = (sketch.ID, geometry_index)
                subgeometry = dict()
                subgeometry[ConstraintReference.CORE] = new_geometry
                ellipse_references = [ConstraintReference.CENTER,
                                      ConstraintReference.X,
                                      ConstraintReference.Y,
                                      ConstraintReference.FOCAL_PLUS,
                                      ConstraintReference.FOCAL_MINUS]
                self._mapping[geometry.uid] = (key, ellipse_id)
                for i, reference in enumerate(ellipse_references):
                    sub_index = geometry_index + i
                    self._geometry_map[sketch.ID, sub_index] = {
                        ConstraintReference.CORE: sub_index
                    }
                    subgeometry[reference] = sub_index
                self._geometry_map[ellipse_id] = subgeometry
                geometry_index += len(ellipse_references)
                last_constraint_index = internal_constraint_index + 4
                
            else:
                self._mapping[geometry.uid] = (geometry,
                                               (sketch.ID, geometry_index))
                self._geometry_map[sketch.ID, geometry_index] = {
                    ConstraintReference.CORE: geometry_index,
                }
                geometry_index += 1

class _FreeCADFeatureMap(MutableMapping):
    """Used to map features and their subfeatures in FreeCAD according to their 
    feature id. Individual constraint reference mappings cannot be directly 
    modified, only the grouped feature and subfeatures all at once.
    """
    
    def __init__(self) -> None:
        self._features = dict()
    
    # Python Dunders #
    def __contains__(self, key: int | tuple[int, ConstraintReference]) -> bool:
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
            return any([key == feature_id for feature_id, _ in self._features])
        else:
            raise TypeError(f"Unrecognized input type {key.__class__}")
    
    def __delitem__(self, feature_id: int) -> None:
        """Delete the feature in the key along with its subfeatures."""
        del self._features[feature_id]
    
    def __getitem__(self, key: int | tuple[int, ConstraintReference]) -> object:
        """Get the subfeature of a feature."""
        if isinstance(key, int):
            # ConstraintReference is assumed to be CORE
            feature_id = key
            reference = ConstraintReference.CORE
        else:
            feature_id, reference = key
        return self._features[feature_id][reference]
    
    def __iter__(self):
        return iter(self._features)
    
    def __len__(self) -> int:
        return len(self._features)
    
    def __setitem__(self,
                    feature_id: int,
                    subfeatures: dict[ConstraintReference, object]) -> None:
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
                       reference: ConstraintReference) -> int:
        return self._features[feature_id][reference].ID
    
    def get_references(self, feature_id: int) -> list[ConstraintReference]:
        """Returns a list of references available for the feature_id."""
        return list(self._features[feature_id])
    
    

class _FreeCADSketchGeometryMap(MutableMapping):
    """Used to map geometry and constraints in FreeCAD sketches according to 
    their owning sketch id and its equivalent constraint index and constraint 
    references. Individual constraint reference mappings cannot be directly 
    modified, only the grouped geometry.
    """
    
    def __init__(self, feature_map: _FreeCADFeatureMap) -> None:
        self._feature_map = feature_map
        self._sketches = dict()
    
    # Public Methods #
    def get_sketch_indices(self, sketch_id: int) -> dict:
        """Returns a dictionary of indices to the constraint or geometry in the 
        sketch.
        """
        return self._sketches[sketch_id]
    
    # Python Dunders #
    def __contains__(self,
                     key: int | tuple[int, int, ConstraintReference]) -> bool:
        if isinstance(key, tuple):
            if len(key) == 3:
                # Check if the specific sub geometry is in the map
                sketch_id, index, reference = key
                if (sketch_id in self._sketches
                        and index in self._sketches[sketch_id]):
                    return reference in self._sketches[sketch_id][index]
                else:
                    return False
            elif len(key) == 2:
                # Check if the geometry as a whole is in the map
                sketch_id, index = key
                return (sketch_id in self._sketches
                        and index in self._sketches[sketch_id])
            else:
                raise ValueError("Tuple key must be either 2 or 3 long")
        elif isinstance(key, int):
            # Return if a sketch with the id of key has an element in the map
            return any([key == sketch_id for sketch_id, _ in self._sketches])
        else:
            raise TypeError(f"Unrecognized input type {key.__class__}")
    
    def __delitem__(self, key: tuple[int, int]) -> None:
        """Delete the geometry in the key along with its subgeometry."""
        sketch_id, index = key
        del self._sketches[sketch_id][index]
    
    def __getitem__(self, key: tuple[int, int, ConstraintReference]) -> object:
        """Get the subgeometry of sketch geometry."""
        sketch_id, index, reference = key
        subgeometry_index = self._sketches[sketch_id][index][reference]
        return self._feature_map[sketch_id].Geometry[subgeometry_index]
    
    def __iter__(self):
        return iter(self._sketches)
    
    def __len__(self) -> int:
        return len(self._sketches)
    
    def __setitem__(self,
                    key: tuple[int, int],
                    subgeometry: dict[ConstraintReference, int]) -> None:
        if not isinstance(key, tuple):
            raise ValueError("Key must be tuple of sketch id and index."
                             f" Given {key}")
        sketch_id, index = key
        if sketch_id not in self._sketches:
            # When the sketch id is new, initialize a sketch dict
            self._sketches[sketch_id] = dict()
        if index not in self._sketches[sketch_id]:
            # When the index is new, initialize a index dict
            self._sketches[sketch_id][index] = dict()
        
        if ConstraintReference.CORE in subgeometry:
            self._sketches[sketch_id][index] = subgeometry
        else:
            raise ValueError("Subgeometry must contain a"
                             " ConstraintReference.CORE")
    
    def __str__(self) -> str:
        output_strings = []
        for sketch, values in self._sketches.items():
            output_strings.append(f"{sketch}:")
            for index, geometry in values.items():
                output_strings.append(f"{{{index}: {geometry}}}")
        return "\n".join(output_strings)
    
    def get_freecad_id(self,
                       key: tuple[int, int, ConstraintReference],
                       ) -> tuple[int, int]:
        sketch_id, index, reference = key
        subgeometry_index = self._sketches[sketch_id][index][reference]
        return (sketch_id, subgeometry_index)
    
    def get_references(self,
                       key: tuple[int, int]) -> tuple[ConstraintReference]:
        sketch_id, index = key
        return list(self._sketches[sketch_id][index])