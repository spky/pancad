"""A module providing an enumeration for the software that PanCAD is compatible 
with.
"""
from enum import StrEnum

class SoftwareName(StrEnum):
    """An enumeration used to refer to software applications by standardizing 
    the spacing, capitalization, and spelling used by PanCAD.
    """
    
    FREECAD = "FreeCAD"
    """References the FreeCAD CAD application. Download it from the 
    `FreeCAD website <https://www.freecad.org/downloads.php>`_.
    """
    OPENSCAD = "OpenSCAD"
    """References the OpenSCAD CAD application. Download it from the 
    `OpenSCAD website <https://openscad.org/downloads.html>`_.
    """
    PANCAD = "PanCAD"
    """References PanCAD, presumably the software that you're using! See 
    and download PanCAD's source code from the `PanCAD GitHub page 
    <https://github.com/spky/PanCAD>`_.
    """
    SOLVESPACE = "SolveSpace"
    """References the SolveSpace CAD application. Download it from the 
    `SolveSpace website <https://solvespace.com/download.pl>`_.
    """