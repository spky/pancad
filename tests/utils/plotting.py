"""Utilities for plotting pancad tests."""
from __future__ import annotations

from functools import cached_property, reduce
from collections.abc import Sequence
import csv
import tempfile
import getpass
from pathlib import Path
from typing import TYPE_CHECKING, Literal, get_args, TypedDict

import ipywidgets as widgets # type: ignore
import plotly.express as px # type: ignore
from IPython.display import display as ip_display
from traitlets import TraitError
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

if TYPE_CHECKING:
    from os import PathLike
    from collections.abc import Callable
    from typing import Optional, Type, NotRequired

    from ipywidgets.widgets.widget import Widget # type: ignore

    ChangeDict = dict[str, str | list[str] | Widget | None]

PlotEngine = Literal["matplotlib", "plotly"]

class SelectorSettings(TypedDict):
    """A dictionary used to specify a input selector's settings in Jupyter ipywidgets.

    :param key: The identifier for the selector in a larger context.
    :param widget: The widget to display.
    :param description: The text appearing right above the widget.
    :param on_change: A function to call when the widget's value changes.
    :param layout_options: The dictionary of widget size and format settings.
    """
    key: str
    widget: Type[Widget]
    description: str
    on_change: NotRequired[Callable[[ChangeDict], None]]
    layout_options: NotRequired[dict[str, str]]

class TestSelector:
    """A class for creating test selection dropdowns."""

    def __init__(self, root: Optional[Path]=None) -> None:
        if root is None:
            root = Path(tempfile.gettempdir()) / f"pytest-of-{getpass.getuser()}"
        self.root: Path = root
        self.widgets: dict[str, Widget] = {}
        selectors: list[SelectorSettings] = [
            {
                "key": "run",
                "widget": widgets.RadioButtons,
                "description": "Run Folder",
                "on_change": self._on_run_change
            },
            {
                "key": "test",
                "widget": widgets.Dropdown,
                "description": "Test Folder",
                "on_change": self._on_test_change,
                "layout_options": {"width": "90%"}
            },
            {
                "key": "file",
                "widget": widgets.RadioButtons,
                "description": "CSV File",
                "layout_options": {"width": "100%"}
            },
        ]
        for select in selectors:
            self.widgets[select["key"]] = self.new_selector(
                select["widget"], select["description"], select.get("on_change"),
                select.get("layout_options", {})
            )
        # initialize test run options
        self.widgets["run"].options = [d.stem for d in self.root.iterdir() if d.is_dir()]
        try:
            self.widgets["run"].index = len(self.widgets["run"].options)
        except TraitError:
            self.widgets["run"].index = None

    def display(self) -> None:
        """Displays data in TestPlotter's default order."""
        ip_display(*list(self.widgets.values())) # type: ignore

    def get_path(self) -> Optional[Path]:
        """Returns the currently selected test file path or None if no file is selected."""
        parts: list[Path | str] = [self.root]
        for name in ("run", "test", "file"):
            path_part = self.widgets[name].value
            if not path_part:
                raise ValueError("No file selected")
            parts.append(Path(path_part).name)
        return Path(reduce(lambda a, b: Path(a) / b, parts))

    @staticmethod
    def new_selector(widget: Type[Widget], description: str,
                     on_change: Optional[Callable[[ChangeDict], None]]=None,
                     layout_options: Optional[dict[str, str]]=None) -> Widget:
        """Returns a new selection widget."""
        if not layout_options:
            layout_options = {}
        layout = widgets.Layout(**layout_options)
        new_widget = widget(description=description, layout=layout)
        if on_change:
            new_widget.observe(on_change, names="value")
        return new_widget

    def _on_run_change(self, change: ChangeDict) -> None:
        """Updates the test folder selection when the run selection is changed."""
        test = self.widgets["test"]
        new_filename = change["new"]
        if not new_filename:
            test.options = []
        elif not isinstance(new_filename, str):
            raise TypeError(f"Expected string for run filename, got: {new_filename}")
        else:
            path = self.root / new_filename
            test.options = [d.stem for d in path.iterdir() if d.is_dir()]
        test.value = None

    def _on_test_change(self, change: ChangeDict) -> None:
        """Updates the csv file selection when the test folder selection is changed."""
        file = self.widgets["file"]
        if change["new"] is None:
            file.options = []
        else:
            run = self.widgets["run"].value
            path = self.root / run / change["new"]
            file.options = [str(f.relative_to(self.root))
                            for f in path.iterdir() if f.suffix == ".csv"]
        file.value = None


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
        self._test_selector = TestSelector(root)
        self._widgets: dict[str, Widget] = {}
        self._widgets.update(self._test_selector.widgets)
        self._widgets["file"].observe(self._on_file_change, names="value")
        self._engine = engine
        self._root: Path = root
        selectors: list[SelectorSettings] = []
        selectors.append(
            {
                "key": "series",
                "widget": widgets.SelectMultiple,
                "description": "Series",
                "on_change": self._on_series_change,
                "layout_options": {"width": "90%", "height": "300px"},
            },
        )
        if self._engine == "plotly":
            self._fig = px.line()
            selectors.append(
                {
                    "key": "logplot",
                    "widget": widgets.Checkbox,
                    "description": "Y Axis Log",
                    "on_change": self._update_fig,
                }
            )
        for select in selectors:
            self._widgets[select["key"]] = TestSelector.new_selector(
                select["widget"], select["description"], select["on_change"],
                select.get("layout_options", {})
            )
        self._widgets.update({key: widgets.Output() for key in ("plot", "err")})

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

    def _update_fig(self, _: Optional[ChangeDict]=None) -> None:
        """Updates the plot to be a log or non-log plot."""
        if self._widgets["logplot"].value:
            self._fig.update_yaxes(type="log")
        else:
            self._fig.update_yaxes(type="-")
        self._widgets["plot"].clear_output()
        with self._widgets["plot"]:
            self._fig.show()

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
        with self._widgets["err"]:
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

