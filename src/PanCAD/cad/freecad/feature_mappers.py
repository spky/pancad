"""A module providing functions to map PanCAD features to FreeCAD features."""

from collections import defaultdict
from collections.abc import MutableMapping
from functools import singledispatch, singledispatchmethod
from typing import Self
from uuid import UUID

from PanCAD.cad.freecad import App, Sketcher, Part
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
    _FREECAD_SKETCH_ID_SEPARATOR = "#"
    
    def __init__(self, document: App.Document, writing_map: bool=True) -> None:
        self._mapping = dict()
        self._writing_map = writing_map
        self._document = document
        
        self._freecad_sketch_geometry_map = dict()
        # Maps freecad sketches to their contained geometry
    
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
    
    # Python Dunders #
    def __contains__(self, key: object) -> bool:
        if isinstance(key, PanCADThing):
            return key.uid in self._mapping
        else:
            return key in self._mapping
    
    def __delitem__(self, key) -> None:
        del self._mapping[key.uid]
    
    def __getitem__(self, key: object | tuple[object,
                                              ConstraintReference]) -> object:
        if isinstance(key, tuple):
            key, reference = key
            _, subfeatures = self._mapping[key.uid]
            if isinstance(subfeatures, dict):
                value = subfeatures[reference]
            else:
                raise ValueError(f"key '{key}' has no mapped subfeatures")
        elif isinstance(key, UUID):
            _, value = self._mapping[key]
        else:
            _, value = self._mapping[key.uid]
            if isinstance(value, dict):
                # If only given the key for a subfeatured item, return the CORE.
                value = value[ConstraintReference.CORE]
        return value
    
    def __iter__(self):
        return iter(self._mapping)
    
    def __len__(self) -> int:
        return len(self._mapping)
    
    def __setitem__(self, key: object, value: object) -> None:
        if self._writing_map:
            # Writing **TO** FreeCAD
            if isinstance(key, FeatureContainer):
                self._mapping[key.uid] = (key, value)
            elif isinstance(key, CoordinateSystem):
                subfeatures = {ConstraintReference.CORE: value,
                               ConstraintReference.ORIGIN: value,
                               ConstraintReference.X: value.OriginFeatures[0],
                               ConstraintReference.Y: value.OriginFeatures[1],
                               ConstraintReference.Z: value.OriginFeatures[2],
                               ConstraintReference.XY: value.OriginFeatures[3],
                               ConstraintReference.XZ: value.OriginFeatures[4],
                               ConstraintReference.YZ: value.OriginFeatures[5],}
                self._mapping[key.uid] = (key, subfeatures)
            elif isinstance(key, Sketch):
                sketch = value
                sketch.AttachmentSupport = (self[key.coordinate_system,
                                                         key.plane_reference],
                                                    [""])
                sketch.MapMode = "FlatFace"
                sketch.Label = key.name
                freecad_parent = self[key.context]
                freecad_parent.addObject(sketch)
                self._mapping[key.uid] = (key, sketch)
                
                # Map the geometry inside of the sketch
                geometry_map = dict()
                index = 0
                for geometry, construction in zip(key.geometry,
                                                  key.construction):
                    freecad_geometry = get_freecad_sketch_geometry(geometry)
                    sketch.addGeometry(freecad_geometry, construction)
                    self._mapping[geometry.uid] = (geometry, freecad_geometry)
                    geometry_map[index] = freecad_geometry
                    if isinstance(geometry, Ellipse):
                        sketch.exposeInternalGeometry(index)
                        subgeometry = {
                            ConstraintReference.CORE: freecad_geometry,
                            ConstraintReference.CENTER: freecad_geometry,
                            ConstraintReference.X: sketch.Geometry[Index + 1],
                            ConstraintReference.Y: sketch.Geometry[Index + 2],
                            ConstraintReference.FOCAL_PLUS: sketch.Geometry[
                                Index + 3
                            ],
                            ConstraintReference.FOCAL_MINUS: sketch.Geometry[
                                Index + 4
                            ],
                        }
                        index += 5
                    else:
                        index += 1
                self._freecad_sketch_geometry_map[sketch.ID] = geometry_map
            elif isinstance(key, Extrude):
                freecad_pad = value
                freecad_parent = self[key.context]
                freecad_parent.addObject(freecad_pad)
                freecad_pad.Profile = (self[key.profile], [""])
                freecad_pad.Length = key.length
                freecad_pad.ReferenceAxis = (self[key.profile], ["N_Axis"])
                self[key.profile].Visibility = False
                self._mapping[key.uid] = (key, freecad_pad)
            elif isinstance(key, PanCADThing):
                self._mapping[key.uid] = (key, value)
            else:
                raise TypeError("Writing map keys must be PanCAD objects,"
                                f" given: {key}, class: {key.__class__}")
        else:
            if not isinstance(key, PanCADThing):
                self._mapping[key] = (key, value)
            else:
                raise TypeError("Reading map keys cannot be PanCAD objects,"
                                f" given: {key}")
    
    def __str__(self) -> str:
        return str(self._mapping)
