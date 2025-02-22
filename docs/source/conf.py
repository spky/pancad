# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'PanCAD'
copyright = '2024, spky'
author = 'spky'
release = '0.0.0'
print("running!")

import sys
from pathlib import Path

sys.path.insert(0, str(Path('..','..', 'src').resolve()))

import svg.element_utils
import svg.elements
import svg.enum_color_keywords
import svg.file
import svg.generators
import svg.parsers
import svg.readers
import svg.validators
import svg.writers

import freecad.object_wrappers
import freecad.sketch_readers

import translators.freecad_sketcher_to_svg
import translators.freecad_svg_file
import translators.svg_to_freecad_sketcher

import trigonometry
import file_handlers

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.duration',
    'sphinx.ext.doctest',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
]

templates_path = ['_templates']
exclude_patterns = []
autodoc_typehints = "description"


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']
