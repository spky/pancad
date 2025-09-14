"""A module of FreeCAD type aliases."""

from PanCAD.cad.freecad import App, Sketcher, Part

FreeCADOrigin = App.DocumentObject
FreeCADFeature = Part.Feature | FreeCADOrigin | Sketcher.Sketch
FreeCADGeometry = Part.LineSegment | Part.Circle | Part.Point | Part.Ellipse
FreeCADConstraint = Sketcher.Constraint
FreeCADCADObject = FreeCADFeature | FreeCADGeometry | FreeCADConstraint