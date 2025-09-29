"""
A module providing methods for FreeCADMap to translate features to and from 
FreeCAD.
"""
from functools import singledispatchmethod

from PanCAD.cad.freecad import (
    FreeCADBody,
    FreeCADFeature,
    FreeCADOrigin,
    FreeCADSketch,
)
from PanCAD.cad.freecad.constants import ObjectType
from PanCAD.geometry import (
    AbstractFeature,
    CoordinateSystem,
    Extrude,
    FeatureContainer,
    Sketch,
)

# PanCAD to FreeCAD
@singledispatchmethod
def _pancad_to_freecad_feature(self,
                               feature: AbstractFeature) -> FreeCADFeature:
    raise TypeError(f"Unrecognized PanCAD feature type {key.__class__}")

@_pancad_to_freecad_feature.register
def _coordinate_system(self, system: CoordinateSystem) -> FreeCADOrigin:
    parent = self[system.context]
    return parent.Origin

@_pancad_to_freecad_feature.register
def _feature_container(self, container: FeatureContainer) -> FreeCADBody:
    body = self._document.addObject(ObjectType.BODY, container.name)
    return body

@_pancad_to_freecad_feature.register
def _extrude(self, pancad_extrude: Extrude) -> FreeCADFeature:
    pad = self._document.addObject(ObjectType.PAD, pancad_extrude.name)
    parent = self[pancad_extrude.context]
    parent.addObject(pad)
    pad.Profile = (self[pancad_extrude.profile], [""])
    pad.Length = pancad_extrude.length
    pad.ReferenceAxis = (self[pancad_extrude.profile], ["N_Axis"])
    self[pancad_extrude.profile].Visibility = False
    return pad

@_pancad_to_freecad_feature.register
def _sketch(self, pancad_sketch: Sketch) -> FreeCADSketch:
    sketch = self._document.addObject(ObjectType.SKETCH, pancad_sketch.name)
    sketch_plane = self[pancad_sketch.coordinate_system,
                        pancad_sketch.plane_reference]
    parent = self[pancad_sketch.context]
    parent.addObject(sketch)
    sketch.AttachmentSupport = (sketch_plane, [""])
    sketch.MapMode = "FlatFace"
    sketch.Label = pancad_sketch.name
    
    geometry_iter = zip(pancad_sketch.geometry, pancad_sketch.construction)
    for pancad_geometry, construction in geometry_iter:
        geometry = self._pancad_to_freecad_geometry(pancad_geometry)
        geometry_id = self._freecad_add_to_sketch(geometry,
                                                  sketch,
                                                  construction)
        # The initial map between the pancad sketch geometry and the core 
        # element of the freecad sketch geometry has to be set here because 
        # there's no way to know which element corresponds to which unless 
        # the single core relationship is mapped during generation.
        self._pancad_to_freecad[pancad_geometry.uid] = (pancad_geometry,
                                                        geometry_id)
    return sketch