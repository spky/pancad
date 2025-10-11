"""A module providing an enumeration class for the string TypeID constants that 
define FreeCAD object types like sketches, bodies, and other features.
"""

from enum import StrEnum

class ObjectType(StrEnum):
    """An enumeration to used to define the FreeCAD feature TypeIDs supported by 
    PanCAD.
    """
    BODY = "PartDesign::Body"
    """FreeCAD's 3D geometry collection and FeatureContainer-like objects."""
    SKETCH = "Sketcher::SketchObject"
    """FreeCAD's Sketch equivalent."""
    PAD = "PartDesign::Pad"
    """FreeCAD's Extrude equivalent."""
    ORIGIN = "App::Origin"
    """FreeCAD's CoordinateSystem equivalent."""
    PART = "App::Part"
    """Both a geometry collection and collection of bodies in FreeCAD. Requires 
    more user input to define how they are being used inside of FreeCAD 
    prior to PanCAD interpretation.
    """