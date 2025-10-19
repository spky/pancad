"""A module providing functions to check whether a FreeCAD document contains 
errors or unattached geometry. These functions must be independent of other 
pancad FreeCAD functionality to allow them to be called using the FreeCAD 
version of Python.
"""

import argparse
import json

import FreeCAD as App

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="PancadFreeCADErrorDetection",
        description=("pancad's script for detecting whether a FreeCAD file"
                     " has errors in it."),
    )
    parser.add_argument("temp_file_name",
                        help=("Filepath to the temporary file used by pancad to"
                              " read output"))
    parser.add_argument("filepath",
                        help="Filepath of the FreeCAD file to check")
    return parser.parse_args()

def _key(freecad_object: App.DocumentObject) -> str:
    return "{0}: {1}".format(freecad_object.ID, freecad_object.Label)

def main():
    args = _parse_args()
    
    document = App.open(args.filepath)
    
    # Recompute the FreeCAD document before checking
    document.recompute()
    
    data = []
    for obj in document.Objects:
        if not obj.isValid():
            # Log errors on features
            data.append(
                ("error", (_key(obj), obj.getStatusString()))
            )
        if hasattr(obj, "AttachmentSupport") and not obj.AttachmentSupport:
            # Log objects detached from geometry
            data.append(("detached", _key(obj)))
        if hasattr(obj, "FullyConstrained") and not obj.FullyConstrained:
            # Log sketches that are not fully constrained
            data.append(("unconstrained", _key(obj)))
    
    report = {}
    for category, item in data:
        if isinstance(item, str):
            report.setdefault(category, []).append(item)
        else:
            name, status = item
            report.setdefault(category, {})[name] = status
    with open(args.temp_file_name, "w") as file:
        json.dump(report, file)
    
if __name__ == "__main__":
    main()