"""A module used to call FreeCAD's Python executable and perform 
pancad-independent actions on those models.
"""

from pathlib import Path
from pprint import pformat
from subprocess import Popen
import os
import tempfile
import json

from . import error_detection
from ._bootstrap import find_app_dir

def call_freecad_python(program: str | Path, *args) -> dict:
    """Calls a python program using the FreeCAD python executable. Assumes that 
    the python program creates a json file for its outputs.
    
    :param program: The path-like to the program.
    :param args: The arguments for the python program.
    :returns: The dictionary read from the program's json output file.
    """
    exe = find_app_dir() / "python.exe"
    with tempfile.NamedTemporaryFile(delete=False) as file:
        temp_file_name = file.name
    with Popen([exe, program, temp_file_name, *args]) as proc:
        # proc = Popen([exe, program, temp_file_name, *args])
        proc.communicate()
        with open(temp_file_name, encoding="utf-8") as file:
            result = json.load(file)
    os.remove(temp_file_name)
    return result

def validate_freecad(fcstd_filepath: str | Path,
                     unconstrained_error: bool=False) -> None:
    """Uses the FreeCAD Python executable to raise an error if a FreeCAD model 
    has errors.
    
    :param fcstd_filepath: Path to a FCStd
    :param unconstrained_error: Sets whether containing an unconstrained sketch 
        counts as an error.
    :raises ValueError: Raised when the FreeCAD file contains an error.
    """
    report = call_freecad_python(error_detection.__file__, fcstd_filepath)
    if not unconstrained_error:
        report.pop(error_detection.ErrorCategory.UNCONSTRAINED, None)
    for _, values in report.items():
        if values:
            report_str = pformat(report)
            raise ValueError("Errors found in FreeCAD file"
                             f" {fcstd_filepath.name}! Report:\n{report_str}")
