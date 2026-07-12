import tomllib
import os
import shutil
from platform import system
from unittest import TestCase
from pathlib import Path
from logging import getLogger
from importlib.util import find_spec

import pytest

from pancad.utils.initialize import write_cache
from pancad.cad.freecad._bootstrap import get_app_dir, find_app_dir

RESOURCES_PATH = Path(find_spec("pancad.resources").origin).parent
with open(RESOURCES_PATH / "pancad.toml", "rb") as file:
    CONFIG = tomllib.load(file)
USER_DIR = Path(os.path.expandvars(CONFIG["paths"]["user_dir"]))
FILENAMES = CONFIG["filenames"]
CONFIG_PATH = USER_DIR / FILENAMES["user_config"]
CACHE_PATH = USER_DIR / FILENAMES["cache"]
FREECAD_TOML = RESOURCES_PATH / "freecad.toml"

logger = getLogger(__name__)

@pytest.fixture(name="datadir_with_setup")
def fixture_datadir_with_setup(shared_datadir: Path) -> Path:
    CACHE_PATH.unlink(missing_ok=True)
    yield shared_datadir
    CONFIG_PATH.unlink(missing_ok=True)
    CACHE_PATH.unlink(missing_ok=True)

class TestSampleUserConfigs:
    """Tests using specialized user config sample files."""
    
    @staticmethod
    def copy_config_to_user(path: Path):
        """Copy/Pastes a sample config file to be the user config"""
        shutil.copyfile(path, CONFIG_PATH)
    
    @staticmethod
    def get_expected(sample_path: Path) -> str:
        with open(sample_path, "rb") as sample:
            return tomllib.load(sample)["application_paths"]["freecad"]
    
    def test_freecad_1_windows_bin(self, datadir_with_setup: Path):
        path = datadir_with_setup / "freecad_1_windows_bin.toml"
        self.copy_config_to_user(path)
        expected = self.get_expected(path)
        assert str(get_app_dir()) == expected
    
    def test_freecad_bin_user_config_fake(self, datadir_with_setup: Path):
        path = datadir_with_setup / "freecad_bin_user_config_fake.toml"
        self.copy_config_to_user(path)
        expected = self.get_expected(path)
        assert str(find_app_dir()) == expected
    
    def test_freecad_bin_user_config_fake_to_cache(self, datadir_with_setup: Path):
        path = datadir_with_setup / "freecad_bin_user_config_fake.toml"
        test_cache = {"application_paths": {"freecad": "FAKE_CACHE_PATH"}}
        write_cache(test_cache)
        expected = test_cache["application_paths"]["freecad"]
        assert str(find_app_dir()) == expected
    
class TestMissingUserConfigAndCache(TestCase):
    """Tests for how pancad handles the user's config and cache missing while 
    trying to import FreeCAD.
    """
    def setUp(self):
        CACHE_PATH.unlink(missing_ok=True)
        CONFIG_PATH.unlink(missing_ok=True)
    
    def test_defaults(self):
        with open(FREECAD_TOML, "rb") as defaults:
            expected_paths = tomllib.load(defaults)["default_install"][system()]
        expected_paths = list(map(Path, expected_paths))
        path = find_app_dir()
        self.assertIn(path, expected_paths)

class TestFreeCADSetUp(TestCase):
    def test_get_app_dir(self):
        path = get_app_dir()
        print(path)