"""Utilities for plotting pancad tests."""
from __future__ import annotations

from collections.abc import Sequence
import csv
import tempfile
import getpass
from pathlib import Path
from functools import reduce
from typing import TYPE_CHECKING, Literal, get_args

import ipywidgets as widgets # type: ignore
from IPython.display import display as ip_display
from traitlets import TraitError
import matplotlib.pyplot as plt
import plotly.express as px # type: ignore
import pandas as pd

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Optional

    from ipywidgets.widgets.widget import Widget # type: ignore

    ChangeDict = dict[str, str | list[str] | Widget | None]

PlotEngine = Literal["matplotlib", "plotly"]

class TestPlotter:
    """A class for plotting data nested in test folders.

    :param root: The directory at the top of the data's directory. Defaults to the pytest
        temporary directory.
    :param engine: The plotting package name to use to generate plots.
    """

    def __init__(self, root: Optional[Path]=None, engine: PlotEngine="plotly"):
        if engine not in get_args(PlotEngine):
            raise TypeError(f"Expected one of {get_args(PlotEngine)} for engine. Got: {engine}")
        if root is None:
            root = Path(tempfile.gettempdir()) / f"pytest-of-{getpass.getuser()}"
        self._engine = engine
        self._root: Path = root
        selects: list[tuple[str, Widget, str, Callable[[ChangeDict], None], dict[str, str]]] = [
            ("run", widgets.RadioButtons, "Run Folder", self._on_run_change, {}),
            ("test", widgets.Dropdown, "Test Folder", self._on_test_change, {}),
            ("file", widgets.RadioButtons, "CSV File",
             self._on_file_change, {"width": "100%"}),
            ("series", widgets.SelectMultiple, "Series",
             self._on_series_change, {"width": "90%", "height": "300px"}),
        ]
        if self._engine == "plotly":
            self._fig = px.line()
            selects.extend(
                [
                    ("logplot", widgets.Checkbox, "Y Axis Log", self._update_fig, {}),
                ]
            )
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
        ip_display(*list(self._widgets.values())) # type: ignore

    def get_widgets(self) -> dict[str, Widget]:
        """Returns all widgets inside this TestPlotter."""
        return self._widgets

    def get_df(self, series: Optional[list[str]]=None) -> pd.DataFrame:
        """Reads the current data file into a pandas dataframe."""
        path = self._get_test_filepath()
        df = pd.read_csv(path)
        if series:
            return df.drop(df.columns.difference(series), axis=1)
        return df

    def _get_test_filepath(self) -> Path:
        parts: list[Path | str] = [self._root]
        for name in ("run", "test", "file"):
            path_part = self._widgets[name].value
            parts.append(Path(path_part).name)
        return Path(reduce(lambda a, b: Path(a) / b, parts))

    def _check_series_titles(self, change: ChangeDict, key: str) -> list[str]:
        new_series = change[key]
        if not isinstance(new_series, Sequence):
            raise TypeError(f"Expected sequence of strings, got: {new_series}")
        selected_series: list[str] = []
        for title in new_series:
            if isinstance(title, str):
                selected_series.append(title)
            else:
                raise TypeError("Expected string for series titles")
        return selected_series

    def _on_run_change(self, change: ChangeDict) -> None:
        """Updates the test folder selection when the run selection is changed."""
        test = self._widgets["test"]
        new_filename = change["new"]
        if not new_filename:
            test.options = []
        elif not isinstance(new_filename, str):
            raise TypeError(f"Expected string for run filename, got: {new_filename}")
        else:
            path = self._root / new_filename
            test.options = [d.stem for d in path.iterdir() if d.is_dir()]
        test.value = None

    def _update_fig(self, _: Optional[ChangeDict]=None) -> None:
        """Updates the plot to be a log or non-log plot."""
        if self._widgets["logplot"].value:
            self._fig.update_yaxes(type="log")
        else:
            self._fig.update_yaxes(type="-")
        self._widgets["plot"].clear_output()
        with self._widgets["plot"]:
            self._fig.show()

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
        new_filename = change["new"]
        if new_filename is None:
            series.options = []
        elif not isinstance(new_filename, str):
            raise TypeError(f"Expected string change value, got: {new_filename}")
        else:
            run = self._widgets["run"].value
            test = self._widgets["test"].value
            path = self._root / run / test / Path(new_filename).name
            with open(path, newline="", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                series.options = list(next(reader))
        series.value = []

    def _on_series_change(self, change: ChangeDict) -> None:
        """Updates the output plot when the data series selection is changed."""
        changers = {"matplotlib": self._on_series_change_matplotlib,
                    "plotly": self._on_series_change_plotly}
        changers[self._engine](change)

    def _on_series_change_plotly(self, change: ChangeDict) -> None:
        """Updates the output plot to a plotly plot when the data series selection is changed."""
        with self._widgets["err"]:
            selected_series = self._check_series_titles(change, "new")
            df = self.get_df(selected_series)
            self._fig = px.line(df, width=2400, height=800)
            self._fig.update_yaxes(exponentformat="E")
            self._update_fig()

    def _on_series_change_matplotlib(self, change: ChangeDict) -> None:
        """Updates the output plot to a matplotlib plot when the data series selection is changed.
        """
        with self._widgets["err"]:
            path = self._get_test_filepath()
            fig, ax = plt.subplots(num=1, clear=True)
            selected_series = self._check_series_titles(change, "new")
            for _, vals in self._get_data(path, selected_series).items():
                ax.plot(list(range(len(vals))), vals)
        self._widgets["plot"].clear_output()
        with self._widgets["plot"]:
            plt.show(fig)

    @staticmethod
    def _get_data(path: Path, series: list[str]) -> dict[str, list[float]]:
        """Returns the data inside the selected csv file output."""
        with open(path, newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file, quoting=csv.QUOTE_NONNUMERIC)
            data: dict[str, list[float]] = {}
            for row in reader:
                for key, value in row.items():
                    data.setdefault(key, []).append(float(value))
        return {k: v for k, v in data.items() if k in series}
