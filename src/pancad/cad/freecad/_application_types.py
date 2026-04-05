"""A module defining FreeCAD type aliases. The classes that FreeCAD prints out 
inside of the application do not always match the classes that will return 
True from isinstance(). The aliases defined in this file are only for classes 
that will return True.
"""

from pancad.cad.freecad.api import freecad, freecad_sketcher, freecad_part

FreeCADDocument = freecad.Document
FreeCADOrigin = freecad.DocumentObject
"""FreeCAD Origins do not have their own class, usually need to be identified by 
their type id.
"""
FreeCADBody = freecad_part.BodyBase
FreeCADSketch = freecad_sketcher.Sketch
FreeCADPad = freecad_part.Feature
"""FreeCAD Pads do not have their own class, usually need to be identified by 
their type id
"""
FreeCADFeature = FreeCADPad | FreeCADOrigin | FreeCADSketch | FreeCADBody
FreeCADLineSegment = freecad_part.LineSegment
FreeCADCircle = freecad_part.Circle
FreeCADCircularArc = freecad_part.ArcOfCircle
FreeCADPoint = freecad_part.Point
FreeCADEllipse = freecad_part.Ellipse
FreeCADGeometry = (FreeCADLineSegment
                   | FreeCADCircle
                   | FreeCADPoint
                   | FreeCADEllipse)

FreeCADConstraint = freecad_sketcher.Constraint
FreeCADCADObject = (FreeCADFeature
                    | FreeCADGeometry
                    | FreeCADConstraint
                    | FreeCADBody)
FreeCADAPIObject = (FreeCADDocument
                    | FreeCADFeature
                    | FreeCADGeometry
                    | FreeCADConstraint)

FreeCADPlacement = freecad.Placement
