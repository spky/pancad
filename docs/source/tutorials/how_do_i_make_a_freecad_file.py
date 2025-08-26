# [corner-definition-start]
side_length = 1
bottom_left = (0, 0)
bottom_right = (side_length, 0)
top_right = (side_length, side_length)
top_left = (0, side_length)
# [corner-definition-end]

# [line-definition-start]
from PanCAD.geometry import LineSegment
bottom = LineSegment(bottom_left, bottom_right)
right = LineSegment(bottom_right, top_right)
top = LineSegment(top_right, top_left)
left = LineSegment(top_left, bottom_left)
# [line-definition-end]

# [sketch-definition-start]
from PanCAD.geometry import Sketch
sketch = Sketch(geometry=[bottom, right, top, left],
                uid="square_sketch")
# [sketch-definition-end]

# from PanCAD import PartFile
# filename = "tutorial_cube"
# sketch_name = "square_sketch"

# [constraint-definition-start]
from PanCAD.geometry.constants import ConstraintReference
from PanCAD.geometry.constraints import (Coincident, Distance,
                                         Horizontal, Vertical)
sketch.constraints = [
    # Corner Coincidence
    Coincident(bottom, ConstraintReference.START,
               left, ConstraintReference.END),
    Coincident(bottom, ConstraintReference.END,
               right, ConstraintReference.START),
    Coincident(right, ConstraintReference.END,
               top, ConstraintReference.START),
    Coincident(left, ConstraintReference.START,
               top, ConstraintReference.END),
    
    # Line Segment Orientations
    Horizontal(bottom, ConstraintReference.CORE),
    Horizontal(top, ConstraintReference.CORE),
    Vertical(right, ConstraintReference.CORE),
    Vertical(left, ConstraintReference.CORE),
    
    # Top/Bottom and Left/Right Distances
    Distance(bottom, ConstraintReference.CORE,
             top, ConstraintReference.CORE,
             side_length, unit="mm"),
    Distance(left, ConstraintReference.CORE,
             right, ConstraintReference.CORE,
             side_length, unit="mm"),
    
    # Constrain one corner to the origin
    Coincident(bottom,
               ConstraintReference.START,
               sketch.get_sketch_coordinate_system(),
               ConstraintReference.ORIGIN),
]
# [constraint-definition-end]

# [extrude-definition-start]
from PanCAD.geometry import Extrude
extrude = Extrude.from_length(sketch, side_length, "cube_extrude")
# [extrude-definition-end]

# [file-definition-start]
from PanCAD import PartFile
file = PartFile("tutorial_cube")
file.add_feature(sketch)
file.add_feature(extrude)
file.to_freecad("tutorial_cube.FCStd")
# [file-definition-end]

import os
os.remove(file.filename + ".FCStd")