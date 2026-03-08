import os
from pathlib import Path
from unittest import TestCase
from importlib.util import find_spec
import tomllib
import shutil

from pancad.utils import initialize

RESOURCES_PATH = Path(find_spec("pancad.resources").origin).parent
with open(RESOURCES_PATH / "pancad.toml", "rb") as file:
    CONFIG = tomllib.load(file)
FILENAMES = CONFIG["filenames"]
USER_DIR = Path(os.path.expandvars(CONFIG["paths"]["user_dir"]))
DEFAULT_USER_CONFIG_PATH = RESOURCES_PATH / FILENAMES["default_user_config"]

class DeletedUserDir(TestCase):
    """Tests for how pancad handles a non-existent user directory."""
    def setUp(self):
        try:
            shutil.rmtree(USER_DIR)
        except FileNotFoundError:
            pass # Only handling FileNotFoundError, all other errors stop test
    
    def test_get_user_config(self):
        test = initialize.get_user_config()
        with open(DEFAULT_USER_CONFIG_PATH, "rb") as file:
            expected = tomllib.load(file)
        self.assertDictEqual(test, expected)
    
    def test_get_cache(self):
        test = initialize.get_cache()
        self.assertDictEqual(test, {})
    
    def test_write_cache(self):
        test_cache_dict = {"test": {"settings": "here"}}
        initialize.write_cache(test_cache_dict)
        test = initialize.get_cache()
        self.assertDictEqual(test, test_cache_dict)
        (USER_DIR / FILENAMES["cache"]).unlink()

class DeletedUserConfig(TestCase):
    """Tests for how pancad handles a deleted user config file"""
    def setUp(self):
        self.user_config_path = USER_DIR / FILENAMES["user_config"]
        self.user_config_path.unlink(missing_ok=True)
    
    def test_get_user_config(self):
        test = initialize.get_user_config()
        with open(DEFAULT_USER_CONFIG_PATH, "rb") as file:
            expected = tomllib.load(file)
        self.assertDictEqual(test, expected)

class DeletedCache(TestCase):
    """Tests for how pancad handles a deleted cache file"""
    def setUp(self):
        self.user_cache_path = USER_DIR / FILENAMES["cache"]
        self.user_cache_path.unlink(missing_ok=True)
    
    def test_get_cache(self):
        test = initialize.get_cache()
        self.assertDictEqual(test, {})
    
    def test_write_cache(self):
        test_cache_dict = {"test": {"settings": "here"}}
        initialize.write_cache(test_cache_dict)
        test = initialize.get_cache()
        self.assertDictEqual(test, test_cache_dict)
        self.user_cache_path.unlink()
