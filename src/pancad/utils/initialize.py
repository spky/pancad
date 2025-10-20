"""A module with functions to initialize pancad. Intended to be called when 
pancad is imported"""

from os.path import expandvars
import shutil
import logging
import tomllib
import json
from pathlib import Path

from pancad import config
from pancad.constants import SoftwareName
from pancad.constants.config_paths import (
    CACHE_FILEPATH,
    CONFIG_FILEPATH,
    DEFAULTS_DIR,
    PANCAD_CONFIG_DIR,
)

logger = logging.getLogger(__name__)

def check_appdata_folder() -> None:
    """Checks whether the pancad appdata folder is available and creates it 
    if it isn't.
    """
    if PANCAD_CONFIG_DIR.is_dir():
        logger.info(f"pancad folder found here: {PANCAD_CONFIG_DIR}")
    else:
        logger.info("No pancad folder found, creating one here:"
                    f" '{PANCAD_CONFIG_DIR}'")
        PANCAD_CONFIG_DIR.mkdir()
        check_config() # Call to replace the missing settings file

def check_config() -> None:
    """Checks whether the pancad settings file is available and creates it 
    if it isn't.
    """
    if CONFIG_FILEPATH.is_file():
        logger.info(f"pancad user settings file found here: {CONFIG_FILEPATH}")
    else:
        logger.info(f"No pancad {CONFIG_FILEPATH.name} found, copying defaults"
                     + f"here: {DEFAULTS_DIR}")
        check_appdata_folder()
        shutil.copyfile(DEFAULTS_DIR / CONFIG_FILEPATH.name, CONFIG_FILEPATH)

def check_cache() -> None:
    """Checks whether the pancad cache file is available and creates it 
    if it isn't.
    """
    if CACHE_FILEPATH.is_file():
        logger.info(f"pancad user cache file found here: {CACHE_FILEPATH}")
    else:
        logger.info(f"No pancad {CACHE_FILEPATH.name} found, creating empty one"
                     + f"here: {CACHE_FILEPATH}")
        check_appdata_folder()
        with open(CACHE_FILEPATH, "w") as file:
            json.dump({}, file)

def delete_pancad_settings() -> None:
    """Deletes all pancad user specific settings. Useful for uninstallation.
    """
    if PANCAD_CONFIG_DIR.is_dir():
        shutil.rmtree(PANCAD_CONFIG_DIR)
    else:
        logger.warning(f"Attempted '{PANCAD_CONFIG_DIR}' config deletion,"
                       " but no folder found")

def get_application_paths() -> dict[str, Path]:
    """Returns a dictionary of configuration file setting filepaths"""
    check_appdata_folder()
    with open(CONFIG_FILEPATH, "rb") as file:
        config_data = tomllib.load(file)
    return config_data["application_paths"]

def get_cache() -> dict:
    """Reads or creates the pancad cache and returns it as a dictionary."""
    check_cache()
    with open(CACHE_FILEPATH) as file:
        return json.load(file)

def write_cache(cache: dict) -> None:
    """Writes a new cache to the pancad config directory. Intended to be used 
    shortly after a get_cache call to update the cache.
    """
    check_cache()
    with open(CACHE_FILEPATH, "w") as file:
        json.dump(cache, file, indent=2)