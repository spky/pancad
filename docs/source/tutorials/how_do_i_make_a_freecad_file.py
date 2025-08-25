from PanCAD import PartFile
from PanCAD.geometry import LineSegment, Sketch, Extrude
from PanCAD.geometry.constraints import (Coincident,
                                         Distance,
                                         Horizontal,
                                         Vertical)
from PanCAD.geometry.constants import ConstraintReference as CR

filename = "tutorial_cube"
side = 1
unit = "mm"
sketch_name = "square_sketch"

bottom_left = (0, 0)
bottom_right = (side, 0)
top_right = (side, side)
top_left = (0, side)

bottom = LineSegment(bottom_left, bottom_right)
right = LineSegment(bottom_right, top_right)
top = LineSegment(top_right, top_left)
left = LineSegment(top_left, bottom_left)

sketch = Sketch(plane_reference=CR.XY,
                geometry=[bottom, right, top, left],
                uid="square_sketch")

sketch.constraints = [
    # Line Segment Orientations
    Horizontal(bottom, CR.CORE),
    Horizontal(top, CR.CORE),
    Vertical(right, CR.CORE),
    Vertical(left, CR.CORE),
    
    # Corner Coincidence
    Coincident(bottom, CR.START, left, CR.END),
    Coincident(bottom, CR.END, right, CR.START),
    Coincident(right, CR.END, top, CR.START),
    Coincident(left, CR.START, top, CR.END),
    
    # Constrain one corner to the origin
    Coincident(bottom, CR.START,
               sketch.get_sketch_coordinate_system(), CR.ORIGIN),
    
    # Height and Width
    Distance(bottom, CR.CORE, top, CR.CORE, side, unit=unit),
    Distance(left, CR.CORE, right, CR.CORE, side, unit=unit),
]
extrude = Extrude.from_length(sketch, side, "cube_extrude")

file = PartFile("tutorial_cube")
file.add_feature(sketch)
file.add_feature(extrude)
file.to_freecad(file.filename + ".FCStd")

import os
os.remove(file.filename + ".FCStd")