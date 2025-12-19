# import sys
# import logging
# from ._bootstrap import find_app_dir

# logger = logging.getLogger(__name__)

# Handle the FreeCAD module imports during initialization so pancad freecad 
# modules can get it from one place.
# BIN_PATH = find_app_dir()
# sys.path.append(str(BIN_PATH))
# import FreeCAD as App
# import Sketcher
# import Part
# import PartDesign
# logger.debug(f"Imported FreeCAD API modules from {BIN_PATH}")

# from ._filetypes import FreeCADFile