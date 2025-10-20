"""
A module providing functions to read FreeCAD files formatted like part files 
into a pancad PartFile object.
"""
from __future__ import annotations

import pathlib
from typing import Self, NoReturn, TYPE_CHECKING

from pancad.filetypes import PartFile

from . import App
from .constants import ObjectType, PadType
from .freecad_python import validate_freecad
from ._feature_mappers import FreeCADMap

if TYPE_CHECKING:
    from ._application_types import FreeCADBody

class FreeCADFile:
    """A class representing FreeCAD files. Provides functionality to translate 
    the file to a pancad filetype.
    
    :param filepath: The location of the FreeCAD file.
    """
    STORED_UNIT = "mm" # Values are always stored internally as this unit
    EXTENSION = ".FCStd"
    
    def __init__(self, filepath: str) -> None:
        self.filepath = filepath
        self._document = App.open(self.filepath)
        no_bodies = len(self._get_bodies())
        if no_bodies == 0:
            raise NotImplementedError("Files without a body are not supported")
        elif no_bodies == 1:
            self._init_part_file_like()
        else:
            raise NotImplementedError("Multiple bodies are not supported")
    
    # Class Methods #
    @classmethod
    def from_partfile(cls, part_file: PartFile, filepath: str) -> Self:
        """Creates and saves a FreeCAD file from a pancad PartFile.
        
        :param part_file: A pancad PartFile.
        :param filepath: The filepath to save the new FreeCAD file to.
        :returns: The new FreeCADFile.
        :raises ValueError: When part_file is not a PartFile.
        """
        if isinstance(part_file, PartFile):
            # Use __new__ to bypass the init function
            new_file = cls.__new__(cls)
            new_file._document = App.newDocument()
            new_file.filepath = filepath
            new_file.document.FileName = new_file.filepath
            
            mapping = FreeCADMap(new_file.document, part_file)
            if part_file.container.name is None:
                # The body has to be named or FreeCAD won't add it
                part_file.container.name = "Body"
            mapping.add_pancad_feature(part_file.container)
            
            new_file.save()
            return new_file
        else:
            raise ValueError(f"Filetype {file.__class__} not recognized")
    
    # Getters #
    @property
    def document(self) -> App.Document:
        """The FreeCAD python object for the document.
        
        :getter: Returns the Document object.
        :setter: Read-only.
        """
        return self._document
    
    @property
    def filepath(self) -> str:
        """The filepath of the FreeCADFile.
        
        :getter: Returns the filepath.
        :setter: Sets the path and updates the stem accordingly.
        :raises ValueError: When path does not end with '.FCStd'.
        """
        return self._filepath
    
    @property
    def stem(self) -> str:
        """The name of the FreeCADFile without the extension or path.
        
        :getter: Returns the name of the file without the extension or path.
        :setter: Sets the stem and updates the path accordingly.
        """
        return self._stem
    
    # Setters #
    @filepath.setter
    def filepath(self, filepath: str):
        pypath = pathlib.Path(filepath)
        if pypath.suffix == self.EXTENSION:
            self._filepath = str(pypath)
            self._stem = pypath.stem
        else:
            raise ValueError(f"Path must end with '{self.EXTENSION}',"
                             f" given: {filepath}")
    
    @stem.setter
    def stem(self, new_stem: str):
        stem_path = pathlib.Path(new_stem)
        if stem_path.suffix in ["", ".FCStd"]:
            self._stem = stem_path.stem
            pypath = pathlib.Path(self._filepath)
            self._filepath = str(pypath.with_name(new_stem) \
                                       .with_suffix(self.EXTENSION))
        else:
            raise ValueError("Stem must either not have extension or end with"
                             f" '.FCStd', given: {new_stem}")
    
    # Public Methods
    def save(self) -> Self:
        """Recomputes and saves the FreeCAD file to its path.
        
        :returns: The same FreeCADFile object.
        """
        self._document.recompute()
        self._document.save()
        return self
    
    def to_pancad(self) -> PartFile:
        """Returns a pancad filetype object from the FreeCAD file."""
        return self._part_file
    
    def validate(self, unconstrained_error: bool=False) -> None:
        """Checks whether the FreeCAD document has any errors. Only checks the 
        document that is saved at the filepath, so if any modifications have 
        happened since the last save they will not be checked.
        
        :param unconstrained_error: Sets whether containing an unconstrained 
        sketch counts as an error.
        :raises ValueError: Raised when the FreeCAD file contains an error.
        """
        return validate_freecad(self.filepath, unconstrained_error)
    
    # Private Methods #
    def _get_bodies(self) -> list[FreeCADBody]:
        """Returns a list of all body objects in the file."""
        return list(
            filter(lambda obj: obj.TypeId == ObjectType.BODY,
                   self._document.Objects)
        )
    
    def _init_part_file_like(self) -> None:
        """Initializes a part-like file from FreeCAD."""
        # The body and origin of a part file is the context everything else is 
        # defined under, so they will be consistent between part files
        self._part_file = PartFile(self.stem)
        self._mapping = FreeCADMap(self._document, self._part_file)
        body = self._get_bodies()[0]
        self._mapping.add_freecad_feature(body)
    
    # Python Dunders #
    def __fs_path__(self):
        return self.filepath