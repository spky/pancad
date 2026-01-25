"""A module providing a class to represent a part file in CAD. pancad defines a 
part file as a CAD file that contains the geometry definition information for 
one object and potentially different configurations of that object. 

CAD files that contain geometry definition information for multiple objects fall 
out of scope, as well as files that position multiple objects relative to 
each other (e.g. Assemblies).

This file defines what metadata is standard between all part files, though not 
all standard metadata is guaranteed to be filled out. Functions going from and 
to other applications need to map the standard metadata to the client 
application's name for the data (Ex: "identifier" in pancad can map to "PartNo" 
in another application).
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from textwrap import indent

from pancad.abstract import PancadThing
from pancad.geometry.feature_container import FeatureContainer

if TYPE_CHECKING:
    from uuid import UUID
    from typing import Self

    from pancad.abstract import AbstractFeature, AbstractGeometry

class PartFile(PancadThing):
    """A class representing a part file in CAD applications. pancad defines a 
    part file that contains geometry definition for one object and different 
    geometry configurations of that object.

    :param name: The name of the file.
    :param container: The primary FeatureContainer for the PartFile. Contains all 
        features inside the file. Usually represented as a FeatureTree inside 
        of a file, but can also be something like a Body or Part object in 
        software like FreeCAD.
    :param uid: The unique id for the pancad object.
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
    for definitions of the 'dcterms' fields. The dcterms namespace uri is 
    'http://purl.org/dc/terms/'
    """

    DEFAULT_COORDINATE_SYSTEM_NAME = "Coordinate System"
    """The name that auto-added coordinate systems are given if not externally 
    provided when features are added.
    """

    def __init__(self,
                 name: str="New_PartFile",
                 container: FeatureContainer | None=None,
                 *,
                 uid: str | None=None) -> None:
        self.name = name
        self.uid = uid
        self.container = container
        super().__init__()

    # Class Methods
    @classmethod
    def from_freecad(cls, filepath: str) -> Self:
        """Reads a FreeCAD file and returns it as a pancad PartFile.

        :param filepath: The filepath to a FreeCAD file structured like a 
            part file.
        :returns: The pancad equivalent of the FreeCAD part file.
        """
        # Local import here to avoid circular imports
        from pancad.cad.freecad.filetypes import FreeCADFile
        file = FreeCADFile.from_fcstd(filepath)
        return file.to_pancad()

    # Properties
    @property
    def container(self) -> FeatureContainer:
        """The primary FeatureContainer for the PartFile.

        :param getter: Returns the FeatureContainer.
        :param setter: Sets the container to a new FeatureContainer. If set to 
            None, an empty FeatureContainer is initialized.
        """
        return self._container
    @container.setter
    def container(self, feature_container: FeatureContainer | None) -> None:
        if feature_container is None:
            self._container = FeatureContainer()
        else:
            self._container = feature_container

    @property
    def name(self) -> str:
        """The name of the PartFile. Does not contain a path or extension.

        :getter: Returns the name of the PartFile.
        :setter: Sets the name of the PartFile.
        """
        return self._filename
    @name.setter
    def name(self, name: str) -> None:
        self._filename = Path(name).stem

    # Public Methods
    def get_dependencies(self) -> list[PancadThing]:
        """Returns the objects the PartFile depends on. pancad PartFiles are not 
        able to reference external files in the current release, so this is 
        always an empty list.
        """
        return self._container.get_dependencies()

    def to_freecad(self, filepath: str) -> None:
        """Writes the PartFile to a FreeCAD file.

        :param filepath: The filepath to save the new FreeCAD file into.
        """
        # Local import here to avoid circular imports
        from pancad.cad.freecad.filetypes import FreeCADFile
        FreeCADFile.from_partfile(self, filepath)

    # Dunders
    def __contains__(self, item: AbstractFeature | AbstractGeometry) -> bool:
        return item in self.container

    def __repr__(self) -> str:
        return super().__repr__().format(details=f"'{self.name}'")

    def __str__(self) -> str:
        """Prints a summary of the part file's contents."""
        prefix = "    "
        summary = [f"PartFile '{self.name}'"]
        # Summarize Features
        for feature in self.container.features:
            dependency_lines = []
            for dependency in feature.get_dependencies():
                dependency_lines.append(
                    f"{dependency.__class__.__name__} '{dependency.name}'"
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
                    indent("\n".join(dependency_summary), prefix),
                    indent(feature_str, prefix),
                ]
            )
            summary.append(
                indent(feature_summary, prefix)
            )
        return "\n".join(summary)
