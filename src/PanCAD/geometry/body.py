"""A module providing a class to represent arbitrary 3D geometry bodies. 
PanCAD's sketch definition aims to be as general as possible, so the base 
implementation of this class does not include appearance information or 
metadata information that may be application specific.
"""


from __future__ import annotations

from PanCAD.geometry import CoordinateSystem, Plane, Sketch


class Body:
    """A class representing a 3D geometry body.
    
    """
    
    GEOMETRY_TYPES = (CoordinateSystem, Plane)
    
    def __init__(self, geometry: tuple=None, uid: str=None):
        self._uid = None
        if geometry is None:
            geometry = tuple()
        self._coordinate_system = CoordinateSystem((0, 0, 0))
        