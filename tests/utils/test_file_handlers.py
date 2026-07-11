import sys
import os
from pathlib import Path

import pytest

from pancad.utils import file_handlers as fh

@pytest.fixture(name="valid_paths")
def fixture_valid_paths(tmp_path: Path) -> list[tuple[str, bool]]:
    """Returns a list of tuples with valid paths along with a boolean for whether they exist."""
    paths = []
    for i in range(2):
        path = tmp_path / f"i_exist{i}.txt"
        with open(path, "w", encoding="utf-8") as file:
            file.write("see, you can open me")
        paths.append((str(path), True))
    for i in range(2):
        paths.append((str(tmp_path / f"i_dont_exist{i}.txt"), False))
    return paths

@pytest.fixture(name="valid_folderpaths")
def fixture_valid_folderpaths(tmp_path: Path) -> list[str]:
    """Returns a list of valid folderpaths that exist."""
    paths = []
    for i in range(4):
        path = tmp_path / f"existing_folder_{i}"
        path.mkdir()
        paths.append(str(path))
    return paths

class TestFileHandlers:
    
    def test_filepath(self, valid_paths: list[tuple[str, bool]]):
        for path, _ in valid_paths:
            assert fh.filepath(path) == path
    
    def test_filepath_is_a_directory_error(self, tmp_path: Path):
        with pytest.raises(IsADirectoryError):
            test_path = fh.filepath(str(tmp_path))
    
    def test_filepath_not_valid(self):
        with pytest.raises(fh.InvalidFilepathError):
            test_path = fh.filepath("I am a bad string")
    
    def test_folderpath(self, valid_folderpaths: list[str]):
        for path in valid_folderpaths:
            assert fh.folderpath(path) == path
    
    def test_filepath_not_valid_none(self):
        with pytest.raises(fh.InvalidFilepathError):
            test_path = fh.filepath(None)
    
    def test_exists(self, valid_paths: list[tuple[str, bool]]):
        for i, (path, existence) in enumerate(valid_paths):
            assert fh.exists(path) == existence
    
    def test_exists_FolderNotFileError(self, tmp_path: Path):
        with pytest.raises(IsADirectoryError):
            test_exist = fh.exists(str(tmp_path))
    
    def test_exists_not_valid(self):
        with pytest.raises(fh.InvalidFilepathError):
            test_exist = fh.exists("I am a bad string")
    
    def test_validate_mode(self, valid_paths: list[tuple[str, bool]]):
        tests = [
            [0, "r"],
            [0, "w"],
            [0, "w"],
            [0, "+"],
            [0, "+"],
        ]
        for t in tests:
            fh.validate_mode(valid_paths[t[0]][0], t[1])
    
    def test_validate_operation(self, valid_paths: list[tuple[str, bool]]):
        tests = [
            [0, "r", "r"],
            [0, "w", "w"],
            [0, "w", "w"],
            [0, "+", "r"],
            [0, "+", "w"],
        ]
        for t in tests:
            fh.validate_operation(valid_paths[t[0]][0], t[1], t[2])
    
    def test_validate_operation_InvalidAccessModeError(self, valid_paths: list[tuple[str, bool]]):
        with pytest.raises(fh.InvalidAccessModeError):
            fh.validate_operation(valid_paths[0][0], "bad", "w")
    
    def test_validate_operation_InvalidOperationModeError(self,
                                                          valid_paths: list[tuple[str, bool]]):
        with pytest.raises(fh.InvalidOperationModeError):
            fh.validate_operation(valid_paths[0][0], "w", "bad")
    
    def test_validate_operation_ExclusiveCreationFileExistsError(
                self, valid_paths: list[tuple[str, bool]]
            ):
        with pytest.raises(fh.ExclusiveCreationFileExistsError):
            fh.validate_operation(valid_paths[0][0], "x", "w")
    
    def test_validate_operation_WriteOnlyError(self, valid_paths: list[tuple[str, bool]]):
        with pytest.raises(fh.WriteOnlyError):
            fh.validate_operation(valid_paths[0][0], "w", "r")
    
    def test_validate_operation_ReadOnlyError(self, valid_paths: list[tuple[str, bool]]):
        with pytest.raises(fh.ReadOnlyError):
            fh.validate_operation(valid_paths[0][0], "r", "w")
    
    def test_validate_operation_FileNotFoundError_read(self, valid_paths: list[tuple[str, bool]]):
        with pytest.raises(FileNotFoundError):
            fh.validate_operation(valid_paths[2][0], "r", "r")
    
    def test_validate_operation_FileNotFoundError_readwrite(self,
                                                            valid_paths: list[tuple[str, bool]]):
        with pytest.raises(FileNotFoundError):
            fh.validate_operation(valid_paths[2][0], "+", "r")
