"""This module provides classes to wrap FreeCAD objects into more 
user-friendly structures.

class:

FreeCADModel

"""
import sys

#Part.LineSegment(App.Vector(1.2, 1.8, 0), App.Vector(5.2, 5.3, 0))

# Path to your FreeCAD.so or FreeCAD.pyd file
FREECADPATH = 'C:/Users/George/Documents/FreeCAD1/FreeCAD_1.0.0RC1-conda-Windows-x86_64-py311/FreeCAD_1.0.0RC1-conda-Windows-x86_64-py311/bin' 
sys.path.append(FREECADPATH) 
import FreeCAD as App
import Part
import Sketcher

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