class RegressionCompare:
    """A class for comparing a test run to its expected data.

    :param path: The filepath of either the obtained or original result file from a test.
    :param suffix: The file extension of the output files being compared.
    """

    def __init__(self, path: PathLike[str], suffix: str=".csv") -> None:
        file = Path(path)
        if ".obtained" in file.suffixes:
            self.obtained = file
            self.original = Path(str(file).rstrip("".join(file.suffixes))).with_suffix(suffix)
        else:
            self.original = file
            self.obtained = file.with_suffix(".obtained" + suffix)

    @cached_property
    def obtained_df(self) -> pd.DataFrame:
        """The dataframe of the test's generated data."""
        return pd.read_csv(self.obtained)

    @cached_property
    def original_df(self) -> pd.DataFrame:
        """The dataframe of the expected original data."""
        return pd.read_csv(self.original)

    def get_comparables(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Returns the original and the obtained dataframes with a guaranteed matching number of
        rows to enable comparisons. Adds the missing number of rows to the shorter of the two
        dataframes.
        """
        original_len, obtained_len = map(len, (self.original_df, self.obtained_df))
        if original_len == obtained_len:
            return self.original_df, self.obtained_df

        # Determine which dataframe needs to be lengthened
        if original_len < obtained_len:
            short_df = self.original_df.copy()
            other_df = self.obtained_df.copy()
        else:
            other_df = self.original_df.copy()
            short_df = self.obtained_df.copy()
        df_dict = short_df.to_dict(orient="list")

        # Remove to_dict added index column
        index_name = short_df.index.name
        if not index_name:
            index_name = "Unnamed: 0"
        del df_dict[index_name]
        other_df.drop(index_name, axis=1, inplace=True)

        row_patch = [np.nan] * (max(original_len, obtained_len) - min(original_len, obtained_len))
        for key, values in df_dict.items():
            df_dict[key] = values + row_patch

        if original_len < obtained_len:
            return pd.DataFrame.from_dict(df_dict), other_df
        return other_df, pd.DataFrame.from_dict(df_dict)
