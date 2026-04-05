"""A stub module for importing the FreeCAD api. Allows other pancad modules to
use it without the extra logic of confirming that it's available in the local
environment.
"""

import sys

from pancad.cad.freecad._bootstrap import get_app_dir

for _ in range(0, 2):
    # Attempt to import the module twice. Once to see if it's already loaded,
    # and a second time to find it if it's not.
    try:
        import FreeCAD as freecad
        import Sketcher as freecad_sketcher
        import Part as freecad_part
    except ImportError:
        sys.path.append(str(get_app_dir()))
        continue
    break
