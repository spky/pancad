"""A module to provide classes to wrap FreeCAD objects into more 
user-friendly structures.

class:

FreeCADModel

"""
import sys
import os

# Path to your FreeCAD.so or FreeCAD.pyd file
FREECADPATH = 'C:/Users/George/Documents/FreeCAD1/FreeCAD_1.0.0RC1-conda-Windows-x86_64-py311/FreeCAD_1.0.0RC1-conda-Windows-x86_64-py311/bin' 
sys.path.append(FREECADPATH) 
import FreeCAD as App
import Part
import Sketcher
import file_handlers as fh
import translators.svg_to_freecad_sketcher_translators as svg_to_fc

class Sketch:
    def __init__(self):
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
    
    def _add_geometry(self, geometry, construction: bool):
        """Adds a FreeCAD geometry object to the constr
        
        """
        if not construction:
            self.geometry.append(geometry)
        else:
            self.construction.append(geometry)
    
    def add_geometry_list(self, geometry: list[dict],
                          construction: bool = False) -> None:
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
        
        :param center: [x, y] of the circle's center point
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
    EXTENSION = ".FCStd"
    DOCUMENT_ID = 'App::Document'
    PART_ID = 'App::Part'
    BODY_ID = 'PartDesign::Body'
    SKETCH_ID = 'Sketcher::SketchObject'
    
    def __init__(self, filepath: str, mode: str = "r"):
        self._mode = mode
        self.filepath = fh.filepath(filepath)
        if self._exists:
            self._document = App.open(self.filepath)
        else:
            # TODO: Need to add write, overwrite, and read modes to this to make sure its predictable!!!!
            # These lines currently just append to the document
            self._document = App.newDocument()
            self._document.FileName = self.filepath
    
    @property
    def filepath(self) -> str:
        return self._filepath
    
    @property
    def mode(self) -> str:
        return self._mode
    
    @filepath.setter
    def filepath(self, filepath: str) -> None:
        """Sets the filepath of the svg and checks whether it can be 
        written to
        :param filepath: a string of the name and location of the file
        """
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
        """Checks the access mode controlling this file session. Can be r 
        (read-only), w (write-only), x (exclusive creation), and + 
        (reading and writing)
        :param mode: a string of one character describing the 
                            access mode of the session
        """
        self._mode = mode
        self._validate_mode()
    
    def _add_object(self, parent, object_type, object_name):
        object_ = self._document.addObject(object_type, object_name)
        if parent.TypeId != self.DOCUMENT_ID:
            object_ = parent.addObject(object_)[0]
        return object_
    
    def new_sketch(self, sketch: Sketch) -> None:
        if sketch.label is None:
            raise ValueError("Unnamed sketch input not supported yet")
        new_sketch = self._document.addObject(self.SKETCH_ID, sketch.label)
        for shape in sketch.geometry:
            new_sketch.addGeometry(shape, False)
        for shape in sketch.construction:
            new_sketch.addGeometry(shape, True)
    
    def _validate_mode(self) -> None:
        """Checks whether the file mode is being violated and will 
        raise an error if it is
        """
        if self._filepath is not None:
            # filepath is allowed to be None during initialization
            fh.validate_mode(self.filepath, self.mode)
        elif self._mode not in fh.ACCESS_MODE_OPTIONS:
            raise InvalidAccessModeError(f"Invalid Mode: '{self._mode}'")
    
    def save(self):
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
"""
position_vector = App.Vector(position)
        axis_vector = App.Vector(axis)
        placement = App.Placement(position_vector, axis_vector, angle)
        return FreeCADPlane.document_plane(placement, self._document)
"""
class FreeCADObject:
    """ Parent class with the properties common to all freecad objects 
    more easily accessible than by default"""
    
    def __init__(self, object_):
        self._object = object_
        self._name = self._object.Name
        self._label = self._object.Label
        self._document = self._object.Document
        self._placement = self._object.Placement
        self._axis = list(self._placement.Rotation.Axis)
        self._angle = self._placement.Rotation.Angle
        self._position = list(self._placement.Base)
    
    @property
    def name(self):
        return self._name
    
    @property
    def label(self):
        return self._label
    
    @label.setter
    def label(self, value):
        self._object.Label = value
        self._label = value
    
    @property
    def axis(self):
        return self._axis
    
    @property
    def angle(self):
        return self._angle
    
    @property
    def position(self):
        return self._position
    
    @property
    def placement(self):
        return self._placement
    
    @placement.setter
    def placement(self, Placement):
        self._placement = Placement
        self._axis = list(self.placement.Rotation.Axis)
        self._angle = self.placement.Rotation.Angle
        self._position = list(self.placement.Base)

