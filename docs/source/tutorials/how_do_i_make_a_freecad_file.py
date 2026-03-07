# [corner-definition-start]
side_length = 1
bottom_left = (0, 0)
bottom_right = (side_length, 0)
top_right = (side_length, side_length)
top_left = (0, side_length)
# [corner-definition-end]

# [line-definition-start]
from pancad.api import LineSegment
bottom = LineSegment(bottom_left, bottom_right)
right = LineSegment(bottom_right, top_right)
top = LineSegment(top_right, top_left)
left = LineSegment(top_left, bottom_left)
geometry = [bottom, right, top, left]
# [line-definition-end]

# [sketch-definition-start]
from pancad.api import Sketch
sketch = Sketch(name="square_sketch")
sketch.geometry_system.geometry.extend(geometry)
# [sketch-definition-end]

# [constraint-definition-start]
from pancad.api import make_constraint, SketchConstraint as SC
constraints = [
    # Corner Coincidence
    make_constraint(SC.COINCIDENT, bottom.start, left.end),
    make_constraint(SC.COINCIDENT, bottom.end, right.start),
    make_constraint(SC.COINCIDENT, right.end, top.start),
    make_constraint(SC.COINCIDENT, left.start, top.end),

    # Line Segment Orientations
    make_constraint(SC.HORIZONTAL, bottom),
    make_constraint(SC.HORIZONTAL, top),
    make_constraint(SC.VERTICAL, right),
    make_constraint(SC.VERTICAL, left),

    # Top/Bottom and Left/Right Distance
    make_constraint(SC.DISTANCE, bottom, top, value=side_length, unit="mm"),
    make_constraint(SC.DISTANCE, left, right, value=side_length, unit="mm"),

    # Constrain one corner to the origin
    make_constraint(SC.COINCIDENT, bottom.start, sketch.geometry_system.origin),
]
sketch.geometry_system.constraints.extend(constraints)
# [constraint-definition-end]

# [extrude-definition-start]
from pancad.api import Extrude
extrude = Extrude.from_length(sketch, side_length,
                              name="cube_extrude", unit="mm")
# [extrude-definition-end]

# [file-definition-start]
from pancad.api import PartFile
file = PartFile("tutorial_cube")
feature_system = file.container.feature_system
feature_system.features.append(sketch)
sketch_alignment = make_constraint(SC.ALIGN_AXES,
                                   feature_system.coordinate_system,
                                   sketch.pose.coordinate_system)
feature_system.constraints.append(sketch_alignment)
feature_system.features.append(extrude)
file.to_freecad("tutorial_cube.FCStd")
# [file-definition-end]

# Clean up after tutorial
import os
os.remove("tutorial_cube.FCStd")
for filename in os.listdir():
    if filename.endswith(".FCBak"):
        os.remove(filename)