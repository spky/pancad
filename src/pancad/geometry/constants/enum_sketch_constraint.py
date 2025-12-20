"""A module providing an enumeration for the constraint types available to 2D 
sketches"""

from enum import Flag, auto

class SketchConstraint(Flag):
    """An enumeration used to refer to a type of sketch constraint."""
    ANGLE = auto()
    """Refers to constraints on the angle between two geometry elements."""
    COINCIDENT = auto()
    """Refers to constraints holding two geometry elements to the same location.
    """
    COLLINEAR = auto()
    """Refers to constraints holding geometry elements to the same line."""
    DISTANCE = auto()
    """Refers to constraints holding geometry elements to a set distance from 
    each other at an arbitrary orientation.
    """
    DISTANCE_HORIZONTAL = auto()
    """Refers to constraints holding geometry elements to a set horizontal 
    distance from each other.
    """
    DISTANCE_VERTICAL = auto()
    """Refers to constraints holding geometry elements to a set vertical 
    distance from each other.
    """
    DISTANCE_RADIUS = auto()
    """Refers to constraints holding the radius of an arc to a specified value.
    """
    DISTANCE_DIAMETER = auto()
    """Refers to constraints holding the diameter of an arc to a specified
    value.
    """
    EQUAL = auto()
    """Refers to constraints holding contextual values of two geometry elements 
    to the same value. Example: 2 line segments to the same length.
    """
    HORIZONTAL = auto()
    """Refers to constraints holding a single geometry element (or multiple 
    geometry elements relative to each) other parallel to a 2D coordinate 
    system's x axis.
    """
    PARALLEL = auto()
    """Refers to constraints holding two geometry elements to be side by side 
    and have the same distance continuously between them.
    """
    PERPENDICULAR = auto()
    """Refers to constraints holding two geometry elements to be angled 90 
    degrees relative to each other.
    """
    SYMMETRIC = auto()
    """Refers to constraints holding two geometry elements to the same position 
    and orientation on opposite sides of a third geometry element.
    """
    TANGENT = auto()
    """Refers to constraints holding a geometry element to touch a curve at a 
    point while not also crossing the curve at that point.
    """
    VERTICAL = auto()
    """Refers to constraints holding a single geometry element (or multiple 
    geometry elements relative to each other) parallel to a 2D coordinate 
    system's y axis.
    """
