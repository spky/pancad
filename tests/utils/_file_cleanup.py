"""A module providing utility methods to make unit testing pancad easier by 
deleting or otherwise working with files when tests are complete.
"""
from os import listdir, remove
from os.path import join

def delete_all_suffix(folder: str, suffix: str) -> None:
    """Deletes all files with the given suffix, usually an extension, in the 
    given folder.
    """
    for filename in listdir(folder):
        if filename.endswith(suffix):
            remove(join(folder, filename))