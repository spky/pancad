"""
test_shape_map.py contains tests for reading the Shape.Map.txt files inside FreeCAD files.
"""
from __future__ import annotations

from pprint import pp
from typing import TYPE_CHECKING
from zipfile import ZipFile
from pathlib import Path

import pytest

from pancad.cad.freecad.shape_map import ShapeMap

from tests._typing import ArchiveFile

if TYPE_CHECKING:
    from typing import IO
    from io import IOBase
    from zipfile import ZipExtFile

def get_all_shape_maps() -> tuple[tuple[str, ...], tuple[ArchiveFile, ...]]:
    """Returns all the shape maps available in the test data folder inside each FCStd file."""
    data: list[tuple[str, ArchiveFile]] = []
    for fcstd in (Path(__file__).parent / "data").glob("*.FCStd"):
        with ZipFile(fcstd) as archive:
            assert archive.filename is not None
            for info in archive.filelist:
                if not info.filename.endswith("Shape.Map.txt"):
                    continue
                file_id = Path(archive.filename).stem
                sub_id = Path(info.filename).stem
                data.append((f"{file_id}:{sub_id}", ArchiveFile(fcstd, Path(info.filename))))
    return tuple(zip(*data, strict=True)) # type: ignore # zip type can't be detected here.

def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Generates the fixtures for testing shape maps in this file based on the data folder."""
    if "shape_map" in metafunc.fixturenames:
        ids, files = get_all_shape_maps()
        metafunc.parametrize("shape_map", files, ids=ids)

def test_read_shape_map(shape_map: ArchiveFile) -> None:
    """ShapeMap must read all FCStd SubShape/Shape.Map.txt files without raising errors."""
    with ZipFile(shape_map.path) as archive:
        try:
            info = next(f for f in archive.filelist if f.filename == str(shape_map.sub))
        except StopIteration as err:
            raise ValueError(f"Could not find {shape_map.sub} in {shape_map.path.stem}") from err
        with archive.open(info) as file:
            mapping = ShapeMap(file)
    for id_, element_map in mapping.items():
        print(f"Map {id_}:")
        pp(dict(element_map))
