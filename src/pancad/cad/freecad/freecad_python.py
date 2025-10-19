"""A module used to call FreeCAD's Python executable"""

from os import close, remove
from pathlib import Path
from subprocess import Popen
import tempfile
import json

from ._bootstrap import find_app_dir

def call_freecad_python(program: Path, *args) -> dict:
    """Calls a python program using the FreeCAD python executable. Assumes that 
    the python program creates a json file for its outputs.
    
    :param program: The path-like to the program.
    :param args: The arguments for the python program.
    :returns: The dictionary read from the program's json output file.
    """
    exe = find_app_dir() / "python.exe"
    file, temp_file_name = tempfile.mkstemp()
    close(file)
    
    proc = Popen([exe, program, temp_file_name, *args])
    proc.communicate()
    with open(temp_file_name) as file:
        result = json.load(file)
    remove(temp_file_name)
    
    return result