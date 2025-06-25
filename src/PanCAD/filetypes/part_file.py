"""A module providing a class to represent a part file in CAD. PanCAD defines a 
part file as a CAD file that contains the geometry definition information for 
one object and potentially different configurations of that object. 

CAD files that contain geometry definition information for multiple objects fall 
out of scope, as well as files that position multiple objects relative to 
each other (e.g. Assemblies).

This file defines what metadata is standard between all part files, though not 
all standard metadata is guaranteed to be filled out. Functions going from and 
to other applications need to map the standard metadata to the client 
application's name for the data (Ex: "identifier" in PanCAD can map to "PartNo" 
in another application).

"""

import os
from collections import defaultdict

from PanCAD.geometry import CoordinateSystem
from PanCAD.filetypes.constants import SoftwareName

class PartFile:
    
    # dcterms defined here:
    # https://www.dublincore.org/specifications/dublin-core/dcmi-terms/
    PANCAD_METADATA = [
        "dcterms:identifier",
        "dcterms:title",
        "dcterms:license",
        "dcterms:description",
        "dcterms:created",
        "dcterms:creator",
        "dcterms:contributor",
        "dcterms:modified",
        "units",
    ]
    
    def __init__(self,
                 filename: str,
                 original_software: SoftwareName,
                 geometry: tuple=None,
                 *,
                 metadata: dict=None,
                 coordinate_system: CoordinateSystem=None,
                 metadata_map: dict=None):
        self._set_filename(filename)
        self._metadata = defaultdict(dict)
        self._metadata_map = defaultdict(dict)
        
        if metadata_map is None:
            metadata_map = dict()
        
        if coordinate_system is None:
            self._coordinate_system = CoordinateSystem()
        else:
            self._coordinate_system = coordinate_system
        
        self._initialize_metadata(metadata, original_software, metadata_map)
    
    def get_metadata_value(self, software: SoftwareName, metadata_name: str):
        try:
            origin_software, name = self._metadata_map[software][metadata_name]
            return self._metadata[origin_software][name]
        except KeyError:
            return None
    
    def update_metadata_value(self, software: SoftwareName,
                              metadata_name: str, value: object):
        origin_software, name = self._metadata_map[software][metadata_name]
        self._metadata[origin_software][name] = value
    
    def metadata_to_dict(self):
        data = defaultdict(dict)
        for software, data_map in self._metadata_map.items():
            for data_name, (origin, name) in data_map.items():
                data[software][data_name] = self._metadata[origin][name]
        return dict(data)
    
    # Private Methods
    def _initialize_metadata(self, metadata: dict, software: SoftwareName,
                             pancad_map: dict=None):
        """Takes metadata from CAD software and maps it into standard data.
        """
        self._metadata[software] = metadata
        
        for key in metadata:
            self._metadata_map[software][key] = (software, key)
        
        for key, value in pancad_map.items():
            if key in self.PANCAD_METADATA and value in metadata:
                self._metadata_map[SoftwareName.PANCAD][key] = (software, value)
            elif key not in self.PANCAD_METADATA:
                raise KeyError(f"pancad_map key '{key}' not found in pancad"
                               " metadata. Map must be formatted"
                               " {pancad_data_name: software_data_name}."
                               f"\npancad_data_names: {self.PANCAD_METADATA}")
            elif value not in metadata:
                raise KeyError(f"Mapped '{key}' not found in '{software}'"
                               " metadata")
            else:
                self._metadata_map[SoftwareName.PANCAD][key] = (software, None)
    
    def _set_filename(self, string: str):
        """Strips the filename of an extension if it has one and then sets the 
        PartFile's filename"""
        name, extension = os.path.splitext(string)
        self.filename = name