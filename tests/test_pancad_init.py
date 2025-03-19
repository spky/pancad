import sys
import os
from pathlib import Path
import unittest
import shutil

sys.path.append('src')

from PanCAD.utils import initialize as init

class TestPanCADInit(unittest.TestCase):
    def setUp(self):
        self.pancad_appdata = init.APPDATA
        self.user_settings_file = init.USER_SETTINGS
    
    @unittest.skip
    def test_appdata_folder_reload(self):
        if os.path.exists(self.pancad_appdata):
            shutil.rmtree(self.pancad_appdata)
        init.appdata_folder()
        self.assertTrue(os.path.exists(self.pancad_appdata))
    
    @unittest.skip
    def test_appdata_folder_found(self):
        init.appdata_folder()
    
    @unittest.skip
    def test_settings_reload(self):
        if os.path.exists(self.user_settings_file):
            os.remove(self.user_settings_file)
        init.settings()
        self.assertTrue(os.path.isfile(self.user_settings_file))
    
    @unittest.skip
    def test_settings_found(self):
        init.settings()
    
    @unittest.skip
    def test_delete_pancad_settings(self):
        init.delete_pancad_settings()
        self.assertFalse(os.path.exists(self.pancad_appdata))
        init.settings()

if __name__ == "__main__":
    with open("tests/logs/"+ Path(sys.modules[__name__].__file__).stem+".log", "w") as f:
        f.write("finished")
    unittest.main()