"""A module for reading and storing PanCAD settings. This module file must be 
in the same directory as the defaults.ini file.
"""

import os
import configparser

from PanCAD.utils import file_handlers as fh
from PanCAD.utils import initialize

class Config:
    """A class representing the settings for PanCAD.
    
    :param filepath: The filepath to an .ini full of settings. Defaults to 
                     None, which causes Config to read local user settings
    """
    
    DEFAULT_SETTINGS_FILE = initialize.DEFAULTS_FILENAME
    
    WINDOWS_SEARCH_PATHS = (
        os.getcwd(),
        os.path.expandvars("%homepath%"),
        initialize.APPDATA,
    )
    REQUIRED_SETTINGS = {
        "pancad": {
            "pancad.default_save_path",
        },
        "svg": {
            "svg.auto_size_margin",
            "svg.default_unit",
            
            "svg.geometry_style.color_and_paint.fill",
            "svg.geometry_style.color_and_paint.stroke",
            "svg.geometry_style.color_and_paint.stroke-linecap",
            "svg.geometry_style.color_and_paint.stroke-linejoin",
            "svg.geometry_style.color_and_paint.stroke-width",
            
            "svg.construction_geometry_style.fill",
            "svg.construction_geometry_style.stroke",
            "svg.construction_geometry_style.stroke-linecap",
            "svg.construction_geometry_style.stroke-linejoin",
            "svg.construction_geometry_style.stroke-width",
        },
        "freecad": {
            "freecad.bin_folder_path"
        },
    }
    
    def __init__(self, filepath: str = None) -> None:
        self._read_defaults()
        
        if filepath is None:
            self.read_settings(initialize.USER_SETTINGS)
        else:
            self.read_settings(filepath)
    
    def read_settings(self, filepath: str) -> None:
        """Reads a settings.ini file into class instance properties.
        
        :param filepath: Path to a .ini file
        """
        self.config = Config._parse_config(filepath)
        self.options = Config._config_to_dict(self.config)
        options = Config._parse_options(self.config)
        if options > self.valid_options:
            invalid_options = options - self.valid_options
            raise InvalidOptionError(f"Unexpected options: {invalid_options}")
    
    def update_options(self, options: dict) -> None:
        """Updates the options in the options dictionary and config 
        configparser.
        
        :param options: A dictionary of options and their values to update
        """
        if options.keys() <= self.valid_options:
            for option in options:
                self.options[option] = options[option]
                section, raw_option = Config._parse_key(option)
                self.config[section][raw_option] = options[option]
        else:
            invalid_options = options.keys() - self.valid_options
            raise InvalidOptionError(f"Unexpected options: {invalid_options}")
    
    def validate_options(self, application: str) -> bool:
        """Returns whether the stored settings dictionary contains enough 
        information to successfully interface with the given application. 
        PanCAD can work with many different applications, so a fully 
        defined settings file should usually be unnecessary.
        
        :param application: The name of the application to validate settings for
        :returns: Whether or not the settings is defined enough to interface 
                  with the application
        """
        application = application.lower()
        return self.options.keys() >= self.REQUIRED_SETTINGS[application]
    
    def write(self, filepath: str) -> None:
        """Writes the config configparser to the given filepath.
        
        :param filepath: Filepath to write to
        """
        filepath = fh.filepath(filepath)
        if filepath.endswith(".ini"):
            with open(filepath, "w") as config_file:
                self.config.write(config_file)
        else:
            raise ValueError(f"Must be an ini file, not '{filepath}'")
    
    def _read_defaults(self) -> None:
        """Reads the defaults.ini file. Initializes _default_config (a 
        configparser.ConfigParser instance for the defaults.ini file), 
        default_options (a dict containing the populated default 
        options), and valid_options (the list of all options that are 
        allowed to be in PanCAD settings files).
        """
        defaults_path = Config._get_defaults_path()
        self._default_config = Config._parse_config(defaults_path)
        self.default_options = Config._config_to_dict(self._default_config)
        self.valid_options = Config._parse_options(self._default_config)
    
    def _read_user_settings(self) -> None:
        """Reads the settings file in the user's appdata PanCAD folder.
        """
        pass
    
    @staticmethod
    def _get_defaults_path() -> str:
        """Finds the filepath that the DEFAULT_SETTINGS_FILE should be based 
        on this module's filepath.
        
        :returns: The filepath of the DEFAULT_SETTINGS_FILE
        """
        config_py_path = os.path.abspath(__file__)
        defaults_dir = os.path.dirname(config_py_path)
        defaults_path = os.path.join(defaults_dir, Config.DEFAULT_SETTINGS_FILE)
        return fh.filepath(defaults_path)
    
    @staticmethod
    def _config_to_dict(config_parser: configparser.ConfigParser) -> dict:
        """Reads a configparser.ConfigParser instance into a dictionary. This 
        will only add options that have non-None values.
        
        :param config_parser: A configparser instance after reading a ini file
        :returns: A dictionary with keys formatted 'section.option'
        """
        settings = {}
        for section in config_parser:
            for option in config_parser[section]:
                value = config_parser[section][option]
                if value is not None:
                    option_name = ".".join([section, option])
                    settings[option_name] = config_parser[section][option]
        return settings
    
    @staticmethod
    def _parse_config(filepath: str) -> configparser.ConfigParser:
        """Initially reads a .ini file with configparser
        
        :param filepath: A filepath for an ini formatted file
        :returns: The configparser for the file at the filepath
        """
        filepath = fh.filepath(filepath)
        if fh.exists(filepath):
            if filepath.endswith(".ini"):
                config_parser = configparser.ConfigParser(allow_no_value=True)
                config_parser.read(filepath)
                return config_parser
            else:
                raise ValueError(f"Must be an ini file, not '{filepath}'")
        else:
            FileNotFoundError(f"No File found at '{filepath}'")
    
    @staticmethod
    def _parse_key(config_key: str) -> list[str, str]:
        """Reads a config dictionary key and returns a list.
        
        :param config_key: Key to parse
        :returns: A list of [section, option]
        """
        return config_key.split(".", 1)
    
    @staticmethod
    def _parse_options(config_parser: configparser.ConfigParser) -> set:
        """Returns all defined (None and non-None) keys in a config output.
        
        :param config_parser: A configparser instance after reading a ini file.
        :returns: A set of all the option keys in the config_parser in the 
                  form 'section.option'
        """
        options = set()
        for section in config_parser:
            for option in config_parser[section]:
                options.add(".".join([section, option]))
        return options

class InvalidOptionError(ValueError):
    """Raise when an unexpected option is found in a settings ini file."""

class SettingsMissingError(ValueError):
    """Raise when settings are missing from an .ini for a requested function"""