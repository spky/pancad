"""A module defining FreeCAD type aliases."""

from . import App, Sketcher, Part

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