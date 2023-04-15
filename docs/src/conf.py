# Sphinx documentation build configuration file

import os
import re
import time

import scwidgets

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.doctest', 'sphinx.ext.todo',
              'sphinx.ext.autosummary', 'sphinx.ext.extlinks',
              'sphinx.ext.intersphinx',
              'sphinx.ext.viewcode', 'sphinx.ext.inheritance_diagram']

templates_path = ['_templates']
exclude_patterns = ['_build']

project = 'scwidget'
copyright = f'BSD 3-Clause License, Copyright (c) 2023, scicode-widgets developer team'
version = scwidgets.__version__
release = version

htmlhelp_basename = 'scicode-widget-doc'
