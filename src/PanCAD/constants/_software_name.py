"""A module providing an enumeration for the software that pancad is compatible 
with.
"""
from enum import StrEnum, auto

class SoftwareName(StrEnum):
    """An enumeration used to refer to software applications by standardizing 
    the spacing, capitalization, and spelling used by pancad.
    """
    
    FREECAD = auto()
    """References the FreeCAD CAD application. Download it from the 
    `FreeCAD website <https://www.freecad.org/downloads.php>`_.
    """
    OPENSCAD = auto()
    """References the OpenSCAD CAD application. Download it from the 
    `OpenSCAD website <https://openscad.org/downloads.html>`_.
    """
    PANCAD = auto()
    """References pancad, presumably the software that you're using! See 
    and download pancad's source code from the `pancad GitHub page 
    <https://github.com/spky/pancad>`_.
    """
    SOLVESPACE = auto()
    """References the SolveSpace CAD application. Download it from the 
    `SolveSpace website <https://solvespace.com/download.pl>`_.
    """