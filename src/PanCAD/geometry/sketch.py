"""A module providing a class to represent sketches in 3D space. PanCAD defines a 
sketch as a set of 2D geometry on a coordinate system's plane oriented in 3D 
space. PanCAD's sketch definition aims to be as general as possible, so the 
base implementation of this class does not include appearance information since 
that is application specific.


"""
from __future__ import annotations

from PanCAD.geometry import CoordinateSystem
from PanCAD.geometry.constants import PlaneName

class Sketch:
    """A class representing a set of 2D geometry on a coordinate system plane in 
    3D space.
    
    :param coordinate_system: A coordinate system defining where the sketch's 
        location and orientation.
    :param plane_name: A string specifying which plane of the coordinate 
        system to place the geometry on. Options include: XY, XZ, YZ. Defaults
        to XY.
    :param geometry: A list of 2D PanCAD geometry. Defaults to an empty list.
    :param constraints: A list of PanCAD constraints. Defaults to an empty list.
    :param externals: A list of 3D PanCAD geometry that can be referenced by the 
        constraints. Defaults to an empty list.
    :param uid: The unique id of the Sketch. Defaults to None.
    """
    
    def __init__(self,
                 coordinate_system: CoordinateSystem, plane_name: str="XY",
                 geometry: list=[], constraints: list=[], externals: list=[],
                 uid: str=None):
        self.uid = uid
        self.coordinate_system = coordinate_system
        self.geometry = geometry
        self.constraints = constraints
        self.plane_name = plane_name
    
    # Getters #
    @property
    def coordinate_system(self) -> CoordinateSystem:
        """The coordinate system of the sketch.
        
        :getter: Returns the CoordinateSystem object
        :setter: Sets the sketch coordinate system and syncs the rest of the 
            sketch to the new coordinate system
        """
        return self._coordinate_system
    
    @property
    def plane_name(self) -> str:
        """The name of the CoordinateSystem's plane that contains the sketch's
        geometry. The name must be one of the enumeration values in 
        PanCAD.geometry.constants.PlaneName.
        
        :getter: Returns the name of the plane
        :setter: Checks name validity and then sets the name of the plane
        """
        return self._plane_name
    
    @property
    def geometry(self) -> list:
        """The list of 2D geometry in the sketch.
        
        """
        return self._geometry
    
    # Setters #
    @coordinate_system.setter
    def coordinate_system(self, coordinate_system: CoordinateSystem):
        self._coordinate_system = coordinate_system
    
    @plane_name.setter
    def plane_name(self, letters: str):
        ordered_letters = "".join(
            sorted(letters.upper())
        )
        if ordered_letters in list(PlaneName):
            self._plane_name = ordered_letters
        else:
            raise ValueError(f"{letters} not recognized as a plane name, must"
                             f" be one of {list(PlaneName)}")
    
    @geometry.setter
    def geometry(self, geometry: list):
        non_2d_geometry = list(
            filter(lambda g: len(g) != 2, geometry)
        )
        if non_2d_geometry != []:
            raise ValueError(f"2D Geometry only, 3D: {non_2d_geometry}")
        
        self._geometry = geometry
    
    # Public Functions #
    def get_plane(self):
        """Returns a copy of the plane that contains the sketch geometry.
        
        :returns: A copy of the sketch plane
        """
        return self.coordinate_system.get_plane_by_name(self.plane_name)