"""A module to provide classes to wrap FreeCAD objects into more 
user-friendly structures.
"""
import sys

from PanCAD.config import Config, SettingsMissingError
settings = Config()
if settings.validate_options("freecad"):
    sys.path.append(settings.options["freecad.bin_folder_path"])
else:
    raise SettingsMissingError("Settings file invalid for FreeCAD")

import FreeCAD as App
import Part

from PanCAD import file_handlers as fh

class Sketch:
    """A class representing a FreeCAD sketch external to the FreeCAD 
    software. Does not use the FreeCAD object directly since FreeCAD 
    does not allow direct creation of those objects, so this class 
    needs to be added to a model using the :class:'File' class
    """
    def __init__(self):
        """Constructor method"""
        self.label = None
        self.placement = None
        self.geometry = []
        self.construction = []
    
    def add_line(self, start: list, end: list,
                 construction: bool = False) -> None:
        """Adds a line to the sketch's geometry.
        
        :param start: [x, y] or [x, y, z] of the line's start
        :param end: [x, y] or [x, y, z] of the line's end
        """
        self._add_geometry(Sketch._line(start, end), construction)
    
    def add_circle(self, center: list, radius: float,
                   construction: bool = False) -> None:
        """Adds a circle to the sketch's geometry.
        
        :param center: [x, y] or [x, y, z] of the circle's center point
        :param radius: The radius of the circle
        """
        self._add_geometry(Sketch._circle(center, radius), construction)
    
    def add_circular_arc(self, center: list, radius: float,
                         start: float, end: float,
                         construction: bool = False) -> None:
        """Adds a circular arc to the sketch's geometry.
        
        :param center: [x, y] or [x, y, z] of the arc's center point
        :param radius: The radius of the arc
        :param start: The start angle of the arc in radians
        :param end: The end angle of the arc in radians
        :param construction: Sets whether to add the geometry as 
                             construction. Defaults to False.
        """
        self._add_geometry(Sketch._circular_arc(center, radius,
                                                start, end), construction)
    
    def add_point(self, location: list, construction: bool = False) -> None:
        """Adds a point to the sketch's geometry.
        
        :param location: [x, y] or [x, y, z] of the point's location
        """
        self._add_geometry(Sketch._point(location), construction)
    
    def _add_geometry(self, geometry, construction: bool) -> None:
        """Adds a FreeCAD geometry object to the constr
        
        :param geometry: A FreeCAD geometry object
        :param construction:Sets whether to add the geometry as construction.
        """
        if not construction:
            self.geometry.append(geometry)
        else:
            self.construction.append(geometry)
    
    def add_geometry_list(self, geometry: list[dict],
                          construction: bool = False) -> None:
        """Adds a list of FreeCAD geometry dictionaries to the sketch as 
        FreeCAD geometry objects
        
        :param geometry: a list of FreeCAD geometry dictionaries
        :param construction: Sets whether to add the geometry as 
                             construction. Defaults to False.
        """
        for g in geometry:
            geometry_type = g["geometry_type"]
            match geometry_type:
                case "line":
                    self.add_line(g["start"], g["end"], construction)
                case "circle":
                    self.add_circle(g["location"], g["radius"], construction)
                case "circular_arc":
                    
                    self.add_circular_arc(g["location"], g["radius"],
                                          g["start"], g["end"],
                                          construction)
                case "point":
                    self.add_point(g["location"], construction)
                case _:
                    raise ValueError(f"'{geometry_type}' is not supported")
    
    @staticmethod
    def _circle(center: list, radius: float) -> Part.Circle:
        """Creates a FreeCAD circle object. If a 2 element list is 
        provided for center, a zero will be appended to it. The 
        circle's axis vector is set to [0, 0, 1] internally.
        
        :param center: [x, y] or [x, y, z] of the circle's center point
        :param radius: The radius of the circle
        :returns: A Part.Circle FreeCAD object
        """
        if len(center) == 2:
            center.append(0)
        center_vector = App.Vector(center)
        axis = App.Vector([0, 0, 1])
        return Part.Circle(center_vector, axis, radius)
    
    @staticmethod
    def _line(start: list, end: list) -> Part.LineSegment:
        """Creates a FreeCAD LineSegment object. If a 2 element list is 
        provided a zero will be appended to it.
        
        :param start: [x, y] or [x, y, z] of the line's start
        :param end: [x, y] or [x, y, z] of the line's end
        :returns: A Part.LineSegment FreeCAD object
        """
        if len(start) == 2:
            start.append(0)
        start_vector = App.Vector(start)
        if len(end) == 2:
            end.append(0)
        end_vector = App.Vector(end)
        return Part.LineSegment(start_vector, end_vector)
    
    @staticmethod
    def _circular_arc(center: list, radius: float,
                      start: float, end: float) -> Part.ArcOfCircle:
        """Creates a FreeCAD ArcOfCircle object. If a 2 element list is 
        provided for center, a zero will be appended to it. FreeCAD 
        arcs are ALWAYS counter-clockwise, so the start angle has 
        to be placed clockwise of the end point
        
        :param center: [x, y] or [x, y, z] of the arc's center point
        :param radius: The radius of the arc
        :param start: The start angle of the arc in radians
        :param end: The end angle of the arc in radians
        :returns: A Part.ArcOfCircle FreeCAD object
        """
        circle = Sketch._circle(center, radius)
        return Part.ArcOfCircle(circle, start, end)
    
    @staticmethod
    def _point(location: list) -> Part.Point:
        """Creates a FreeCAD Point object.If a 2 element list is 
        provided for center, a zero will be appended to it.
        
        :param location: [x, y] or [x, y, z] of the point's location
        :returns: A Part.Point FreeCAD object
        """
        if len(location) == 2:
            location.append(0)
        position_vector = App.Vector(location)
        return Part.Point(position_vector)

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
        self.filepath = fh.filepath(filepath)
        if self._exists:
            self._document = App.open(self.filepath)
        else:
            self._document = App.newDocument()
            self._document.FileName = self.filepath
    
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
    
    @filepath.setter
    def filepath(self, filepath: str) -> None:
        if filepath is None:
            # filepath is allowed to be None during initialization
            self._exists = False
            self._filepath = None
        else:
            self._filepath = fh.filepath(filepath)
            if not self._filepath.endswith(self.EXTENSION):
                self._filepath = self._filepath + self.EXTENSION
            self._exists = fh.exists(filepath)
        self._validate_mode()
    
    @mode.setter
    def mode(self, mode: str) -> None:
        self._mode = mode
        self._validate_mode()
    
    def new_sketch(self, sketch: Sketch) -> None:
        """Adds a new Sketch to the File.
        
        :param sketch: A :class:'Sketch' object
        """
        
        if sketch.label is None:
            raise ValueError("Unnamed sketch input not yet supported")
        new_sketch = self._document.addObject(self.SKETCH_ID, sketch.label)
        for shape in sketch.geometry:
            new_sketch.addGeometry(shape, False)
        for shape in sketch.construction:
            new_sketch.addGeometry(shape, True)
    
    def _validate_mode(self) -> None:
        """Checks whether the current file mode is being violated and will 
        raise an InvalidAccessModeError if so.
        """
        if self._filepath is not None:
            # filepath is allowed to be None during initialization
            fh.validate_mode(self.filepath, self.mode)
        elif self._mode not in fh.ACCESS_MODE_OPTIONS:
            raise InvalidAccessModeError(f"Invalid Mode: '{self._mode}'")
    
    def save(self):
        """Saves the file if the current access mode allows it."""
        fh.validate_operation(self.filepath, self.mode, "w")
        self._document.recompute()
        self._document.save()

def make_placement(position: list, axis: list, angle: float) -> App.Placement:
    """Returns a Base.Placement object set based on the position, 
    axis, and angle given
    
    :param position: [x, y, z] position list
    :param axis: [x, y, z] axis list
    :param angle: rotation around axis
    :returns: Base.Placement object
    """
    return App.Placement(App.Vector(position), App.Vector(axis), angle)