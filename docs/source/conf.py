# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'pancad'
copyright = '2024, spky'
author = 'spky'

import pancad.constants
import pancad.geometry
import pancad.geometry.constants
import pancad.geometry.constraints
import pancad.filetypes
import pancad.utils

from pancad.__about__ import __version__
release = __version__

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.duration',
    'sphinx.ext.doctest',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinxcontrib.programoutput',
]

templates_path = ['_templates']
exclude_patterns = []
autodoc_typehints = "description"
autodoc_member_order = "bysource"

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'classic'
html_static_path = ['_static']
html_theme_options = {
    "body_max_width": "none",
    "stickysidebar": False,
    "sidebarwidth": "375px",
    "collapsiblesidebar": True,
}
