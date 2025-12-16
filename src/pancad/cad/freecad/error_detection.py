"""A module providing functions to check whether a FreeCAD document contains 
errors or unattached geometry. These functions must be independent of other 
pancad FreeCAD functionality to allow them to be called using the FreeCAD 
version of Python. This module is meant to be called as a script, so it is one 
of the freecad module's public modules.
"""

import argparse
from enum import StrEnum, auto
import json

import FreeCAD as App

class ErrorCategory(StrEnum):
    """An enumeration used to define FreeCAD error categories for model validation.
    """
    DETACHED = auto()
    """When a sketch is not properly attached to geometry"""
    ERROR = auto()
    """When a feature has an explicit error. Can include solver errors, 
    conflicting constraints, open profile pads, etc.
    """
    UNCONSTRAINED = auto()
    """When a sketch contains geometry that is not fully constrained. Is not an 
    error, but is usually bad practice.
    """

def _parse_args() -> argparse.Namespace:
    """Reads the command line arguments given to the script."""
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

def _key(object_: App.DocumentObject) -> str:
    """Returns the report key for the FreeCAD object/"""
    return f"{object_.ID}: {object_.Label}"

def main():
    """This function receives arguments from the primary pancad instance to 
    check a .FCStd file for errors. It then reports the results into a 
    temporary json file so the primary pancad process can read it.
    """
    args = _parse_args()
    document = App.open(args.filepath)
    # Recompute the FreeCAD document before checking
    document.recompute()
    data = []
    for obj in document.Objects:
        if not obj.isValid():
            # Log errors on features
            data.append(
                (ErrorCategory.ERROR, (_key(obj), obj.getStatusString()))
            )
        if hasattr(obj, "AttachmentSupport") and not obj.AttachmentSupport:
            # Log objects detached from geometry
            data.append((ErrorCategory.DETACHED, _key(obj)))
        if hasattr(obj, "FullyConstrained") and not obj.FullyConstrained:
            # Log sketches that are not fully constrained
            data.append((ErrorCategory.UNCONSTRAINED, _key(obj)))
    report = {}
    for category, item in data:
        if isinstance(item, str):
            report.setdefault(category, []).append(item)
        else:
            name, status = item
            report.setdefault(category, {})[name] = status
    with open(args.temp_file_name, "w", encoding="utf-8") as file:
        json.dump(report, file)

if __name__ == "__main__":
    main()
