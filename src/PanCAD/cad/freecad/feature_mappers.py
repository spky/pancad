"""A module providing functions to map PanCAD features to FreeCAD features."""

from collections.abc import MutableMapping
from functools import singledispatch

from PanCAD.cad.freecad import App, Sketcher, Part
from PanCAD.geometry.constants import ConstraintReference
from PanCAD.geometry import (PanCADThing,
                             AbstractGeometry,
                             AbstractFeature,
                             Circle,
                             CoordinateSystem,
                             LineSegment,
                             Sketch,
                             Extrude)

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
    
    :param _writing_map: Sets whether the map is for writing to FreeCAD or 
        reading from FreeCAD. A writing map will have PanCAD objects as keys and 
        FreeCAD objects as values, and a reading map will reverse those roles.
    
    """
    def __init__(self, writing_map: bool=True) -> None:
        self._mapping = dict()
        self._writing_map = writing_map
    
    
    # Python Dunders #
    def __contains__(self, key: object) -> bool:
        if isinstance(key, PanCADThing):
            return key.uid in self._mapping
        else:
            return key in self._mapping
    
    def __delitem__(self, key) -> None:
        del self._mapping[key.uid]
    
    def __getitem__(self, key: object | tuple) -> object:
        if isinstance(key, tuple):
            key, reference = key
            _, subfeatures = self._mapping[key.uid]
            value = subfeatures[reference]
        else:
            _, value = self._mapping[key.uid]
        return value
    
    def __iter__(self):
        return iter(self._mapping)
    
    def __len__(self) -> int:
        return len(self._mapping)
    
    def __setitem__(self, key: object, value: object) -> None:
        if self._writing_map:
            if isinstance(key, CoordinateSystem):
                subfeatures = {
                    ConstraintReference.ORIGIN: value,
                    ConstraintReference.X: value.OriginFeatures[0],
                    ConstraintReference.Y: value.OriginFeatures[1],
                    ConstraintReference.Z: value.OriginFeatures[2],
                    ConstraintReference.XY: value.OriginFeatures[3],
                    ConstraintReference.XZ: value.OriginFeatures[4],
                    ConstraintReference.YZ: value.OriginFeatures[5],
                }
                self._mapping[key.uid] = (key, subfeatures)
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
    