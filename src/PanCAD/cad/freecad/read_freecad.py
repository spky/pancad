"""
A module providing functions to read FreeCAD files formatted like part files 
into a PanCAD PartFile object.
"""
import os
import pathlib

import numpy as np
import quaternion

from PanCAD.cad.freecad import App, PartDesign, Sketcher
from PanCAD.cad.freecad.feature_mappers import map_freecad
from PanCAD.cad.freecad.sketch_geometry import get_pancad_sketch_geometry
from PanCAD.cad.freecad.sketch_constraints import add_pancad_sketch_constraint
from PanCAD.cad.freecad.constants import ObjectType, PadType
from PanCAD.filetypes import PartFile
from PanCAD.filetypes.constants import SoftwareName
from PanCAD.geometry.constants import ConstraintReference, FeatureType

from PanCAD.geometry import CoordinateSystem, Sketch, Extrude

def from_freecad(filepath: str) -> PartFile:
    freecad_file = FreeCADFile(filepath)

class FreeCADFile:
    def __init__(self, path: str):
        self.path = path
        self._document = App.open(self.path)
        no_bodies = len(self._get_bodies())
        if no_bodies == 0:
            raise NotImplementedError("Files without a body are not supported")
        elif no_bodies == 1:
            self._init_part_file_like()
        else:
            raise NotImplementedError("Multiple bodies are not supported")
    
    @property
    def path(self) -> str:
        return self._path
    
    @property
    def stem(self) -> str:
        return self._stem
    
    @path.setter
    def path(self, filepath: str):
        pypath = pathlib.Path(filepath)
        self._path = str(pypath)
        self._stem = pypath.stem
    
    @stem.setter
    def stem(self, new_stem: str):
        self._stem = new_stem
        pypath = pathlib.Path(self._path)
        self._path = os.path.join(pypath.parent, new_stem + pypath.suffix)
        
    
    def _get_bodies(self) -> list:
        """Returns a list of all body objects in the file."""
        return list(
            filter(lambda obj: obj.TypeId == ObjectType.BODY,
                   self._document.Objects)
        )
    
    def _init_part_file_like(self) -> None:
        # The body and origin of a part file is the context everything else is 
        # defined under, so they will be consistent between part files
        self._body = self._get_bodies()[0]
        self._origin = self._body.Origin
        not_features = [self._body, self._origin]
        objects = filter(
            lambda obj: all(obj is not nf for nf in not_features),
            self._document.Objects
        )
        
        # sub_features: origin axes/planes that are not independent features
        sub_features = []
        sub_features.extend(self._origin.OriginFeatures)
        
        self._features = []
        for obj in objects:
            if not any([obj is sub_feat for sub_feat in sub_features]):
                match obj.TypeId:
                    case ObjectType.ORIGIN:
                        self._features.append(obj)
                        sub_features.extend(obj.OriginFeatures)
                    case _:
                        self._features.append(obj)
    
    def _get_part_file_coordinate_system(self) -> CoordinateSystem:
        """Returns the equivalent PanCAD coordinate system from the primary part 
        file FreeCAD body origin.
        """
        position = list(self._body.Placement.Base)
        quaternion = np.quaternion(
            *list(
                map(self._body.Placement.Rotation.Q.__getitem__, [3, 0, 1, 2])
            )
        )
        uid = self._body.Label + "_coordinate_system"
        
        return CoordinateSystem.from_quaternion(position, quaternion, uid=uid)
    
    def _translate_sketch(self,
                          sketch: Sketcher.Sketch,
                          feature_map: dict) -> dict:
        if len(sketch.AttachmentSupport) != 1:
            # Check whether the sketch is attached in a way that PanCAD doesn't 
            # support
            raise ValueError(f"Expected length of AttachmentSupport = 1,"
                             f" given: {sketch.AttachmentSupport}")
        elif len(sketch.AttachmentSupport[0]) != 2:
            raise ValueError("Expected length of AttachmentSupport[0] = 2,"
                             f" given: {sketch.AttachmentSupport[0]}")
        
        attachment_support = sketch.AttachmentSupport[0][0]
        base_geometry, base_reference = feature_map[attachment_support]
        pancad_sketch = Sketch(coordinate_system=base_geometry,
                               plane_reference=base_reference,
                               uid=sketch.Label)
        feature_map.update(
            map_freecad(pancad_sketch, sketch, from_freecad=True)
        )
        for i, geometry in enumerate(sketch.Geometry):
            pancad_geometry = get_pancad_sketch_geometry(geometry)
            pancad_sketch.add_geometry(pancad_geometry,
                                       sketch.getConstruction(i))
            feature_map.update(
                map_freecad(pancad_geometry,
                            geometry,
                            from_freecad=True,
                            parent_sketch=pancad_sketch,
                            index=i)
            )
        
        for constraint in sketch.Constraints:
            temp = add_pancad_sketch_constraint(constraint, pancad_sketch)
            if temp is not None:
                pancad_sketch = temp
        return feature_map
    
    def _translate_pad(self, pad: object, feature_map: dict) -> dict:
        profile_sketch, *_ = pad.Profile
        sketch, *_ = feature_map[profile_sketch]
        feature_type = PadType(pad.Type).get_feature_type(pad.Midplane,
                                                          pad.Reversed)
        extrude = Extrude(sketch,
                          uid=pad.Label,
                          feature_type=feature_type,
                          length=pad.Length.Value,
                          opposite_length=pad.Length2.Value,
                          is_midplane=pad.Midplane,
                          is_reverse_direction=pad.Reversed)
        feature_map.update(
            map_freecad(extrude, pad, from_freecad=True)
        )
        return feature_map
    
    def to_pancad(self) -> PartFile:
        feature_map = dict()
        coordinate_system = self._get_part_file_coordinate_system()
        filename = self.stem
        part_file = PartFile(filename, coordinate_system=coordinate_system)
        
        feature_map.update(
            map_freecad(coordinate_system, self._body.Origin, from_freecad=True)
        )
        for feature in self._features:
            match feature.TypeId:
                case ObjectType.SKETCH:
                    feature_map = self._translate_sketch(feature, feature_map)
                    sketch, *_ = feature_map[feature]
                    part_file.add_feature(sketch)
                case ObjectType.PAD:
                    feature_map = self._translate_pad(feature, feature_map)
                    extrude = feature_map[feature]
                    part_file.add_feature(extrude)
        print(part_file)
        return PartFile(filename,
                        coordinate_system=coordinate_system)
    
    
    # Python Dunders #
    def __fs_path__(self):
        return self._path