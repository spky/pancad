"""A module of FreeCAD type aliases."""

from PanCAD.cad.freecad import App, Sketcher, Part

FreeCADFeature = Part.Feature | App.DocumentObject | Sketcher.Sketch