import sys
import os
from pathlib import Path
import unittest

sys.path.append('src')

from pancad.utils import file_handlers as fh

class TestFileHandlers(unittest.TestCase):
    def setUp(self):
        self.valid_paths = [
            [
                os.path.join("tests",
                             "sample_svgs",
                             "input_sketch_test.svg"),
                os.path.join(os.getcwd(),
                             "tests",
                             "sample_svgs",
                             "input_sketch_test.svg")
            ],
            [
                os.path.join(os.getcwd(),
                             "tests",
                             "sample_svgs",
                             "input_sketch_test.svg"),
                os.path.join(os.getcwd(),
                             "tests",
                             "sample_svgs",
                             "input_sketch_test.svg")
            ],
            [
                os.path.join(os.getcwd(),
                             "tests",
                             "sample_svgs",
                             "file_that_does_not_exist.fake"),
                os.path.join(os.getcwd(),
                             "tests",
                             "sample_svgs",
                             "file_that_does_not_exist.fake")
            ],
        ]
        self.valid_folderpaths = [
            [
                os.path.join("tests", "sample_svgs"),
                os.path.join(os.getcwd(), "tests", "sample_svgs")
            ],
            [
                os.path.join("%homepath%", "AppData"),
                os.path.join(os.path.realpath(os.path.expandvars("%homepath%")),
                             "AppData")
            ],
        ]
        self.valid_path_existence = [True, True, False, False]
        self.folder_path = os.path.join("tests", "sample_svgs")
        self.invalid_path = "I am a bad string"
    
    def test_filepath(self):
        for t in self.valid_paths:
            with self.subTest(t=t):
                self.assertEqual(fh.filepath(t[0]), t[1])
    
    def test_filepath_IsADirectoryError(self):
        with self.assertRaises(IsADirectoryError):
            test_path = fh.filepath(self.folder_path)
    
    def test_filepath_not_valid(self):
        with self.assertRaises(fh.InvalidFilepathError):
            test_path = fh.filepath(self.invalid_path)
    
    def test_folderpath(self):
        for t in self.valid_folderpaths:
            with self.subTest(t=t):
                self.assertEqual(fh.folderpath(t[0]), t[1])
    
    
    def test_filepath_not_valid_None(self):
        with self.assertRaises(fh.InvalidFilepathError):
            test_path = fh.filepath(None)
    
    def test_exists(self):
        for i, t in enumerate(self.valid_paths):
            with self.subTest(t=t):
                self.assertEqual(fh.exists(t[0]),
                                 self.valid_path_existence[i])
    
    def test_exists_FolderNotFileError(self):
        with self.assertRaises(IsADirectoryError):
            test_exist = fh.exists(self.folder_path)
    
    def test_exists_not_valid(self):
        with self.assertRaises(fh.InvalidFilepathError):
            test_exist = fh.exists(self.invalid_path)
    
    def test_validate_mode(self):
        tests = [
            [0, "r"],
            [0, "w"],
            [0, "w"],
            [0, "+"],
            [0, "+"],
        ]
        for t in tests:
            with self.subTest(t=t):
                fh.validate_mode(self.valid_paths[t[0]][0], t[1])
    
    def test_validate_operation(self):
        # First element is the index of valid_paths in setUp
        tests = [
            [0, "r", "r"],
            [0, "w", "w"],
            [0, "w", "w"],
            [0, "+", "r"],
            [0, "+", "w"],
        ]
        for t in tests:
            with self.subTest(t=t):
                fh.validate_operation(self.valid_paths[t[0]][0], t[1], t[2])
    
    def test_validate_operation_InvalidAccessModeError(self):
        with self.assertRaises(fh.InvalidAccessModeError):
            fh.validate_operation(self.valid_paths[0][0], "bad", "w")
    
    def test_validate_operation_InvalidOperationModeError(self):
        with self.assertRaises(fh.InvalidOperationModeError):
            fh.validate_operation(self.valid_paths[0][0], "w", "bad")
    
    def test_validate_operation_ExclusiveCreationFileExistsError(self):
        with self.assertRaises(fh.ExclusiveCreationFileExistsError):
            fh.validate_operation(self.valid_paths[0][0], "x", "w")
    
    def test_validate_operation_WriteOnlyError(self):
        with self.assertRaises(fh.WriteOnlyError):
            fh.validate_operation(self.valid_paths[0][0], "w", "r")
    
    def test_validate_operation_ReadOnlyError(self):
        with self.assertRaises(fh.ReadOnlyError):
            fh.validate_operation(self.valid_paths[0][0], "r", "w")
    
    def test_validate_operation_FileNotFoundError_read(self):
        with self.assertRaises(FileNotFoundError):
            fh.validate_operation(self.valid_paths[2][0], "r", "r")
    
    def test_validate_operation_FileNotFoundError_readwrite(self):
        with self.assertRaises(FileNotFoundError):
            fh.validate_operation(self.valid_paths[2][0], "+", "r")

if __name__ == "__main__":
    with open("tests/logs/"+ Path(sys.modules[__name__].__file__).stem+".log", "w") as f:
        f.write("finished")
    unittest.main()