"""A module providing a class to represent points in all CAD programs, 
graphics, and other geometry use cases.
"""

import numpy as np

class Point:
    
    def __init__(self, position: tuple[float, float, float] = (None, None), *,
                 uid: str = None, unit: str = None):
        
        if uid:
            self.uid = uid
        
        if position:
            self.position = position
        
        if unit:
            self.unit = unit
    
    # Getters #
    @property
    def position(self) -> tuple[float, float, float]:
        return self._position
    
    @property
    def uid(self) -> str:
        return self._uid
    
    @property
    def x(self) -> float:
        return self._x
    
    @property
    def y(self) -> float:
        return self._y
    
    @property
    def z(self):
        return self._z
    
    # Setters #
    @position.setter
    def position(self, position: tuple[float, float, float]):
        self._position = position
    
    @uid.setter
    def uid(self, uid: str):
        self._uid = uid
    
    @x.setter
    def x(self, value: float):
        self.position[0] = value
    
    @y.setter
    def y(self, value: float):
        self.position[1] = value
    
    @z.setter
    def z(self, value: float):
        self.position[2] = value
    
    # Public Methods #
    def vector(self, vertical = True) -> np.ndarray:
        """Returns a numpy vector of the point's position"""
        array = np.array(self) 
        if vertical:
            return array.reshape(len(self.position), 1)
        else:
            return array
    
    # Python Dunders #
    def __iter__(self):
        self.dimension = 0
        return self
    
    def __next__(self):
        if self.dimension < len(self.position):
            i = self.dimension
            self.dimension += 1
            return self.position[i]
        else:
            raise StopIteration
    
    def __str__(self):
        return f"PanCAD Point at position {self.position}"
    
    # NumPy Dunders #
    def __array__(self, dtype=None, copy=None):
        return np.array(list(self))