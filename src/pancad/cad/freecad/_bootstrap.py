"""A module providing functions for ensuring pancad's access to the FreeCAD 
application.
"""

from logging import getLogger
from pathlib import Path
from platform import system
from shutil import which
from importlib.util import find_spec
from tkinter import messagebox, filedialog
import tomllib

from pancad.utils.initialize import get_user_config, get_cache, write_cache

FREECAD_TOML = Path(find_spec("pancad.resources").origin).parent / "freecad.toml"
FREECAD = "freecad"
APPLICATION_PATHS = "application_paths"
DEFAULT_INSTALL = "default_install"
FOLDERS = "folders"
INSTALL_DIR = "install_dir"
FREECAD_PYD = "FreeCAD.pyd"

logger = getLogger(__name__)

def _check_freecad_config() -> str:
    """Returns the settings inside the pancad freecad config file.
    
    :raises NotImplementedError: If the current OS is not in the config file.
    :raises FileNotFoundError: If none of the defaults are directories or if the 
        freecad config file is missing.
    """
    with open(FREECAD_TOML, "rb") as file:
        system_defaults = tomllib.load(file)[DEFAULT_INSTALL]
    try:
        defaults = system_defaults[system()]
    except KeyError as err:
        raise NotImplementedError("Current OS defaults not supported") from err
    for default in defaults:
        if (path := Path(default)).is_dir():
            return path
    raise FileNotFoundError("No FreeCAD default directories in file system")

def get_app_dir(search_environment: bool=False) -> Path:
    """Returns the freecad application directory. Checks whether the directory 
    is valid. Updates the cache if the directory doesn't match the one in the 
    cache.
    
    :param search_environment: Sets whether to look in the user's PATH.
    """
    path = find_app_dir(search_environment)
    path = _validate_app_path(path)
    cache = get_cache()
    stored = cache.setdefault(APPLICATION_PATHS, {}).setdefault(FREECAD, "")
    if str(path) != stored:
        # Update cache with new path
        cache.setdefault(APPLICATION_PATHS, {})[FREECAD] = str(path)
        write_cache(cache)
    return path

def find_app_dir(search_environment: bool=False) -> Path:
    """Returns the path of the FreeCAD application directory. Prioritizes found 
    paths in this order: previous successful run cache, user config file, 
    environment, pancad defaults, user input.
    
    :param search_environment: Sets whether to look in the user's PATH.
    
    .. warning::
    
        Does not check whether the path actually has FreeCAD. Primary use of 
        this function is as an intermediary and to test whether pancad can find 
        each option.
    """
    try:
        # Check user cache
        path = get_cache()[APPLICATION_PATHS][FREECAD]
        logger.info("Found FreeCAD bin using cache file here: '%s'", path)
        return Path(path)
    except KeyError as not_in_cache_err:
        try:
            # Check user config
            path = get_user_config()[APPLICATION_PATHS][FREECAD]
            if path == "":
                logger.info("FreeCAD path option in user config file blank")
                raise KeyError from not_in_cache_err
            logger.info("Found FreeCAD bin using user config: '%s'", path)
            return Path(path)
        except KeyError as not_in_user_config_err:
            try:
                # Check user path
                if (path := which("FreeCAD")) is None or not search_environment:
                    raise KeyError from not_in_user_config_err
                logger.info("Found FreeCAD bin using environment: '%s'", path)
                return Path(path).parent
            except KeyError:
                try:
                    # Check default config
                    path = _check_freecad_config()
                    logger.info("Found FreeCAD bin using defaults: '%s'", path)
                    return path
                except FileNotFoundError:
                    # Ask user
                    logger.warning("Could not find candidates, asking user.")
                    messagebox.showerror(
                        title="FreeCAD Not Found",
                        message=(
                            "pancad couldn't find your FreeCAD installation."
                            "\n\nPress OK to browse for a FreeCAD 'bin' folder"
                            "or press cancel and install FreeCAD"
                        )
                    )
                    return _ask_for_freecad()

def _ask_for_freecad() -> Path:
    """Asks the user for the bin path. Exits pancad if they cancel.
    
    :raises SystemError: If the User canceled the FreeCAD bin selection.
    """
    path = filedialog.askdirectory(mustexist=True,
                                   title="Select FreeCAD bin folder")
    if path == "":
        logger.critical("FreeCAD bin selection canceled by user")
        raise SystemError("FreeCAD bin selection canceled by user")
    return Path(path)

def _validate_app_path(path: Path) -> Path:
    """Checks the path is valid and asks the user to correct it if not."""
    while True:
        try:
            path = _correct_install_dir(path)
            if not path.is_dir():
                raise NotADirectoryError
            if not list(path.glob(FREECAD_PYD)):
                raise FileNotFoundError(f"{FREECAD_PYD} not found in '{path}'")
            return path
        except NotADirectoryError:
            logger.warning("Invalid directory path: '%s', asking user.", path)
            messagebox.showerror(
                title="Invalid FreeCAD Path",
                message=("The path for FreeCAD found below is not a valid"
                         f" directory path.\n\n{path}"
                         "\n\nClick OK to browse for a FreeCAD 'bin' folder")
            )
            path = _ask_for_freecad()
        except FileNotFoundError:
            logger.warning("Missing %s here: '%s', asking user.",
                           FREECAD_PYD, path)
            messagebox.showerror(
                title=f"Missing {FREECAD_PYD}",
                message=("The path for FreeCAD found below did not have"
                         f" {FREECAD_PYD}:\n\n{path}"
                         "\n\nClick OK to browse for a FreeCAD 'bin' folder")
            )
            path = _ask_for_freecad()

def _correct_install_dir(path: Path) -> Path:
    """Checks to see if the users accidentally picked the installation directory 
    rather than the bin directory and modifies the path to the bin directory 
    if necessary.
    """
    with open(FREECAD_TOML, "rb") as file:
        install_dir = tomllib.load(file)[FOLDERS][INSTALL_DIR]
    if path.name in install_dir:
        path = path / "bin"
    return path
