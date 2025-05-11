"""A module providing functions to convert parts of PanCAD geometry into other 
representations while avoiding the need for circular imports. Example: a 
LineSegment can be used to define a Line.
"""

from PanCAD.geometry import Line, LineSegment

def to_line(line_segment: LineSegment) -> Line:
    return line_segment.get_line()