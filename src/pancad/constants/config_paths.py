"""A module providing constants for pancad configuration paths. Intended to be 
barebones so that multiple versions of Python can use this file.
"""
from os.path import expandvars
from pathlib import Path

from pancad import config

_CONFIG_NAME = "config.toml"
_CACHE_NAME = "cache.json"
_APPDATA = Path(expandvars("%appdata%"))
_DATABASE_NAME = "data.db"

PANCAD_CONFIG_DIR = _APPDATA / "pancad"
CACHE_FILEPATH = PANCAD_CONFIG_DIR / _CACHE_NAME
CONFIG_FILEPATH = PANCAD_CONFIG_DIR / _CONFIG_NAME
DEFAULTS_DIR = Path(config.__file__).parent
DATABASE = _APPDATA / _DATABASE_NAME