"""A module defining FreeCAD type aliases. The classes that FreeCAD prints out 
inside of the application do not always match the classes that will return 
True from isinstance(). The aliases defined in this file are only for classes 
that will return True.
"""

from . import App, Sketcher, Part

FreeCADDocument = App.Document
FreeCADOrigin = App.DocumentObject
# FreeCAD Origins do not have their own class, usually need to be identified by 
# their type id
FreeCADBody = Part.BodyBase
FreeCADSketch = Sketcher.Sketch
FreeCADPad = Part.Feature
# FreeCAD Pads do not have their own class, usually need to be identified by 
# their type id
FreeCADFeature = FreeCADPad | FreeCADOrigin | FreeCADSketch | FreeCADBody

FreeCADLineSegment = Part.LineSegment
FreeCADCircle = Part.Circle
FreeCADCircularArc = Part.ArcOfCircle
FreeCADPoint = Part.Point
FreeCADEllipse = Part.Ellipse
FreeCADGeometry = (FreeCADLineSegment
                   | FreeCADCircle
                   | FreeCADPoint
                   | FreeCADEllipse)

FreeCADConstraint = Sketcher.Constraint

FreeCADCADObject = (FreeCADFeature
                    | FreeCADGeometry
                    | FreeCADConstraint
                    | FreeCADBody)