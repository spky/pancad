"""A module providing a functions defining how PanCAD opens, reads, 
writes, overwrites, and appends to files by default.
"""

import os

ACCESS_MODE_OPTIONS = ["r", "w", "x", "+"]
OPERATION_TYPES = ["r", "w"]

def filepath(filepath: str) -> str:
    """Returns the real filepath of the file and checks its validity.
    
    :param filepath: a string of the name and location of the file
    :returns: The real path of the file
    """
    if filepath is None:
        raise InvalidFilepathError("Filepath cannot be None")
    directory = os.path.dirname(filepath)
    if os.path.isfile(filepath):
        # Filepath is valid and file already exists
        return os.path.realpath(filepath)
    elif os.path.isdir(filepath):
        raise IsADirectoryError(f"'Filepath: '{filepath}'")
    elif os.path.isdir(directory) and os.path.basename(filepath) != "":
        # Filepath is valid but file does not exist
        return os.path.realpath(filepath)
    else:
        raise InvalidFilepathError(f"Filepath given: '{filepath}'")

def exists(path: str) -> bool:
    """Returns whether a file exists at the given filepath. If the 
    filepath is a directory or is a incorrectly formatted string it 
    will raise errors.
    
    :param filepath: a string of the name and location of the file
    :returns: A boolean for whether the file exists
    """
    path = filepath(path)
    directory = os.path.dirname(path)
    if os.path.isfile(path):
        return True
    elif os.path.isdir(directory) and os.path.basename(path) != "":
        return False
    else:
        raise InvalidFilepathError(f"Filepath: '{path}'")

def validate_mode(path:str, mode:str) -> None:
    """Checks whether the file mode is valid on the given filepath
    :param path: a string of the name and location of the file
    :param mode: the single character string describing the file's 
                 mode. read (r), write (w), exclusive creation (x), and 
                 read-write (+) 
    """
    path = filepath(path)
    file_exists = exists(path)
    if mode not in ACCESS_MODE_OPTIONS:
        raise InvalidAccessModeError(f"Mode: '{mode}'")
    elif mode == "x" and file_exists:
        raise ExclusiveCreationFileExistsError(f"Filepath: '{path}'")
    elif mode in "r" and not file_exists:
        raise FileNotFoundError(f"Filepath: '{path}'")

def validate_operation(path: str, mode: str, operation_type: str) -> None:
    """Checks whether the file mode is being violated by a specific 
    file operation and will raise an errors when settings are 
    violated to prevent data loss
    :param path: a string of the name and location of the file
    :param mode: the single character string describing the file's 
                 mode. read (r), write (w), exclusive creation (x), and 
                 read-write (+) 
    :param operation_type: a single character string describing the 
                           operation type, read (r), write (w)
    """
    path = filepath(path)
    file_exists = exists(path)
    validate_mode(path, mode)
    if operation_type not in OPERATION_TYPES:
        raise InvalidOperationModeError(f"Operation: '{operation_type}',")
    elif mode in ["w", "x"] and operation_type == "r":
        raise WriteOnlyError("Cannot read while in write-only"
                             + " or exclusive creation mode")
    elif mode == "r" and operation_type == "w":
        raise ReadOnlyError("Cannot write while in read-only mode")
    elif mode == "+" and operation_type == "r" and not file_exists:
        raise FileNotFoundError(f"Filepath: '{path}'")

class InvalidAccessModeError(ValueError):
    """Raise when a file access mode is not ACCESS_MODE_OPTIONS"""

class InvalidOperationModeError(ValueError):
    """Raise when a file modification operation mode is not in 
    OPERATION_TYPES"""

class ExclusiveCreationFileExistsError(FileExistsError):
    """Raise when trying to exclusively create an already existing file"""

class InvalidFilepathError(ValueError):
    """Raise when the filepath provided does not match a file or folder"""

class WriteOnlyError(ValueError):
    """Raise when trying to read a file when the mode is write-only"""

class ReadOnlyError(ValueError):
    """Raise when trying to write to a file when the mode is read-only"""