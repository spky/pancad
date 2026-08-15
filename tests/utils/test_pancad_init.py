"""Tests for initializing pancad and its configuration directories."""
from __future__ import annotations

from typing import TYPE_CHECKING
import shutil

import pytest

from pancad.utils import initialize

if TYPE_CHECKING:
    from collections.abc import Generator
    # dataframe_regression can take all serializable dictionaries and is an untyped module.
    from pytest_regressions.dataframe_regression import DataFrameRegressionFixture # type: ignore

@pytest.fixture(name="delete_user_dir")
def fixture_delete_user_dir() -> Generator[None]:
    """Deletes the user configuration directory before and after a test is run."""
    shutil.rmtree(initialize.get_user_config_dir(), ignore_errors=True)
    yield None
    shutil.rmtree(initialize.get_user_config_dir(), ignore_errors=True)

@pytest.mark.usefixtures("delete_user_dir")
class TestDeletedUserDir:
    """Tests for how pancad handles a non-existent user directory."""

    def test_get_user_config(self, data_regression: DataFrameRegressionFixture) -> None:
        """Test that the default user configuration file is loaded."""
        data_regression.check(initialize.get_user_config())

    def test_get_cache(self) -> None:
        """Test that the cache is returned as an empty dictionary."""
        assert initialize.get_cache() == {}

    def test_write_cache(self) -> None:
        """Test that the cache can be written to and read from successfully."""
        test_cache_dict = {"test": {"settings": "here"}}
        initialize.write_cache(test_cache_dict)
        assert initialize.get_cache() == test_cache_dict
