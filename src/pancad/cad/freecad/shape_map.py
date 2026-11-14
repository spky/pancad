"""
shape_map.py contains utilities to read and parse data from FreeCAD mapping files including
ElementMap, MappedName, and IndexedName elements stored inside Shape.Map.txt files.
"""
from __future__ import annotations

import itertools
from collections.abc import Mapping
from typing import TYPE_CHECKING, NamedTuple


if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import Final, IO
    from os import PathLike

    NumberedLineIter = Iterator[tuple[int, bytes]]

def next_not_blank(lines: NumberedLineIter) -> tuple[int, str]:
    """Returns the first non-blank line number and text from an iterator."""
    i, raw = next((i, line) for i, line in lines if line.strip())
    return i, raw.decode("utf-8")

class ElementMapItems(NamedTuple):
    """The lists of children and names defined in a FreeCAD element map."""
    children: tuple[str, ...]
    names: tuple[str, ...]

class ShapeMapError(Exception):
    """An exception raised while reading a FreeCAD shape map text file."""

    def __init__(self, message: str, line_no: int | None=None):
        super().__init__(message)
        self.line_no = line_no

class ShapeMap(Mapping[int, "ElementMap"]):
    """The shape map defined by a txt file inside a FreeCAD fcstd file."""

    def __init__(self, filelike: IO[bytes]):
        self._version: str | None = None
        self._id: int | None = None
        self.postfixes: tuple[str, ...] = ()
        self.maps: list[ElementMap] = []
        lines: Iterator[tuple[int, bytes]] = enumerate(filelike)
        while True:
            if self._read_next(lines):
                break
        if not self._version:
            raise ShapeMapError("No ShapeMap version found in entire file.")
        if not self._id:
            raise ShapeMapError("No ShapeMap id found in entire file.")
        self._map: Mapping[int, ElementMap] = {m.id: m for m in self.maps}

    @property
    def version(self) -> str:
        """The FreeCAD shape map format version."""
        assert self._version is not None
        return self._version

    @property
    def id(self) -> int:
        """The id number of the shape map."""
        assert self._id is not None
        return self._id

    def _read_next(self, lines: NumberedLineIter) -> bool:
        # Reads the next line, processes and returns True when there are no lines left.
        try:
            i, text = next_not_blank(lines)
        except StopIteration:
            return True
        if "BeginElementMap" in text:
            self._read_version(i, text)
        elif "PostfixCount" in text:
            self._read_postfixes(i, text, lines)
        elif "MapCount" in text:
            self._read_maps(text, lines)
        elif "EndMap" in text:
            if not self.maps:
                raise ShapeMapError("File ended without any maps", i)
        else:
            raise ShapeMapError(f"Unexpected line ({i}) format: {text}", i)
        return False

    def _read_version(self, i: int, text: str) -> None:
        # Sets the ShapeMap type version.
        if i != 0:
            raise ShapeMapError("Expected BeginElementMap only on the first line", i)
        self._version = text.removeprefix("BeginElementMap ").strip()

    def _read_postfixes(self, i: int, text: str, lines: NumberedLineIter) -> None:
        self._id, count = map(int, text.split("PostfixCount"))
        if self.postfixes:
            raise ShapeMapError("Multiple postfix locations found", i)
        postfixes = []
        for _ in range(count):
            __, raw = next(lines)
            postfixes.append(raw.decode("utf-8").strip())
        self.postfixes = tuple(postfixes)

    def _read_maps(self, text: str, lines: NumberedLineIter) -> None:
        for _ in range(int(text.removeprefix("MapCount"))):
            header = next(b.decode("utf-8") for _, b in lines if b.startswith(b"ElementMap"))
            map_lines = itertools.takewhile(lambda x: not x[1].startswith(b"EndMap"), lines)
            self.maps.append(ElementMap(header, map_lines))

    def __getitem__(self, key: int) -> ElementMap:
        return self._map[key]

    def __iter__(self) -> Iterator[int]:
        yield from self._map

    def __len__(self) -> int:
        return len(self._map)

class ElementMap(Mapping[str, ElementMapItems]):
    """The element map inside a shape map inside a FreeCAD fcstd file."""

    prefix_map: Mapping[str, str] = {"children": "ChildCount", "names": "NameCount"}

    def __init__(self, header: str, lines: NumberedLineIter):
        self._map: dict[str, ElementMapItems] = {}
        self.index, self.id, name_count = map(int, header.removeprefix("ElementMap").split())
        for _ in range(name_count):
            self._add_name(lines)

    def _add_name(self, lines: Iterator[tuple[int, bytes]]) -> None:
        # Adds the next name in the lines to the map.
        i, text = next_not_blank(lines)
        name = text.strip()
        if name.startswith(tuple(self.prefix_map.values())):
            raise ShapeMapError("Could not find map name", i)
        items: dict[str, list[str]] = {}
        for prefix in self.prefix_map.values():
            i, text = next_not_blank(lines)
            if not text.startswith(prefix):
                raise ShapeMapError(f"Could not find {name} {prefix}", i)
            for _ in range(int(text.removeprefix(prefix))):
                i, raw = next(lines)
                items.setdefault(prefix, []).append(raw.decode("utf-8").strip())
        self._map[name] = ElementMapItems(
            *map(tuple, (items.get(v, []) for v in self.prefix_map.values()))
        )

    def __getitem__(self, key: str) -> ElementMapItems:
        return self._map[key]

    def __iter__(self) -> Iterator[str]:
        yield from self._map

    def __len__(self) -> int:
        return len(self._map)
