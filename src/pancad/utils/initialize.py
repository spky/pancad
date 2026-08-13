"""A module with functions to initialize pancad. Does not import any of the rest
of pancad, only uses the location of the resources module.
"""
from __future__ import annotations

import os
import shutil
import logging
import tomllib
import json
from typing import TYPE_CHECKING, cast
from functools import cache
from importlib.util import find_spec
from pathlib import Path

if TYPE_CHECKING:
    from pancad.utils.pancad_types import PancadTomlConfig, PancadJsonCache

PANCAD_RESOURCES_MODULE = "pancad.resources" # The name of the internal pancad resources module.
PANCAD_CONFIG_FILENAME = "pancad.toml" # The name of the overall internal pancad config file.
logger = logging.getLogger(__name__)

@cache
def get_resources_path() -> Path:
    """Returns the path to the pancad resources directory without importing the module.

    :raises ModuleNotFoundError: When the pancad.resources module cannot be found.
    """
    spec = find_spec(PANCAD_RESOURCES_MODULE)
    if not spec:
        raise ModuleNotFoundError("Check install: Could not find the pancad.resources module")
    assert spec.origin is not None # resources module isn't a top level import
    return Path(str(spec.origin)).parent

@cache
def get_pancad_config() -> PancadTomlConfig:
    """Returns the internal pancad configuration data."""
    with open(get_resources_path() / PANCAD_CONFIG_FILENAME, "rb") as file:
        # pancad.toml is an internal config file, so it is cast to a type to enable type checking.
        # The config must be manually set to match the type rather than checking the structure
        # each run.
        return cast("PancadTomlConfig", tomllib.load(file))

@cache
def get_user_config_dir() -> Path:
    """Returns the path where pancad stores and reads user configuration data."""
    return Path(os.path.expandvars(get_pancad_config()["paths"]["user_dir"]))

@cache
def get_default_user_config_path() -> Path:
    """Returns the path where the default pancad user config file is stored within pancad."""
    return get_resources_path() / get_pancad_config()["filenames"]["default_user_config"]

@cache
def get_cache_path() -> Path:
    """Returns the path where pancad stores user cache data."""
    return get_user_config_dir() / get_pancad_config()["filenames"]["cache"]

def get_user_config() -> dict[str, dict[str, str]]:
    """Reads the user configuration files and returns them as a dict. If the
    file isn't found, a default user config file is copied from pancad into
    the location instead.

    :raises FileNotFoundError: Raised when the config file couldn't be returned
        even after trying to copy a new one into the location.
    """
    filepath = get_user_config_dir() / get_pancad_config()["filenames"]["user_config"]
    for _ in range(0, 2):
        try:
            with open(filepath, "rb") as file:
                return tomllib.load(file)
        except FileNotFoundError:
            filepath.parent.mkdir(exist_ok=True)
            shutil.copyfile(get_default_user_config_path(), filepath)
    raise FileNotFoundError("Could not find the user config file.")


def get_cache() -> PancadJsonCache:
    """Reads or creates the pancad cache and returns it as a dictionary."""
    path = get_cache_path()
    while True:
        try:
            with open(path, "r", encoding="utf-8") as file:
                # pancad cache files are internally generated, so the data is cast to a type to
                # enable type checking. Cache generation must be made to meet the PancadJsonCache
                # TypedDict or else errors will occur.
                data = json.load(file)
                assert isinstance(data, dict)
                return cast("PancadJsonCache", data)
        except FileNotFoundError:
            path.parent.mkdir(exist_ok=True)
            with open(path, "w", encoding="utf-8") as file:
                json.dump({}, file)
        except json.decoder.JSONDecodeError as err:
            # Handle when the cache was corrupted somehow
            logger.warning("Failed to decode cache json: %s", err)
            with open(path, "w", encoding="utf-8") as file:
                json.dump({}, file)


def write_cache(data: dict[str, dict[str, str]]) -> None:
    """Writes a new cache to the pancad config directory. Creates the user
    config directory if it's missing.
    """
    path = get_cache_path()
    while True:
        try:
            with open(path, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=2)
        except FileNotFoundError:
            path.parent.mkdir()
            continue
        break
