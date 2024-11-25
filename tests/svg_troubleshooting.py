import sys

sys.path.append('../src')

from text2freecad.svg_interface import SVGPath

match = SVGPath.match_front_cmd("M 100,150 200,250 L 200,200")

print(match["match"]["coord"])