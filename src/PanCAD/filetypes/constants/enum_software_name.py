"""A module providing an enumeration for the software that PanCAD is compatible 
with.

"""
from enum import StrEnum

class SoftwareName(StrEnum):
    
    FREECAD = "FreeCAD"
    OPENSCAD = "OpenSCAD"
    SOLVESPACE = "SolveSpace"
    PANCAD = "PanCAD"