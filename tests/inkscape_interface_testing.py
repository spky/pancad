import sys

sys.path.append('../src')

from text2freecad.inkscape_interface import InkscapeDocument

filename = "input_sketch_test.svg"

ink = InkscapeDocument(filename)

#print(ink._svg_element)

#for e in ink.elements:
#    print(e.tag)
#print(ink.NAMESPACES)

for path in ink.layers["Layer 1"].paths:
    print(ink.layers["Layer 1"].paths[path].d)