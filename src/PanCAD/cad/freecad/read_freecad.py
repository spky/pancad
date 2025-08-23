"""
A module providing functions to read FreeCAD files formatted like part files 
into a PanCAD PartFile object.
"""
from collections import OrderedDict
import os
import pathlib
from typing import Self

import numpy as np
import quaternion

from PanCAD.cad.freecad import App, PartDesign, Sketcher
from PanCAD.cad.freecad.constants import ObjectType, PadType
from PanCAD.cad.freecad.feature_mappers import map_freecad
from PanCAD.cad.freecad.sketch_geometry import get_pancad_sketch_geometry
from PanCAD.cad.freecad.sketch_constraints import add_pancad_sketch_constraint
from PanCAD.cad.freecad.to_part_file import add_feature_to_freecad

from PanCAD.filetypes import PartFile
from PanCAD.filetypes.constants import SoftwareName
from PanCAD.geometry import CoordinateSystem, Sketch, Extrude
from PanCAD.geometry.constants import ConstraintReference, FeatureType
from PanCAD.utils import file_handlers

class FreeCADFile:
    """A class representing FreeCAD files. Provides functionality to translate 
    the file to a PanCAD filetype.
    
    :param path: The location of the FreeCAD file.
    """
    STORED_UNIT = "mm" # Values are always stored internally as this unit
    EXTENSION = ".FCStd"
    
    def __init__(self, path: str=None):
        self.path = path
        self._document = App.open(self.path)
        no_bodies = len(self._get_bodies())
        if no_bodies == 0:
            raise NotImplementedError("Files without a body are not supported")
        elif no_bodies == 1:
            self._init_part_file_like()
        else:
            raise NotImplementedError("Multiple bodies are not supported")
    
    # Class Methods #
    @classmethod
    def from_partfile(cls, part_file: PartFile, directory: str) -> Self:
        """Creates a FreeCAD file from a PanCAD PartFile.
        
        :param part_file: The PanCAD PartFile to make a FreeCAD file from.
        :param directory: The directory path to save the new FreeCAD file into.
        """
        if isinstance(part_file, PartFile):
            new_file = cls.__new__(cls)
            new_file._document = App.newDocument()
            filepath = os.path.join(directory,
                                    part_file.filename + cls.EXTENSION)
            new_file._document.FileName = file_handlers.filepath(filepath)
            
            # Add body and coordinate system
            root = new_file._document.addObject(ObjectType.BODY, "Body")
            part_file_cs = part_file.get_coordinate_system()
            
            # Initialize feature map with part_file coordinate system
            feature_map = OrderedDict()
            feature_map.update(
                map_freecad(part_file_cs, root.Origin)
            )
            
            # Add all other PartFile features.
            for feature in part_file.get_features():
                feature_map = add_feature_to_freecad(feature, feature_map)
            
            new_file.save()
            return new_file
        else:
            raise ValueError(f"Filetype {file.__class__} not recognized")
    
    # Properties #
    @property
    def path(self) -> str:
        """The filepath of the FreeCADFile.
        
        :getter: Returns the filepath.
        :setter: Sets the path and updates the stem accordingly.
        """
        return self._path
    
    @property
    def stem(self) -> str:
        """The name of the FreeCADFile without the extension or path.
        
        :getter: Returns the name of the file without the extension or path.
        :setter: Sets the stem and updates the path accordingly.
        """
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
    
    # Public Methods
    def save(self) -> Self:
        """Recomputes and saves the FreeCAD file to its path.
        
        :returns: The FreeCADFile object to enable method chaining.
        """
        self._document.recompute()
        self._document.save()
        return self
    
    def to_pancad(self) -> PartFile:
        """Returns a PanCAD filetype object from the FreeCAD file."""
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
        return part_file
    
    # Private Methods #
    def _get_bodies(self) -> list:
        """Returns a list of all body objects in the file."""
        return list(
            filter(lambda obj: obj.TypeId == ObjectType.BODY,
                   self._document.Objects)
        )
    
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
    
    def _init_part_file_like(self) -> None:
        """Initializes a part-like file from FreeCAD."""
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
    
    def _translate_pad(self, pad: object, feature_map: dict) -> dict:
        """Adds the FreeCAD pad to the given feature map.
        
        :param pad: A FreeCAD Pad object.
        :param feature_map: The mapping from the FreeCAD object to the 
            equivalent PanCAD object.
        :returns: The updated feature_map.
        """
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
                          is_reverse_direction=pad.Reversed,
                          unit=self.STORED_UNIT)
        feature_map.update(
            map_freecad(extrude, pad, from_freecad=True)
        )
        return feature_map
    
    def _translate_sketch(self,
                          sketch: Sketcher.Sketch,
                          feature_map: dict) -> dict:
        """Adds the FreeCAD sketch and its geometry to the given feature map.
        
        :param sketch: A FreeCAD Sketch object.
        :param feature_map: The mapping from the FreeCAD object to the 
            equivalent PanCAD object.
        :returns: The updated feature_map.
        """
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
    
    # Python Dunders #
    def __fs_path__(self):
        return self._path