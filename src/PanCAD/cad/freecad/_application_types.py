"""A module of FreeCAD type aliases."""

from PanCAD.cad.freecad import App, Sketcher, Part

FreeCADOrigin = App.DocumentObject
FreeCADBody = Part.BodyBase
FreeCADSketch = Sketcher.Sketch
FreeCADPad = Part.Feature
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