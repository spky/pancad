"""Module providing base input-output interfaces for FreeCAD."""
from __future__ import annotations

from typing import TYPE_CHECKING

from pancad.cad.freecad.read_xml import FCStd

if TYPE_CHECKING:
    from os import PathLike

    from pancad.filetypes.part_file import PartFile

def read_freecad(path: PathLike) -> PartFile:
    """Reads a FreeCAD file into a pancad file object.

    :param path: The path to a FreeCAD FCStd file.
    :raises ValueError: When the FreeCAD file is using features that pancad
        recognizes but cannot parse.
    :raises NotImplementedError: When the FreeCAD file is using known
        unsupported application features.
    """
    # Prevent FreeCAD from being imported until the last moment, otherwise
    # importing pancad will depend on the ability to import FreeCAD.
    # pylint: disable=import-outside-toplevel
    from pancad.cad.freecad._feature_translation import new_part_from_document
    fcstd = FCStd.from_path(path)
    return new_part_from_document(fcstd)
