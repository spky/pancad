"""A module providing an enumeration for the portions of geometry that a 
constraint is referencing. For example, a constraint can be defined between a 
point and a line's end point, so constraints need a way to track what part 
of the line is being constrained.
"""
from enum import Flag, auto

class ConstraintReference(Flag):
    """An enumeration used by constraints to reference portions of geometry."""
    CORE = auto()
    """The geometry as a whole. Example: A line's CORE can be parallel to 
    another line's CORE.
    """
    START = auto()
    """The start of the geometry. Example: The start of a line segment."""
    END = auto()
    """The end of the geometry. Example: The end of a line segment."""
    CENTER = auto()
    """The center of the geometry. Example: The center point of a circle."""
    FOCAL_PLUS = auto()
    """The focal point of an ellipse in the positive direction of its major
    axis.
    """
    FOCAL_MINUS = auto()
    """The focal point of an ellipse in the negative direction of its major
    axis.
    """
    ORIGIN = CENTER
    """An alias for the center of the geometry. Example: The origin point of a 
    coordinate system.
    """
    X = auto()
    """The X-Axis of the geometry. Examples: The X axis of a coordinate system 
    or the major axis of an ellipse.
    """
    MAJOR_AXIS = X
    """An alias for X"""
    Y = auto()
    """The Y-Axis of the geometry. Examples: The Y axis of a coordinate system 
    or the minor axis of an ellipse.
    """
    MINOR_AXIS = Y
    """An alias for Y"""
    Z = auto()
    """The Z-Axis of the geometry."""
    XY = auto()
    """The XY-Plane of the geometry."""
    XZ = auto()
    """The XZ-Plane of the geometry."""
    YZ = auto()
    """The YZ-Plane of the geometry."""
    CS = auto()
    """The coordinate system of the geometry. Example: The coordinate system of 
    a sketch.
    """
    COORDINATE_SYSTEM = CS
    """An alias for CS."""
    
    def __repr__(self) -> str:
        return f"{self.name}"

class FeatureReference(Flag):
    """An enumeration used by features to reference portions of other 
    features.
    """
    ROOT = auto
    """The feature as a whole."""