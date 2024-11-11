"""This module provides classes to wrap FreeCAD objects into more 
user-friendly structures.

class:

FreeCADModel

"""
import sys

Part.LineSegment(App.Vector(1.2, 1.8, 0), App.Vector(5.2, 5.3, 0))

# Path to your FreeCAD.so or FreeCAD.pyd file
FREECADPATH = 'C:/Users/George/Documents/FreeCAD1/FreeCAD_1.0.0RC1-conda-Windows-x86_64-py311/FreeCAD_1.0.0RC1-conda-Windows-x86_64-py311/bin' 
sys.path.append(FREECADPATH) 
import FreeCAD as App
import Part
import Sketcher

class FreeCADObject:
    """ TODO: WRITE DOC STRING"""
    
    def __init__(self, object_):
        self.object_ = object_
        self.name = object_.Name
        self.document = object_.Document
    
    def print_properties(self):
        print("name: " + self.name)

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
        self.document = App.open(filepath)
        self.name = self.document.Name
        self.filepath = filepath
        for object_ in self.document.Objects:
            match object_.TypeId:
                case self.BODY_TYPE_ID:
                    self.bodies[object_.Name] = FreeCADBody(object_)
                case self.PART_TYPE_ID:
                    self.parts[object_.Name] = FreeCADPart(object_)
                case self.SKETCH_TYPE_ID:
                    self.sketches[object_.Name] = FreeCADSketch(object_)
    
    def print_objects(self):
        for obj in self.document.Objects:
            print(obj.FullName)
    
    def _add_object(self, parent, object_type, object_name):
        match parent.TypeId:
            case self.DOCUMENT_TYPE_ID:
                object_ = parent.addObject(object_type, object_name)
            case self.PART_TYPE_ID:
                part_parent = parent.Document
                object_ = part_parent.addObject(object_type, object_name)
                object_ = parent.addObject(object_)[0]
        return object_
    
    def add_body(self, parent):
        body = self._add_object(parent, self.BODY_TYPE_ID, "Body")
        self.bodies[body.Name] = body
        return body
    
    def add_part(self, parent):
        part = self._add_object(parent, self.PART_TYPE_ID, "Part")
        self.parts[part.Name] = part
        return part
    
    #def add_sketch(self, parent):
    #    
    
    def save(self):
        self.document.recompute()
        self.document.save()