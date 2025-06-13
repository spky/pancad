"""A module providing a constraint class for coincident relations between two 
geometry elements.

"""
from __future__ import annotations

from PanCAD.geometry import Point, Line, LineSegment, Plane
from PanCAD.geometry.spatial_relations import coincident

class Coincident:
    GeometryType = Point | Line | LineSegment | Plane
    
    def __init__(self, geometry_a: GeometryType, geometry_b: GeometryType,
                 uid: str=None):
        self.uid = uid
        if len(geometry_a) == len(geometry_b):
            self._a = geometry_a
            self._b = geometry_b
        else:
            raise ValueError("Geometry a and b must have the same number"
                             " of dimensions")
    
    # Public Methods
    def check(self) -> bool:
        """Returns whether the constraint is met by the geometry"""
        return coincident(self._a, self._b)
    
    def get_a(self) -> GeometryType:
        return self._a
    
    def get_b(self) -> GeometryType:
        return self._b
    
    # Python Dunders #
    def __repr__(self) -> str:
        return f"<Coincident'{self.uid}'{repr(self._a)}{repr(self._b)}>"
    
    def __str__(self) -> str:
        return (
            f"PanCAD Coincident Constraint '{self.uid}' with {repr(self._a)}"
            f" as geometry a and {repr(self._b)} as geometry b"
        )