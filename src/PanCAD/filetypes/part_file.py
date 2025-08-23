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
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import textwrap
from typing import Sequence, Self
from pprint import pformat

from PanCAD.geometry import CoordinateSystem, Sketch, AbstractFeature
from PanCAD.filetypes.constants import SoftwareName

class PartFile:
    """A class representing a part file in CAD applications. PanCAD defines a 
    part file that contains geometry definition for one object and different 
    geometry configurations of that object.
    
    :param filename: The name of the file. Any extension at the end of the file 
        will be removed.
    :param original_software: A SoftwareName enumeration value defining where 
        the PartFile was originally designed. Defaults to None, resulting in no 
        metadata storage.
    :param features: The Features to be added to the PartFile. Defaults to an 
        empty tuple.
    :param metadata: The metadata to be added to the file. Cross references the 
        PanCAD metadata keys with the known original_software metadata keys. 
        Defaults to None.
    :param coordinate_system: The CoordinateSystem that all of the PartFile's 
        features depend on. Defaults to a coordinate system with an origin at 
        (0, 0, 0) and with axes in the canonical cartesian xyz directions.
    :param metadata_map: The mapping between synchronized software metadata 
        fields. Its keys must be SoftwareName values, and each value must have a 
        subdictionary with field names for keys and a tuple of (SoftwareName, 
        field name). The mapping allows different software metadata fields to be 
        synchronized together as necessary.
    """
    
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
    """The default available PartFile metadata. An standard xml namespace is 
    defined where available to improve the interoperability of the 
    metadata. See `DCMI Metadata Terms 
    <https://www.dublincore.org/specifications/dublin-core/dcmi-terms/>`_ 
    for definitions of the 'dcterms' fields.
    """
    
    def __init__(self,
                 filename: str,
                 original_software: SoftwareName=None,
                 features: Sequence=None,
                 *,
                 metadata: dict=None,
                 coordinate_system: CoordinateSystem=None,
                 metadata_map: dict[SoftwareName,
                                    dict[str,
                                         tuple[SoftwareName, str]]]=None
                 ) -> None:
        self.filename = filename
        # self._set_filename(filename)
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
        
        if original_software is None:
            self._metadata = None
        else:
            self._initialize_metadata(metadata, original_software, metadata_map)
    
    # Class Methods #
    @classmethod
    def from_freecad(cls, filepath: str) -> Self:
        """Reads a FreeCAD file and returns it as a PanCAD PartFile.
        
        :param filepath: The filepath to a FreeCAD file structured like a 
            PartFile.
        :returns: The PanCAD equivalent of the FreeCAD file.
        """
        # Local import here to avoid circular imports
        from PanCAD.cad.freecad.read_freecad import FreeCADFile
        file = FreeCADFile(filepath)
        return file.to_pancad()
    
    # Properties #
    @property
    def filename(self) -> str:
        """The filename of the PartFile. Does not contain a path or extension.
        """
        return self._filename
    
    @filename.setter
    def filename(self, name: str) -> None:
        self._filename = Path(name).stem
    
    # Public Methods #
    def add_feature(self, feature: AbstractFeature) -> Self:
        """Adds a feature to the PartFile.
        
        :param feature: The feature to add.
        :returns: The updated PartFile.
        :raises LookupError: Raised if the feature's dependencies are not 
            already in the PartFile.
        """
        if (isinstance(feature, Sketch)
            and feature.coordinate_system is not self.get_coordinate_system()):
            # Replace the sketch's locating coordinate system with the part 
            # file's. Sketches are currently only possible to place on Part File 
            # baseplanes
            feature.coordinate_system = self.get_coordinate_system()
        
        if all([d in self for d in feature.get_dependencies()]):
            self._features = self._features + (feature,)
        else:
            missed = filter(lambda d: d not in self, feature.get_dependencies())
            raise LookupError(f"Dependencies for {repr(feature)} are missing"
                             f" from part: {list(missed)}")
        return self
    
    def get_coordinate_system(self) -> CoordinateSystem:
        """Returns the PartFile's defining coordinate_system."""
        return self._coordinate_system
    
    def get_features(self) -> tuple[AbstractFeature]:
        """Returns all of the PartFile's stored features."""
        return self._features
    
    def get_metadata_value(self,
                           software: SoftwareName,
                           metadata_name: str) -> object | None:
        """Returns a software's metadata field.
        
        :param software: The SoftwareName for the software that defined the 
            metadata field.
        :param metadata_name: The name of the metadata field in the software.
        :returns: The value of the metadata field if it exists, otherwise None.
        """
        try:
            origin_software, name = self._metadata_map[software][metadata_name]
            return self._metadata[origin_software][name]
        except KeyError:
            return None
    
    def metadata_to_dict(self) -> dict[str, dict[str, object]]:
        """Returns the metadata as a simplified dictionary without automated 
        synchronization.
        """
        data = defaultdict(dict)
        for software, data_map in self._metadata_map.items():
            for data_name, (origin, name) in data_map.items():
                data[software][data_name] = self._metadata[origin][name]
        return dict(data)
    
    def to_freecad(self, directory: str) -> None:
        """Writes the PartFile to a FreeCAD file.
        
        :param directory: The directory to save the new FreeCAD file into.
        """
        # Local import here to avoid circular imports
        from PanCAD.cad.freecad.read_freecad import FreeCADFile
        file = FreeCADFile.from_partfile(self, directory)
    
    def update_metadata_value(self,
                              software: SoftwareName,
                              metadata_name: str,
                              value: object) -> Self:
        """Updates a metadata field for a specific software.
        
        :param software: The SoftwareName for the software that defined the 
            metadata field.
        :param metadata_name: The name of the metadata field in the software.
        :param value: The value of the metadata field.
        :returns: The updated PartFile.
        """
        origin_software, name = self._metadata_map[software][metadata_name]
        self._metadata[origin_software][name] = value
        return self
    
    # Private Methods #
    def _initialize_metadata(self,
                             metadata: dict,
                             software: SoftwareName,
                             metadata_map: dict=None) -> None:
        """Takes metadata from CAD software and maps it into standard data.
        
        :metadata: The original software's metadata.
        :software: The original software's SoftwareName.
        :metadata_map: The metadata mapping described in the init method.
        """
        self._metadata[software] = metadata
        
        for key in metadata:
            self._metadata_map[software][key] = (software, key)
        
        for key, value in metadata_map.items():
            if key in self.PANCAD_METADATA and value in metadata:
                self._metadata_map[SoftwareName.PANCAD][key] = (software, value)
            elif key not in self.PANCAD_METADATA:
                raise KeyError(f"metadata_map key '{key}' not found in pancad"
                               " metadata. Dict must be formatted"
                               " {pancad_data_name: software_data_name}."
                               f"\npancad_data_names: {self.PANCAD_METADATA}")
            elif value not in metadata:
                raise KeyError(f"Mapped '{key}' not found in '{software}'"
                               " metadata")
            else:
                self._metadata_map[SoftwareName.PANCAD][key] = (software, None)
    
    # Python Dunders #
    def __contains__(self, item) -> bool:
        contents = (self._coordinate_system,) + self._features
        return any([item is c for c in contents])
    
    def __repr__(self) -> str:
        n_features = len(self.get_features())
        return f"<PanCADPartFile'{self.filename}'({n_features}feats)>"
    
    def __str__(self) -> str:
        """Prints a summary of the part file's contents."""
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
            feature_str = "\n".join(str(feature).split("\n")[1:])
            feature_summary = "\n".join(
                [
                    f"{feature.__class__.__name__} '{feature.uid}'",
                    textwrap.indent("\n".join(dependency_summary), INDENT),
                    textwrap.indent(feature_str, INDENT),
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
        if len(metadata_lines) == 0:
            metadata_lines = ["No metadata available"]
        metadata_summary = "\n".join(
            [
                "Metadata",
                textwrap.indent("\n".join(metadata_lines), INDENT)
            ]
        )
        summary.append(
            textwrap.indent(metadata_summary, INDENT)
        )
        return "\n".join(summary)