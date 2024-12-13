# Sphinx documentation build configuration file

import sphinx_material

import scwidgets

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.doctest",
    "sphinx.ext.todo",
    "sphinx.ext.autosummary",
    "sphinx.ext.extlinks",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "sphinx.ext.mathjax",
    "nbsphinx",
]


html_theme = "sphinx_material"
html_theme_path = sphinx_material.html_theme_path()
html_context = sphinx_material.get_html_context()
html_theme_options = {
    # Set the name of the project to appear in the navigation.
    "nav_title": "scicode-widgets",
    # Set the repo location to get a badge with stats
    "repo_url": "https://github.com/osscar-org/scicode-widgets/",
    "repo_name": "scicode-widgets",
    # Visible levels of the global TOC; -1 means unlimited
    "globaltoc_depth": 1,
    # If False, expand all TOC entries
    "globaltoc_collapse": False,
    "color_primary": "orange",
    "color_accent": "cyan",
}

html_sidebars = {
    "**": ["logo-text.html", "globaltoc.html", "localtoc.html", "searchbox.html"]
}

# htmlhelp_basename = ""
html_title = "scicode-widgets documentation"
html_short_title = "Documentation"

templates_path = ["_templates"]
exclude_patterns = ["_build"]

project = "scwidget"
copyright = "BSD 3-Clause License, Copyright (c) 2024, scicode-widgets developer team"
version = scwidgets.__version__
release = version
