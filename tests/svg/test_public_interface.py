import sys
import os
from pathlib import Path

import pytest

import pancad

@pytest.fixture(name="rounded_rect_svg")
def fixture_rounded_rect_svg(self, shared_datadir: Path) -> Path:
    """Returns the path to an svg with a rounded rectangle and centered circle."""
    return shared_datadir / "rounded_rect_with_center_circle.svg"

@pytest.fixture(name="rounded_rect_fcstd")
def fixture_rounded_rect_fcstd(self, shared_datadir: Path) -> Path:
    """Returns the path to a FreeCAD file with a rounded rectangle and centered circle sketch."""
    return shared_datadir / "rounded_rect_with_center_circle.FCStd"

class TestSVGInterface:

    @pytest.mark.skip("Skipping until svg refactor")
    def test_read_write_svg(self, rounded_rect_svg: Path, tmp_path: Path):
        """Read an svg file and then write it to a folder."""
        out_path = tmp_path / "test_read_write_svg.svg"
        svg_file = pancad.read_svg(rounded_rect_svg)
        svg_file.write(out_path)

    def test_read_write_svg_defaulted_format(self):
        """Read an svg file and override its styles with the configuration file
        format."""
        pass

    @pytest.mark.skip("Skipping until svg refactor")
    def test_export_freecad_sketch_to_svg(self, rounded_rect_fcstd: Path, tmp_path: Path):
        """Read a freecad model and write one of its sketches as a svg file."""
        sketch_label = "xz_rounded_rectangle_with_circle"
        out_path = tmp_path / "test_export_freecad_sketch_to_svg.svg"
        freecad_file = pancad.read_freecad(rounded_rect_fcstd)
        freecad_sketch = freecad_file.get_sketch(sketch_label)
        sketch_svg_file = pancad.freecad_sketch_to_svg(freecad_sketch)
        sketch_svg_file.write(out_path)

    @pytest.mark.skip("Skipping until svg refactor")
    def test_import_svg_to_freecad_file(self, rounded_rect_svg: Path, tmp_path: Path):
        """Read a svg file and add it to a freecad model as a sketch."""
        out_path = tmp_path / "test_import_svg_to_freecad_file.FCStd"
        import_svg_file = pancad.read_svg(rounded_rect_svg)
        freecad_sketch = pancad.svg_to_freecad_sketch(import_svg_file)
        freecad_file = pancad.read_freecad(out_path, "w")
        freecad_file.new_sketch(freecad_sketch)
        freecad_file.save()

    def test_sync_freecad_sketch_and_svg_file(self):
        """Read both a freecad sketch and svg file, compare them, and update the
        oldest one to the newer one."""
        pass
