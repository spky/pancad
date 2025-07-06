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
import textwrap
from pprint import pformat

from PanCAD.geometry import CoordinateSystem, Sketch, Extrude
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
                 features: tuple=None,
                 *,
                 metadata: dict=None,
                 coordinate_system: CoordinateSystem=None,
                 metadata_map: dict=None):
        self._set_filename(filename)
        self._metadata = defaultdict(dict)
        self._metadata_map = defaultdict(dict)
        
        if metadata_map is None:
            metadata_map = dict()
        
        if features is None:
            self._features = tuple()
        else:
            self._features = tuple(features)
        
        if coordinate_system is None:
            self._coordinate_system = CoordinateSystem(
                uid=f"{self.filename} CS"
            )
        else:
            self._coordinate_system = coordinate_system
        
        self._initialize_metadata(metadata, original_software, metadata_map)
    
    # Public Methods
    def add_feature(self, feature: Sketch | Extrude):
        if all([d in self for d in feature.get_dependencies()]):
            self._features = self._features + (feature,)
        else:
            missed = filter(lambda d: d not in self, feature.get_dependencies())
            raise LookupError(f"Dependencies for {repr(feature)} are missing"
                             f" from part: {list(missed)}")
    
    def get_coordinate_system(self):
        return self._coordinate_system
    
    def get_features(self):
        return self._features
    
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
                               " metadata. Dict must be formatted"
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
    
    # Python Dunders #
    
    def __contains__(self, item):
        contents = (self._coordinate_system,) + self._features
        return any([item is c for c in contents])
    
    def __repr__(self) -> str:
        n_features = len(self.get_features())
        return f"<PanCADPartFile'{self.filename}'({n_features}feats)>"
    
    def __str__(self) -> str:
        """Prints a summary of the part file's contents"""
        INDENT = "    "
        summary = [f"PartFile '{self.filename}'"]
        
        # Summarize Coordinate System
        cs = self.get_coordinate_system()
        cs_title = f"{cs.__class__.__name__} '{cs.uid}'"
        cs_lines = []
        for reference in cs.get_all_references():
            geometry = cs.get_reference(reference)
            cs_lines.append(f"{reference.name} {geometry.__class__.__name__}"
                            f" '{geometry.uid}'")
        cs_summary = "\n".join(
            [
                f"{cs.__class__.__name__} '{cs.uid}'",
                textwrap.indent("\n".join(cs_lines), INDENT)
            ]
        )
        summary.append(
            textwrap.indent(cs_summary, INDENT)
        )
        
        # Summarize Features
        for feature in self.get_features():
            
            dependency_lines = []
            for dependency in feature.get_dependencies():
                dependency_lines.append(
                    f"{dependency.__class__.__name__} '{dependency.uid}'"
                )
            dependency_iter = iter(dependency_lines)
            preface = "Dependencies: "
            dependency_summary = [preface + next(dependency_iter)]
            dep_indent = " "*len(preface)
            dependency_summary.extend(
                [textwrap.indent(line, dep_indent) for line in dependency_iter]
            )
            feature_summary = "\n".join(
                [
                    f"{feature.__class__.__name__} '{feature.uid}'",
                    textwrap.indent("\n".join(dependency_summary), INDENT),
                ]
            )
            summary.append(
                textwrap.indent(feature_summary, INDENT)
            )
        
        # Summarize Metadata
        metadata_summary = []
        metadata_lines = []
         
        for software, data in self.metadata_to_dict().items():
            data_lines = [f"{field}: '{val}'" for field, val in data.items()]
            data_iter = iter(data_lines)
            preface = software.value + ": "
            software_summary = [preface + next(data_iter)]
            sw_indent = " "*len(preface)
            software_summary.extend(
                [textwrap.indent(line, sw_indent) for line in data_iter]
            )
            metadata_lines.append("\n".join(software_summary))
        metadata_summary = "\n".join(
            [
                "Metadata",
                textwrap.indent(
                    "\n".join(metadata_lines),
                    INDENT
                )
            ]
        )
        summary.append(
            textwrap.indent(metadata_summary, INDENT)
        )
        return "\n".join(summary)