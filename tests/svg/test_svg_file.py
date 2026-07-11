import sys
from pathlib import Path
import xml.etree.ElementTree as ET
import os

import pytest

import pancad
from pancad.graphics.svg import element_utils as seu
from pancad.graphics.svg import elements as se
from pancad.graphics.svg import file as sf
from pancad.graphics.svg import generators as sg

from pancad.utils.file_handlers import InvalidAccessModeError

@pytest.fixture(name="default_style")
def fixture_default_style() -> sg.SVGStyle:
    """A style with some default settings to be able to view the svg after writing."""
    style = sg.SVGStyle()
    settings = {"fill": "none", "stroke": "black", "stroke-width": "0.010467px",
                "stroke-linecap": "butt", "stroke-linejoin": "miter"}
    for key, value in settings.items():
        style.set_property(key, value)
    return style

@pytest.fixture(name="svg_tag")
def fixture_svg_tag() -> se.SvgTag:
    """An empty svg tag with inch units."""
    tag = se.SvgTag("svg1")
    tag.unit = "in"
    return tag

class TestFileInit:
    """Tests for initializing an SVGFile with a filepath."""

    @pytest.mark.parametrize("mode", ["w", "x", "+"])
    def test_non_read_init(self, mode: str, tmp_path: Path) -> None:
        """Test initializing on a filepath that doesn't exist runs with no error."""
        sf.SVGFile(tmp_path / "should_not_exist.svg", mode)

    def test_read_init(self, shared_datadir: Path) -> None:
        """Test that parsing on initialization of a read-mode SvgFile runs with no error."""
        file = sf.SVGFile(shared_datadir / "input_sketch_test.svg", "r")
        file.parse()

    @pytest.mark.skip("Skipping until svg refactor, see #221")
    def test_read_svg(self, shared_datadir: Path) -> None:
        """Test the public svg file reading interface."""
        file_instance = pancad.read_svg(shared_datadir / "input_sketch_test.svg")


class TestInternals:
    """Tests for SVGFile methods that don't need to read or write files."""

    def test_set_declaration(self):
        """Test that the svg files xml declaration is set correctly."""
        file = sf.SVGFile()
        file.set_declaration()
        test = ET.tostring(file._declaration)
        assert test == b'<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'

    def test_setting_svg(self):
        """Test that the file's svg element can be set."""
        file = sf.SVGFile()
        svg = se.SvgTag("svg1")
        file.svg = svg

    def test_resetting_svg(self):
        """Test that the default properties are removed from the original."""
        file = sf.SVGFile()
        svg1 = se.SvgTag("svg1")
        svg2 = se.SvgTag("svg2")
        file.svg = svg1
        file.svg = svg2
        assert ET.tostring(svg1) == b'<svg id="svg1" />'

    def test_validate_mode_InvalidAccessModeError(self):
        """Test that an invalid access mode raises an InvalidAccessModeError."""
        file = sf.SVGFile()
        with pytest.raises(InvalidAccessModeError):
            file.mode = "bad"


class TestSVGFileWriting:
    """Tests for writing svg files."""

    def test_write(self, svg_tag: se.SvgTag, default_style: sg.SVGStyle, tmp_path: Path) -> None:
        filepath = tmp_path / "test_svg_file_write"
        file = sf.SVGFile(filepath, "w")
        svg_tag.append(se.SvgGroup("g1"))
        svg_tag.sub("g1").set("style", default_style.string)
        svg_tag.sub("g1").append(se.SvgPath("path1", "M 0 0 1 1"))
        file.svg = svg_tag
        file.write(indent="  ")

    def test_write_circle(self, svg_tag: se.SvgTag, default_style: sg.SVGStyle,
                          tmp_path: Path) -> None:
        filepath = tmp_path / "test_svg_file_write_circle"
        file = sf.SVGFile(filepath, "w")
        svg_tag.append(se.SvgGroup("g1"))
        svg_tag.sub("g1").set("style", default_style.string)
        svg_tag.sub("g1").append(se.SvgCircle("c1", 0.5, 0.5, 0.5))
        file.svg = svg_tag
        file.write(indent="  ")
