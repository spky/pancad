"""Utilities for plotting pancad tests."""
from __future__ import annotations

import csv
import tempfile
import getpass
from pathlib import Path
from functools import reduce
from typing import TYPE_CHECKING

import ipywidgets as widgets
from IPython.display import display as ip_display
from traitlets import TraitError
import matplotlib.pyplot as plt

if TYPE_CHECKING:
    from ipywidgets.widgets.widget import Widget

    ChangeDict = dict[str, str | Widget | None]

class TestPlotter:
    """A class for plotting data nested in test folders.

    :param root: The directory at the top of the data's directory. Defaults to the pytest
        temporary directory.
    """

    def __init__(self, root: Path=None):
        if root is None:
            root = Path(tempfile.gettempdir()) / f"pytest-of-{getpass.getuser()}"
        self._root = root
        selects = [
            ("run", widgets.RadioButtons, "Run Folder", self._on_run_change, {}),
            ("test", widgets.Dropdown, "Test Folder", self._on_test_change, {}),
            ("file", widgets.RadioButtons, "CSV File",
             self._on_file_change, {"width": "100%"}),
            ("series", widgets.SelectMultiple, "Series",
             self._on_series_change, {"width": "100%", "height": "300px"}),
        ]
        self._widgets = {}
        for key, widget_func, desc, on_change_func, layout_opts in selects:
            layout = widgets.Layout(**layout_opts)
            self._widgets[key] = widget_func(description=desc, layout=layout)
            self._widgets[key].observe(on_change_func, names="value")
        self._widgets.update({key: widgets.Output() for key in ("plot", "err")})
        self._widgets["run"].options = [d.stem for d in self._root.iterdir() if d.is_dir()]
        try:
            self._widgets["run"].index = len(self._widgets["run"].options)
        except TraitError:
            self._widgets["run"].index = None

    def display(self) -> None:
        """Displays data in TestPlotter's default order."""
        ip_display(*list(self._widgets.values()))

    def get_widgets(self) -> dict[str, Widget]:
        """Returns all widgets inside this TestPlotter."""
        return self._widgets

    def _on_run_change(self, change: ChangeDict) -> None:
        """Updates the test folder selection when the run selection is changed."""
        test = self._widgets["test"]
        if change["new"] is None:
            test.options = []
        else:
            path = self._root / change["new"]
            test.options = [d.stem for d in path.iterdir() if d.is_dir()]
        test.value = None

    def _on_test_change(self, change: ChangeDict) -> None:
        """Updates the csv file selection when the test folder selection is changed."""
        file = self._widgets["file"]
        if change["new"] is None:
            file.options = []
        else:
            run = self._widgets["run"].value
            path = self._root / run / change["new"]
            file.options = [str(f.relative_to(self._root))
                            for f in path.iterdir() if f.suffix == ".csv"]
        file.value = None

    def _on_file_change(self, change: ChangeDict) -> None:
        """Updates the data series selection when the file selection is changed."""
        series = self._widgets["series"]
        if change["new"] is None:
            series.options = []
        else:
            run = self._widgets["run"].value
            test = self._widgets["test"].value
            path = self._root / run / test / Path(change["new"]).name
            with open(path, newline="") as file:
                reader = csv.DictReader(file)
                series.options = list(next(reader))
        series.value = []

    def _on_series_change(self, change: ChangeDict) -> None:
        """Updates the output plot when the data series selection is changed."""
        with self._widgets["err"]:
            parts = [self._root,
                     *[Path(self._widgets[n].value).name for n in ("run", "test", "file")]]
            path = reduce(lambda a, b: a / b, parts)
            fig, ax = plt.subplots(num=1, clear=True)
            for name, vals in self._get_data(path, change["new"]).items():
                ax.plot(list(range(len(vals))), vals)
        self._widgets["plot"].clear_output()
        with self._widgets["plot"]:
            plt.show(fig)

    @staticmethod
    def _get_data(path: Path, series: list[str]) -> dict[str, float]:
        """Returns the data inside the selected csv file output."""
        with open(path, newline="") as file:
            reader = csv.DictReader(file, quoting=csv.QUOTE_NONNUMERIC)
            data = {}
            for row in reader:
                for key, value in row.items():
                    data.setdefault(key, []).append(value)
        return {k: v for k, v in data.items() if k in series}
