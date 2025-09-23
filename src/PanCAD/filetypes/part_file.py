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
from typing import Sequence, Self
from pprint import pformat

from PanCAD.geometry import (CoordinateSystem, FeatureContainer, Sketch,
                             AbstractFeature, PanCADThing)
from PanCAD.filetypes.constants import SoftwareName

class PartFile(PanCADThing):
    """A class representing a part file in CAD applications. PanCAD defines a 
    part file that contains geometry definition for one object and different 
    geometry configurations of that object.
    
    :param filename: The name of the file. Any extension at the end of the file 
        will be removed. Defaults to "New_PartFile".
    :param container: The primary container for the PartFile. Contains all 
        features inside the file. Usually represented as a FeatureTree inside 
        of a file, but can also be something like a Body or Part object in 
        software like FreeCAD.
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
                 filename: str="New_PartFile",
                 container: FeatureContainer=None,
                 *,
                 uid: str=None) -> None:
        self.filename = filename
        self.uid = uid
        self.container = container
    
    # Class Methods #
    @classmethod
    def from_freecad(cls, filepath: str) -> Self:
        """Reads a FreeCAD file and returns it as a PanCAD PartFile.
        
        :param filepath: The filepath to a FreeCAD file structured like a 
            PartFile.
        :returns: The PanCAD equivalent of the FreeCAD file.
        """
        # Local import here to avoid circular imports
        from PanCAD.cad.freecad import FreeCADFile
        file = FreeCADFile(filepath)
        return file.to_pancad()
    
    # Getters #
    @property
    def container(self) -> FeatureContainer:
        """The primary FeatureContainer for the PartFile."""
        return self._container
    
    @property
    def filename(self) -> str:
        """The filename of the PartFile. Does not contain a path or extension.
        
        :getter: Returns the filename of the PartFile.
        :setter: Sets the filename of the PartFile. Removes any extensions from 
            the input string.
        """
        return self._filename
    
    @property
    def features(self) -> tuple[AbstractFeature]:
        """The features inside the PartFile"""
        return self.container.features
    
    # Setters #
    @container.setter
    def container(self, feature_container: FeatureContainer) -> None:
        if feature_container is None:
            self._container = FeatureContainer()
        else:
            self._container = feature_container
    
    @filename.setter
    def filename(self, name: str) -> None:
        self._filename = Path(name).stem
    
    @features.setter
    def features(self, new_features: tuple[AbstractFeature]) -> None:
        if not isinstance(new_features[0], CoordinateSystem):
            new_features = (CoordinateSystem(),) + new_features
        self.container.features = new_features
    
    # Public Methods #
    def add_feature(self, feature: AbstractFeature) -> Self:
        """Adds a feature to the PartFile.
        
        :param feature: The feature to add.
        :returns: The updated PartFile.
        :raises LookupError: Raised if the feature's dependencies are not 
            already in the PartFile.
        """
        if (not isinstance(feature, CoordinateSystem)
                and len(self.container.features) == 0):
            # The first element in the PartFile's primary container needs to 
            # always be its coordinate system. This behavior can't be done on 
            # the FeatureContainer level since it only applies to PartFiles 
            # and not things like Folders.
            self.container.add_feature(
                CoordinateSystem(name="Coordinate System")
            )
        
        if isinstance(feature, Sketch) and feature.coordinate_system is None:
            # If the sketch doesn't have a coordinate system and is being put 
            # into a PartFile's primary container, its coordinate system is 
            # set to the PartFile's first coordinate system.
            feature.coordinate_system = self.container.features[0]
        
        self.container.add_feature(feature)
        
        return self
    
    def get_feature(self, uid: str) -> AbstractFeature:
        """Returns the feature with the given uid.
        
        :raises LookupError: When no feature with the uid is in the file.
        """
        
        for feature in self.container.features:
            if uid == feature.uid:
                return feature
        raise LookupError(f"File has no feature with uid '{uid}'")
    
    def get_features(self) -> tuple[AbstractFeature]:
        """Returns all of the PartFile's stored features."""
        return self.container.features
    
    def to_freecad(self, filepath: str) -> None:
        """Writes the PartFile to a FreeCAD file.
        
        :param filepath: The filepath to save the new FreeCAD file into.
        """
        # Local import here to avoid circular imports
        from PanCAD.cad.freecad import FreeCADFile
        file = FreeCADFile.from_partfile(self, filepath)
    
    # Python Dunders #
    def __contains__(self, item) -> bool:
        return item in self.container
    
    def __repr__(self) -> str:
        n_features = len(self.container.features)
        return f"<PanCADPartFile'{self.filename}'({n_features}feats)>"
    
    def __str__(self) -> str:
        """Prints a summary of the part file's contents."""
        from textwrap import indent
        PREFIX = "    "
        summary = [f"PartFile '{self.filename}'"]
        
        # Summarize Features
        for feature in self.container.features:
            dependency_lines = []
            for dependency in feature.get_dependencies():
                dependency_lines.append(
                    f"{dependency.__class__.__name__} '{dependency.uid}'"
                )
            
            preface = "Dependencies: "
            if len(dependency_lines) > 0:
                dependency_iter = iter(dependency_lines)
                dependency_summary = [preface + next(dependency_iter)]
                dep_indent = " "*len(preface)
                dependency_summary.extend(
                    [indent(line, dep_indent) for line in dependency_iter]
                )
            else:
                dependency_summary = [preface + "None"]
            feature_str = "\n".join(str(feature).split("\n")[1:])
            feature_summary = "\n".join(
                [
                    f"{feature.__class__.__name__} '{feature.name}'",
                    indent("\n".join(dependency_summary), PREFIX),
                    indent(feature_str, PREFIX),
                ]
            )
            summary.append(
                indent(feature_summary, PREFIX)
            )
        
        return "\n".join(summary)