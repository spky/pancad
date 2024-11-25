import sys

sys.path.append('../src')

from text2freecad.inkscape_interface import InkscapeDocument

in_filename = "input_sketch_test.svg"
out_filename = "output_sketch_test.svg"

ink = InkscapeDocument(in_filename)

print(ink.layers)
layer = ink.layers["Layer 1"]
path = layer.paths["path1"]

#new_coords = [[1,1],[2,.5]]

#path.d = path.absolute_move_to(new_coords)

ink.write(out_filename)
