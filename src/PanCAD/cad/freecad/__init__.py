import sys
from PanCAD import CONFIG

# Handle the FreeCAD module imports during initialization so PanCAD freecad 
# modules can get it from one place.
if CONFIG.validate_options("freecad"):
    sys.path.append(CONFIG.options["freecad.bin_folder_path"])
else:
    raise ModuleNotFoundError(
        "Settings file does not have the binary path for "
        "freecad in the parameter freecad.bin_folder_path"
    )

import FreeCAD as App
import Sketcher
import Part

from PanCAD.cad.freecad.file import File