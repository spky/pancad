import sys
import os
from pathlib import Path
import unittest

sys.path.append('src')

import PanCAD.config as config

class TestConfig(unittest.TestCase):
    def setUp(self):
        self.SAMPLE_DIR = os.path.join("tests", "sample_config")
        self.OUTPUT_DUMP = os.path.join("tests", "test_output_dump")
        self.NOMINAL_0 = os.path.join(self.SAMPLE_DIR,
                                      "test_nominal_settings_0.ini")
        self.INVALID_0 = os.path.join(self.SAMPLE_DIR,
                                      "test_invalid_options_0.ini")
    
    def test_read_settings(self):
        settings = config.Config(self.NOMINAL_0)
    
    def test_validate_options(self):
        settings = config.Config(self.NOMINAL_0)
        applications = ["svg", "SVG", "Svg"]
        for app in applications:
            with self.subTest(app=app):
                self.assertTrue(settings.validate_options(app))
    
    def test_read_defaults(self):
        settings = config.Config(self.NOMINAL_0)
    
    def test_read_invalid_options(self):
        with self.assertRaises(config.InvalidOptionError):
            settings = config.Config(self.INVALID_0)
    
    def test_update_options(self):
        tests = [
            {
                    "svg.geometry_style.color_and_paint.fill": "black",
            },
            {
                    "svg.geometry_style.color_and_paint.fill": "black",
                    "svg.geometry_style.color_and_paint.stroke": "red",
            },
        ]
        settings = config.Config(self.NOMINAL_0)
        for test in tests:
            with self.subTest(test=test):
                settings.update_options(test)
                ans_dict = dict()
                ans_config = dict()
                for key in test:
                    ans_dict[key] = settings.options[key]
                    section, raw_option = settings._parse_key(key)
                    ans_config[key] = settings.config[section][raw_option]
                    ans = [ans_dict, ans_config]
                self.assertCountEqual(ans, [test, test])
    
    def test_write(self):
        out_file_name = "test_config_write.ini"
        out_filepath = os.path.join(self.OUTPUT_DUMP, out_file_name)
        settings = config.Config(self.NOMINAL_0)
        settings.write(out_filepath)
    
    def test_init_none(self):
        settings = config.Config()

if __name__ == "__main__":
    with open("tests/logs/"+ Path(sys.modules[__name__].__file__).stem+".log", "w") as f:
        f.write("finished")
    unittest.main()