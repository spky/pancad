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

import sys
from pathlib import Path

sys.path.insert(0, str(Path('..','..', 'src').resolve()))

import PanCAD.graphics.svg.element_utils
import PanCAD.graphics.svg.elements
import PanCAD.graphics.svg.enum_color_keywords
import PanCAD.graphics.svg.file
import PanCAD.graphics.svg.generators
import PanCAD.graphics.svg.parsers
import PanCAD.graphics.svg.validators

import PanCAD.cad.freecad.object_wrappers
import PanCAD.cad.freecad.sketch_readers

import PanCAD.translators.freecad_sketcher_to_svg
import PanCAD.translators.freecad_svg_file
import PanCAD.translators.svg_to_freecad_sketcher

import PanCAD.utils.trigonometry
import PanCAD.utils.file_handlers
import PanCAD.utils.config
import PanCAD.utils.initialize

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
