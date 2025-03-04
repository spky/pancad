"""A module with functions to initialize PanCAD. Intended to be called when 
PanCAD is imported"""

import os
import shutil
import logging

APPDATA = os.path.expandvars(os.path.join("%appdata%", "PanCAD"))
SETTINGS_FILENAME = "settings.ini"
DEFAULTS_FILENAME = "defaults.ini"
USER_SETTINGS = os.path.join(APPDATA, SETTINGS_FILENAME)
DEFAULTS = os.path.join(os.getcwd(), "src", "PanCAD", DEFAULTS_FILENAME)

def appdata_folder() -> None:
    """Checks whether the PanCAD appdata folder is available and creates it 
    if it isn't.
    """
    if os.path.exists(APPDATA):
        logging.info(f"PanCAD folder found here: {APPDATA}")
    else:
        logging.info(f"No PanCAD folder found, creating one here: {APPDATA}")
        os.mkdir(APPDATA)
        settings() # Call to replace the missing settings file

def settings() -> None:
    """Checks whether the PanCAD settings file is available and creates it 
    if it isn't.
    """
    if os.path.isfile(USER_SETTINGS):
        logging.info(f"PanCAD user settings file found here: {USER_SETTINGS}")
    else:
        logging.info(f"No PanCAD {SETTINGS_FILENAME} found, copying defaults"
                     + f"here: {USER_SETTINGS}")
        if os.path.isfile(DEFAULTS):
            appdata_folder()
            shutil.copyfile(DEFAULTS, USER_SETTINGS)
        else:
            raise FileNotFoundError(f"No {DEFAULTS_FILENAME} found, please "
                                    + f"replace it or reinstall PanCAD")

def delete_pancad_settings() -> None:
    """Deletes all PanCAD user specific settings. Useful for uninstallation.
    """
    if os.path.exists(APPDATA):
        shutil.rmtree(APPDATA)
    else:
        logging.warning(f"Attempted {APPDATA} deletion, but no folder found")