"""
A module providing functions to read FreeCAD files formatted like part files 
into a PanCAD PartFile object.
"""
import os

from PanCAD.cad.freecad import App, PartDesign
from PanCAD.cad.freecad.constants import ObjectType
from PanCAD.filetypes import PartFile

from PanCAD.geometry import CoordinateSystem

def _from_freecad(filepath: str) -> PartFile:
    
    freecad_file = FreeCADFile(filepath)

class FreeCADFile:
    def __init__(self, path: str):
        self._path = path
        self._document = App.open(self._path)
        no_bodies = len(self._get_bodies())
        if no_bodies == 0:
            raise NotImplementedError("Files without a body are not supported")
        elif no_bodies == 1:
            self._init_part_file_like()
        else:
            raise NotImplementedError("Multiple bodies are not supported")
    
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
        pass
    
    def to_pancad(self) -> PartFile:
        pass
    
    # Python Dunders #
    def __fs_path__(self):
        return self._path