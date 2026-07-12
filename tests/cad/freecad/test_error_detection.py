"""A collection of tests for pancad's ability to check FreeCAD files for validity and errors."""
from pathlib import Path

import pytest

from pancad.cad.freecad.freecad_python import call_freecad_python, validate_freecad
from pancad.cad.freecad import error_detection

class TestErrorDetection:
    """Tests for detecting invalid FreeCAD files using FreeCAD's application."""

    def test_invalid_sketches(self, shared_datadir: Path):
        """Test invalid sketch detection: detached sketches, unconstrained sketches, and errored
        sketches.
        """
        filename = "invalid_sketches.FCStd"
        test = call_freecad_python(error_detection.__file__, shared_datadir / filename)

        DETACHED = "unattached"
        NO_UNCONSTRAINED = 5
        NO_ERRORS = 4

        detached_errs = test["detached"]
        assert detached_errs[0].split(":")[-1].strip() == DETACHED
        assert len(detached_errs) == 1
        assert len(test["unconstrained"]) == NO_UNCONSTRAINED
        assert len(test["error"]) == NO_ERRORS

    def test_invalid_sketches_validation(self, shared_datadir: Path):
        """Test that validate_freecad can raise an error on incorrect files."""
        with pytest.raises(ValueError):
            validate_freecad(shared_datadir / "invalid_sketches.FCStd")

    def test_invalid_pads(self, shared_datadir: Path):
        """Test that invalid pads in freecad can be detected."""
        filename = "invalid_pads.FCStd"
        test = call_freecad_python(error_detection.__file__, shared_datadir / filename)
        assert len(test["unconstrained"]) == 1
        assert len(test["error"]) == 1

    def test_invalid_pads_validation(self, shared_datadir: Path):
        """Test that invalid pads in freecad raise an error when validated."""
        with pytest.raises(ValueError):
            validate_freecad(shared_datadir / "invalid_pads.FCStd")
