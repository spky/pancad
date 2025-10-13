"""A module providing an enumeration for PanCAD cache and configuration 
categories.
"""
from enum import StrEnum, auto

class ConfigCategory(StrEnum):
    """An enumeration used for PanCAD cache and configuration category options.
    """
    
    APPLICATION_PATHS = auto()
    """Used to store paths to executables"""
    DEFAULT_INSTALL = auto()
    """Used to store paths to application-specific default installation 
    directories
    """
    FOLDERS = auto()
    """Used to store application-specific folder names."""