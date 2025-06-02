""" A module providing the SVG path element class
"""

class Path:
    
    def __init__(self, svg_id: str=None, d: str=None):
        self.d = path_data
    
    # Getters #
    @property
    def d(self) -> str:
        """The svg path data for the path element.
        
        :getter: Returns the path data string
        :setter: Sets path data string and updates the path's geometry
        """
        return self._d
    
    @property
    def geometry(self) -> tuple:
        pass
    
    # Setters #
    @d.setter
    def d(self, path_data: str):
        self._d = path_data
    
    def _parse_path_data(self, d: str) -> tuple:
        pass
    
    