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
sketch = Sketch(geometry=[bottom, right, top, left], name="square_sketch")
# [sketch-definition-end]

# [constraint-definition-start]
from PanCAD.geometry.constants import ConstraintReference, SketchConstraint
from PanCAD.geometry.constraints import make_constraint

sketch.constraints = [
    # Corner Coincidence
    make_constraint(SketchConstraint.COINCIDENT,
                    bottom, ConstraintReference.START,
                    left, ConstraintReference.END),
    make_constraint(SketchConstraint.COINCIDENT,
                    bottom, ConstraintReference.END,
                    right, ConstraintReference.START),
    make_constraint(SketchConstraint.COINCIDENT,
                    right, ConstraintReference.END,
                    top, ConstraintReference.START),
    make_constraint(SketchConstraint.COINCIDENT,
                    left, ConstraintReference.START,
                    top, ConstraintReference.END),
    
    # Line Segment Orientations
    make_constraint(SketchConstraint.HORIZONTAL,
                    bottom, ConstraintReference.CORE),
    make_constraint(SketchConstraint.HORIZONTAL,
                    top,  ConstraintReference.CORE),
    make_constraint(SketchConstraint.VERTICAL,
                    right, ConstraintReference.CORE),
    make_constraint(SketchConstraint.VERTICAL,
                    left, ConstraintReference.CORE),
    
    # Top/Bottom and Left/Right Distances
    make_constraint(SketchConstraint.DISTANCE,
                    bottom, ConstraintReference.CORE,
                    top, ConstraintReference.CORE,
                    value=side_length, unit="mm"),
    make_constraint(SketchConstraint.DISTANCE,
                    left, ConstraintReference.CORE,
                    right, ConstraintReference.CORE,
                    value=side_length, unit="mm"),
    
    # Constrain one corner to the origin
    make_constraint(SketchConstraint.COINCIDENT,
                    bottom, ConstraintReference.START,
                    sketch, ConstraintReference.ORIGIN),
]
# [constraint-definition-end]

# [extrude-definition-start]
from PanCAD.geometry import Extrude
extrude = Extrude.from_length(sketch, side_length, name="cube_extrude")
# [extrude-definition-end]

# [file-definition-start]
from PanCAD import PartFile
file = PartFile("tutorial_cube")
file.features = [sketch, extrude]
file.to_freecad("tutorial_cube.FCStd")
# [file-definition-end]

# Clean up after tutorial
import os
os.remove(file.filename + ".FCStd")
for filename in os.listdir():
    if filename.endswith(".FCBak"):
        os.remove(filename)