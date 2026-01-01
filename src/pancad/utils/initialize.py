"""A module with functions to initialize pancad.Does not import any of the rest 
of pancad, only uses the location of the resources module.
"""

import os
import shutil
import logging
import tomllib
import json
from importlib.util import find_spec
from pathlib import Path

PANCAD_RESOURCES_MODULE = "pancad.resources"
PANCAD_CONFIG_FILENAME = "pancad.toml"
_resources_path = Path(find_spec("pancad.resources").origin).parent
with open(_resources_path / "pancad.toml", "rb") as _config_file:
    CONFIG = tomllib.load(_config_file)
USER_CONFIG_DIR = Path(os.path.expandvars(CONFIG["paths"]["user_dir"]))
FILENAMES = CONFIG["filenames"]
CACHE_PATH = USER_CONFIG_DIR / FILENAMES["cache"]
USER_CONFIG_PATH = USER_CONFIG_DIR / FILENAMES["user_config"]
DEFAULT_USER_CONFIG_PATH = _resources_path / FILENAMES["default_user_config"]
logger = logging.getLogger(__name__)

def get_resources_path() -> Path:
    """Returns the path to the pancad resources directory without actually 
    importing the module.
    """
    return Path(find_spec(PANCAD_RESOURCES_MODULE).origin).parent


def get_pancad_config() -> dict[str, dict[str, str]]:
    """Reads the main pancad configuration file and returns it as a 
    dictionary.
    """
    with open(get_resources_path() / PANCAD_CONFIG_FILENAME, "rb") as file:
        return tomllib.load(file)


def get_user_config() -> dict[str, dict[str, str]]:
    """Reads the user configuration files and returns them as a dict. If the 
    file isn't found, a default user config file is copied from pancad into 
    the location instead.
    
    :raises FileNotFoundError: Raised when the config file couldn't be returned 
        even after trying to copy a new one into the location.
    """
    for _ in range(0, 2):
        try:
            with open(USER_CONFIG_PATH, "rb") as file:
                return tomllib.load(file)
        except FileNotFoundError:
            USER_CONFIG_PATH.parent.mkdir(exist_ok=True)
            shutil.copyfile(DEFAULT_USER_CONFIG_PATH, USER_CONFIG_PATH)
    raise FileNotFoundError("Could not find the user config file.")


def get_cache() -> dict[str, dict[str, str]]:
    """Reads or creates the pancad cache and returns it as a dictionary."""
    while True:
        try:
            with open(CACHE_PATH, "r", encoding="utf-8") as file:
                return json.load(file)
        except FileNotFoundError:
            CACHE_PATH.parent.mkdir(exist_ok=True)
            with open(CACHE_PATH, "w", encoding="utf-8") as file:
                json.dump({}, file)
        except json.decoder.JSONDecodeError as err:
            # Handle when the cache was corrupted somehow
            logger.warning("Failed to decode cache json: %s", err)
            with open(CACHE_PATH, "w", encoding="utf-8") as file:
                json.dump({}, file)


def write_cache(cache: dict[str, dict[str, str]]) -> None:
    """Writes a new cache to the pancad config directory. Creates the user 
    config directory if it's missing.
    """
    while True:
        try:
            with open(CACHE_PATH, "w", encoding="utf-8") as file:
                json.dump(cache, file, indent=2)
        except FileNotFoundError:
            CACHE_PATH.parent.mkdir()
            continue
        break
