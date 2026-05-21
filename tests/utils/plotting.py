"""Utilities for plotting pancad tests."""
from __future__ import annotations

#from typing import TYPE_CHECKING

import csv
import tempfile
import getpass
from pathlib import Path
from functools import partial

import ipywidgets as widgets
from IPython.display import display
import matplotlib.pyplot as plt
import numpy as np

BASE_TEST_DIR = Path(tempfile.gettempdir()) / f"pytest-of-{getpass.getuser()}"

# Getter Helpers
def get_subdirs(path: Path) -> list[Path]:
    """Returns the subdirectories in a given path."""
    return [d for d in path.iterdir() if d.is_dir()]

def get_file_type(path: Path, ext: str) -> list[Path]:
    """Returns all files with the provided extension inside the path."""
    return [f for f in path.iterdir() if f.suffix == ext]

# Option Getters
def get_folder_opts(folder: Path) -> list[str]:
    """Returns the selection options for folders inside the path."""
    return [f.stem for f in folder.iterdir() if f.is_dir()]

def get_test_opts(run: str) -> list[str]:
    """Returns the selection options for the test names inside the pytest temp directory."""
    return [t.stem for t in get_subdirs(BASE_TEST_DIR / run)]

def get_file_opts(run: str, test: str, ext: str) -> list[str]:
    """Returns the file options for the run's test's outputs with a given extension.

    :param run: The name of the unittest run folder
    :param test: The name of the test data folder
    :param ext: The file extension to filter for. Ex: '.csv'
    """
    return [f.name for f in get_file_type(BASE_TEST_DIR / run / test, ext)]

def get_series_opts(run: str, test: str, filename: str) -> list[str]:
    """Returns the options for the series names at the top of a test output csv file.

    :param run: The name of the unittest run folder
    :param test: The name of the test data folder
    :param filename: The name of the csv file to read series data names from. The first row is
        assumed to have the names of the data series columns.
    """
    try:
        path = BASE_TEST_DIR / run / test / filename
    except TypeError:
        return []
    with open(path, newline="") as file:
        reader = csv.DictReader(file)
        return list(next(reader))

def get_series_data(run: str, test: str, filename: str, series: list[str]) -> dict[str, float]:
    """Returns the data inside a test csv file output.

    :param run: The name of the unittest run folder
    :param test: The name of the test data folder
    :param filename: The name of the csv file to read series data names from.
    :param series: A list of a subset of the column names in the file.
    """
    try:
        path = BASE_TEST_DIR / run / test / filename
    except TypeError:
        return {}
    with open(path, newline="") as file:
        reader = csv.DictReader(file, quoting=csv.QUOTE_NONNUMERIC)
        data = {}
        for row in reader:
            for key, value in row.items():
                data.setdefault(key, []).append(value)
    return {k: v for k, v in data.items() if k in series}

# Event Handlers
def on_run_change(change, selector):
    """Updates the test selector options when the run selection changes.

    :param change: A dictionary produced by the widget change.
    :param selector: The test selector needing an option update.
    """
    selector.options = get_test_opts(change["new"])

def on_test_change(change, run, selector):
    """Updates the csv file selector options when the test selection changes.

    :param change: A dictionary produced by the widget change.
    :param run: The widget that selects a run folder name.
    :param selector: The file selector needing an option update.
    """
    
    selector.options = get_file_opts(run.value, change["new"], ".csv")
    selector.index = 0

def on_file_change(change, run, test, selector):
    """Updates the series selector options when the file selection changes.

    :param change: A dictionary produced by the widget change.
    :param run: The widget that selects a run folder name.
    :param test: The widget that selects a test folder name.
    :param selector: The series selector needing an option update.
    """
    opts = get_series_opts(run.value, test.value, change["new"])
    selector.options = get_series_opts(run.value, test.value, change["new"])

def on_series_change(change, run, test, filename: str, plot_output):
    """Updates the displayed plot when the series selection changes.

    :param change: A dictionary produced by the widget change.
    :param run: The widget that selects a run folder name.
    :param test: The widget that selects a test folder name.
    :param plot_output: The output widget to print a plot to.
    """
    data = get_series_data(run.value, test.value, filename.value, change["new"])
    plot_output.clear_output()
    with plot_output:
        fig, ax = plt.subplots(num=1, clear=True)
        for name, vals in data.items():
            ax.plot(list(range(len(vals))), vals)
        plt.show(fig)

def get_displayed():
    """Returns display elements for a jupyter notebook to display test output series."""
    displayed = []
    runs = get_folder_opts(BASE_TEST_DIR)
    run_select = widgets.RadioButtons(options=get_folder_opts(BASE_TEST_DIR),
                                      value=runs[-1],
                                      description="Run Folder")
    test_select = widgets.Dropdown(options=get_test_opts(run_select.value),
                                   description="Test")
    file_select = widgets.RadioButtons(
        options=get_file_opts(run_select.value, test_select.value, ".csv"),
        description="File"
    )
    series_select = widgets.SelectMultiple(
        options=get_series_opts(run_select.value, test_select.value, file_select.value),
        description="Series",
        disabled=False,
        layout=widgets.Layout(width="90%", height="300px")
    )
    run_select.observe(partial(on_run_change, selector=test_select), names="value")
    test_select.observe(partial(on_test_change, run=run_select, selector=file_select),
                        names="value")
    file_select.observe(
        partial(on_file_change, run=run_select, test=test_select, selector=series_select),
        names="value")
    plot_output = widgets.Output()
    series_select.observe(
        partial(
            on_series_change,
            run=run_select,
            test=test_select,
            filename=file_select,
            plot_output=plot_output
        ),
        names="value"
    )

    return [
        run_select,
        test_select,
        file_select,
        series_select,
        plot_output,
    ]