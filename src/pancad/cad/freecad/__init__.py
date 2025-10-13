import sys

from ._bootstrap import find_app_dir

# Handle the FreeCAD module imports during initialization so pancad freecad 
# modules can get it from one place.
BIN_PATH = find_app_dir()
sys.path.append(str(BIN_PATH))

import FreeCAD as App
import Sketcher
import Part
import PartDesign

from ._filetypes import FreeCADFile