"""A module providing an enumeration class for the string constants that define 
FreeCAD object types like sketches, bodies, and other features."""

from enum import StrEnum

class ObjectType(StrEnum):
    BODY = "PartDesign::Body"
    SKETCH = "Sketcher::SketchObject"