class FreeCADPart(FreeCADObject):
    """ TODO: WRITE DOC STRING"""
    
    def __init__(self, part_object):
        super().__init__(part_object)

class FreeCADBody(FreeCADObject):
    """ TODO: WRITE DOC STRING"""
    
    def __init__(self, body_object):
        super().__init__(body_object)

class FreeCADSketch(FreeCADObject):
    """ TODO: WRITE DOC STRING"""
    
    def __init__(self, sketch_object):
        super().__init__(sketch_object)
    
    def add_line(self, start_point_2d, end_point_2d, construction=False):
        
        start_point = [start_point_2d[0], start_point_2d[1], 0]
        finish_point = [end_point_2d[0], end_point_2d[1], 0]
        start = App.Vector(start_point)
        finish = App.Vector(finish_point)
        line = Part.LineSegment(start, finish)
        self.object_.addGeometry([line],construction)

class FreeCADPlane(FreeCADObject):
    """ TODO: WRITE DOC STRING"""
    
    def __init__(self, plane_object):
        super().__init__(plane_object)
    
    @classmethod
    def document_plane(cls, placement, document):
        """This function is used to initialize planes in documents that 
        don't actually exist but are an option for the user to add a 
        sketch to"""
        object_ = cls.__new__(cls)
        object_._name = "virtual"
        object_._label = "virtual"
        object_._document = "virtual"
        object_._placement = placement
        object_.TypeId = 'App::Document'
        object_.object_ = document
        #super(FreeCADPlane, object_).__init__()
        return object_

class FreeCADModel:
    """ TODO: WRITE DOC STRING"""
    
    DOCUMENT_TYPE_ID = 'App::Document'
    PART_TYPE_ID = 'App::Part'
    BODY_TYPE_ID = 'PartDesign::Body'
    SKETCH_TYPE_ID = 'Sketcher::SketchObject'
    bodies = {}
    parts = {}
    sketches = {}
    
    def __init__(self, filepath):
        self._document = App.open(filepath)
        self.name = self._document.Name
        self.filepath = filepath
        self.xy_plane = self._make_virtual_plane([0, 0, 0],
                                                 [0, 0, 1],
                                                 0)
        self.xz_plane = self._make_virtual_plane([0, 0, 0],
                                                 [1, 0, 0],
                                                 90)
        # The yz axis is very odd in FreeCAD, the below list may need to be 
        # revised later
        self.yz_plane = self._make_virtual_plane([0, 0, 0],
                                                 [.577, .577, .577],
                                                 120)
        for object_ in self._document.Objects:
            match object_.TypeId:
                case self.BODY_TYPE_ID:
                    self.bodies[object_.Name] = FreeCADBody(object_)
                case self.PART_TYPE_ID:
                    self.parts[object_.Name] = FreeCADPart(object_)
                case self.SKETCH_TYPE_ID:
                    self.sketches[object_.Name] = FreeCADSketch(object_)
    
    def print_objects(self):
        for obj in self._document.Objects:
            print(obj.FullName)
    
    def _add_object(self, parent, object_type, object_name):
        object_ = self._document.addObject(object_type, object_name)
        if parent.TypeId != self.DOCUMENT_TYPE_ID:
            object_ = parent.addObject(object_)[0]
        return object_
    
    def add_body(self, parent):
        body_object = self._add_object(parent, self.BODY_TYPE_ID, "Body")
        body = FreeCADBody(body_object)
        self.bodies[body.name] = body
        return body
    
    def add_part(self, parent):
        part_object = self._add_object(parent, self.PART_TYPE_ID, "Part")
        part = FreeCADPart(part_object)
        self.parts[part.name] = part
        return part
    
    def add_sketch(self, parent):
        sketch_object = self._add_object(parent,self.SKETCH_TYPE_ID, "Sketch")
        sketch = FreeCADSketch(sketch_object)
        sketch.placement = parent.placement
        #sketch.MapMode = "Deactivated"
        self.sketches[sketch.name] = sketch
        return sketch
    
    def _make_virtual_plane(self, position, axis, angle):
        """ Returns an object to represent the invisible planes that 
        FreeCAD documents allow sketches to be bound to"""
        
        position_vector = App.Vector(position)
        axis_vector = App.Vector(axis)
        placement = App.Placement(position_vector, axis_vector, angle)
        return FreeCADPlane.document_plane(placement, self._document)
    
    def save(self):
        self._document.recompute()
        self._document.save()