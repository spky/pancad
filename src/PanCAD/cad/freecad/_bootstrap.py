"""A module providing functions for ensuring pancad's access to the FreeCAD 
application.
"""

from logging import getLogger
from pathlib import Path
from platform import system
from shutil import which
from tkinter import messagebox, filedialog
import tomllib

from pancad import data
from pancad.constants import ConfigCategory, SoftwareName
from pancad.utils.initialize import (
    get_application_paths, get_cache, write_cache
)

logger = getLogger(__name__)

def find_app_dir() -> Path:
    """Returns the path of the FreeCAD application directory. Prioritizes found 
    paths in this order: previous successful run cache, config file, environment, 
    defaults, user input. If the path was not already in the cache, it writes 
    the value to the cache for future runs.
    """
    path = None
    app_paths = get_application_paths()
    
    # Set a flag to make sure it's added to the cache if necessary
    in_cache = False
    if _check_cache() is not None:
        # Get Previous Runs if possible
        path = _check_cache()
        logger.info(f"Found FreeCAD bin using cache file here: '{path}'")
        in_cache = True
    elif _check_config() is not None:
        path = _check_config()
        logger.info(f"Found FreeCAD bin using config file here: '{path}'")
    elif _check_environment() is not None:
        path = _check_environment()
        logger.info(f"Found FreeCAD bin using environment: '{path}'")
    elif _check_defaults() is not None:
        path = _check_defaults()
        logger.info(f"Found FreeCAD bin using default: '{default_path}'")
    else:
        logger.warning("Could not find any candidate FreeCADs, asking user.")
        messagebox.showerror(
            title="FreeCAD Not Found",
            message=("pancad couldn't find your FreeCAD installation."
                     "\n\nPress OK to browse for a FreeCAD 'bin' folder or"
                     " press cancel and install FreeCAD")
        )
        path = _ask_for_freecad()
    
    path, in_cache = _confirm_app_path(path, in_cache)
    logger.info(f"Validated FreeCAD bin: '{path}'")
    
    if not in_cache:
        _write_to_cache(path)
    return path

def _ask_for_freecad() -> Path:
    """Asks the user for the bin path. Exits pancad if they cancel."""
    path_string = filedialog.askdirectory(mustexist=True,
                                          title="Select FreeCAD bin folder")
    if path_string == "":
        logger.critical("FreeCAD bin selection canceled by user")
        raise SystemError("FreeCAD bin selection canceled by user")
    return Path(path_string)

def _check_cache() -> Path | None:
    """Checks the pancad cache file to see if an application path was saved 
    there.
    """
    cache = get_cache()
    try:
        return Path(
            cache[ConfigCategory.APPLICATION_PATHS][SoftwareName.FREECAD]
        )
    except KeyError:
        return None

def _check_config() -> Path | None:
    """Checks the pancad config file to see if an application path is there."""
    app_paths = get_application_paths()
    if SoftwareName.FREECAD in app_paths:
        # Check if the path is in the config file and if it has been defined
        config_app_path = app_paths[SoftwareName.FREECAD]
        if config_app_path == "":
            logger.info(f"FreeCAD path option in config file but not defined")
            return None
        else:
            return Path(config_app_path)
    else:
        return None

def _check_defaults() -> Path | None:
    """Checks the defaults file to see if any of the default locations have a 
    FreeCAD install in them.
    """
    config_data = _read_data()
    for default_path in config_data[ConfigCategory.DEFAULT_INSTALL][system()]:
        if Path(default_path).is_dir():
            return Path(default_path)
    return None

def _check_environment() -> Path | None:
    """Checks the environment to see if the user has added FreeCAD to their PATH.
    """
    if which("FreeCAD") is not None:
        path = Path(which("FreeCAD")).parent
        return path

def _confirm_app_path(path: Path, in_cache: bool) -> Path:
    """Checks the path is valid and asks the user to correct it if not."""
    while True:
        try:
            path = _correct_install_dir(path)
            if not path.is_dir():
                raise NotADirectoryError(f"'{path}' is not a valid directory")
            elif not list(path.glob("FreeCAD.pyd")):
                raise FileNotFoundError(f"FreeCAD.pyd not found in '{path}'")
            else:
                break
        except NotADirectoryError:
            logger.warning("Could not find FreeCAD."
                           f" Invalid directory path: '{path}', asking user.")
            messagebox.showerror(
                title="Invalid FreeCAD Path",
                message=(
                    "The path for FreeCAD found below is not a valid"
                    f" directory path.\n\n{path}"
                    "\n\nPress OK to browse for a FreeCAD 'bin' folder"
                )
            )
            in_cache = False
            path = _ask_for_freecad()
        except FileNotFoundError:
            logger.warning("Could not find FreeCAD."
                           f" Missing FreeCAD.pyd here: '{path}', asking user.")
            messagebox.showerror(
                title="Missing FreeCAD.pyd",
                message=(
                    "The path for FreeCAD found below did not have FreeCAD.pyd:"
                    f"\n\n{path}"
                    "\n\nPress OK to browse for a FreeCAD 'bin' folder"
                )
            )
            in_cache = False
            path = _ask_for_freecad()
    return path, in_cache

def _correct_install_dir(path: Path) -> Path:
    """Checks to see if the users accidentally picked the installation directory 
    rather than the bin directory and modifies the path to the bin directory 
    if necessary.
    """
    install_dir = _read_data()[ConfigCategory.FOLDERS]["install_dir"]
    if path.name in install_dir:
        path = path / "bin"
    return path

def _read_data() -> dict:
    """Reads the freecad data toml."""
    filepath = Path(data.__file__).parent / "freecad.toml"
    with open(filepath, "rb") as file:
        config_data = tomllib.load(file)
    return config_data

def _write_to_cache(path: Path) -> None:
    cache = get_cache()
    if ConfigCategory.APPLICATION_PATHS not in cache:
        cache[ConfigCategory.APPLICATION_PATHS] = dict()
    cache[ConfigCategory.APPLICATION_PATHS][SoftwareName.FREECAD] = str(path)
    write_cache(cache)
