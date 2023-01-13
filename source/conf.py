# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import observer_hooks
import observer_hooks.observer_hooks
import observer_hooks.common
import observer_hooks.decorators
import observer_hooks.block_events
observer_hooks.observer_hooks.__doc__ = None
observer_hooks.common.__doc__ = None
observer_hooks.decorators.__doc__ = None
observer_hooks.block_events.__doc__ = None

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Observer Hooks'
copyright = '2023, Ryan McConnell'
author = 'Ryan McConnell'
release = observer_hooks.VERSION

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ["sphinx.ext.autodoc",
              "sphinx.ext.viewcode",
              "sphinx.ext.intersphinx",
              'sphinx.ext.autosummary',
              'm2r'
              ]

intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None)
}

templates_path = ['_templates']
exclude_patterns = []
autosummary_generate = True
autodoc_member_order = 'bysource'
autodoc_typehints = 'description'
autodoc_typehints_description_target = 'all'
autodoc_default_options = {
    "members": True,
    "special-members": False,
    "private-members": False,
    "inherited-members": False,
    "undoc-members": True
}
# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'furo'
html_static_path = ['_static']

html_context = {
    "default_mode": "dark"
}
