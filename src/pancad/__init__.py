"""This init module ensures that the configuration of pancad is set up 
correctly and provides access to the developer interface level classes.
"""
from pancad.utils.initialize import PANCAD_CONFIG_DIR, check_config
from pancad.filetypes import PartFile

check_config()
