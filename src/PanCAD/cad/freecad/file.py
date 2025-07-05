"""A module providing a class to represent FreeCAD files."""
import os
from datetime import datetime, tzinfo

from PanCAD.cad.freecad import App, Sketcher
from PanCAD.utils import file_handlers
# from PanCAD.cad.freecad import Sketch

class File:
    """A class representing a FreeCAD file.
    
    :param filepath: The filepath of the FreeCAD file. If the file does 
                     not already exist, a file will be created but cannot 
                     be saved unless opened in a non-read-only mode.
    :param mode: The file access mode.
    """
    
    EXTENSION = ".FCStd"
    DOCUMENT_ID = 'App::Document'
    PART_ID = 'App::Part'
    BODY_ID = 'PartDesign::Body'
    SKETCH_ID = 'Sketcher::SketchObject'
    
    def __init__(self, filepath: str, mode: str = "r"):
        """Constructor method"""
        self._mode = mode
        self.filepath = file_handlers.filepath(filepath)
        if self._exists:
            self._document = App.open(self.filepath)
        else:
            self._document = App.newDocument()
            self._document.FileName = self.filepath
    
    @property
    def filename(self) -> str:
        """The name of the FreeCAD file without an extension"""
        name, _ = os.path.splitext(
            os.path.basename(self.filepath)
        )
        return name
    
    @property
    def filepath(self) -> str:
        """The filepath of the FreeCAD file
        
        :getter: Returns the filepath string
        :setter: Sets the filepath, checks if it exists, and validates the 
                 access mode against it. Can be None during construction.
        """
        return self._filepath
    
    @property
    def mode(self) -> str:
        """The file access mode. Can be r (read-only), w (write-only), x 
        (exclusive creation), and + (reading and writing)
        
        :getter: Returns the access mode string
        :setter: Sets the access mode and validates it against the filepath
        """
        return self._mode
    
    @filename.setter
    def filename(self, new_name: str) -> None:
        """The name of the FreeCAD file without an extension"""
        if self.mode == "r":
            raise ValueError("Cannot rename files in read-only mode")
        name, ext = os.path.splitext(new_name)
        if ext == self.EXTENSION or ext == "":
            directory = os.path.dirname(self.filepath)
            self.filepath = os.path.join(directory, name + self.EXTENSION)
        else:
            raise ValueError(f"Invalid Extension given: '{ext}'")
    
    @filepath.setter
    def filepath(self, filepath: str) -> None:
        self._filepath = file_handlers.filepath(filepath)
        if not filepath.endswith(self.EXTENSION):
            self._filepath = self._filepath + self.EXTENSION
        self._exists = file_handlers.exists(filepath)
        self._validate_mode()
    
    @mode.setter
    def mode(self, mode: str) -> None:
        self._mode = mode
        self._validate_mode()
    
    # Public Methods #
    
    def get_metadata(self, timezone: tzinfo=None) -> dict:
        attributes = [
            "Comment",
            "Company",
            "CreatedBy",
            "CreationDate",
            "FileName",
            "Id",
            "Label",
            "LastModifiedBy",
            "LastModifiedDate",
            "License",
            "LicenseURL",
            "Material",
            "Name",
            "OldLabel",
            "Uid",
            "UnitSystem",
        ]
        metadata = dict()
        for a in attributes:
            match a:
                case "CreationDate":
                    metadata[a] = self.get_creation_date(timezone)
                case "LastModifiedDate":
                    metadata[a] = self.get_last_modified_date(timezone)
                case _:
                    metadata[a] = getattr(self._document, a)
        return metadata
    
    def get_creation_date(self, timezone: tzinfo=None) -> datetime:
        date = datetime.fromisoformat(self._document.CreationDate)
        if timezone is None:
            timezone = datetime.now().astimezone().tzinfo
        return date.astimezone(tz=timezone)
    
    def get_last_modified_date(self, timezone: tzinfo=None) -> datetime:
        date = datetime.fromisoformat(self._document.LastModifiedDate)
        if timezone is None:
            timezone = datetime.now().astimezone().tzinfo
        return date.astimezone(tz=timezone)
    
    def get_unit_system(self):
        return self._document.UnitSystem
    
    
    # def new_sketch(self, sketch: Sketch) -> None:
        # """Adds a new Sketch to the File.
        
        # :param sketch: A :class:'Sketch' object
        # """
        
        # if sketch.label is None:
            # raise ValueError("Unnamed sketch input not yet supported")
        # new_sketch = self._document.addObject(self.SKETCH_ID, sketch.label)
        # for shape in sketch.geometry:
            # new_sketch.addGeometry(shape, False)
        # for shape in sketch.construction:
            # new_sketch.addGeometry(shape, True)
    
    # def get_sketch(self, label: str) -> Sketcher.Sketch:
        # """Returns the Sketch from the File with the given label if it exists.
        
        # :param label: The label of the sketch in FreeCAD
        # :returns: The FreeCAD Sketcher.Sketch object for the sketch
        # """
        # for fc_object in self._document.Objects:
            # if fc_object.TypeId == self.SKETCH_ID and fc_object.Label == label:
                # return fc_object
        # raise ValueError(f"File '{self.filepath}' has no '{label}' sketch")
    
    def _validate_mode(self) -> None:
        """Checks whether the current file mode is being violated and will 
        raise an InvalidAccessModeError if so.
        """
        file_handlers.validate_mode(self.filepath, self.mode)
    
    # def save(self) -> None:
        # """Saves the file if the current access mode allows it."""
        # file_handlers.validate_operation(self.filepath, self.mode, "w")
        # self._document.recompute()
        # self._document.save()