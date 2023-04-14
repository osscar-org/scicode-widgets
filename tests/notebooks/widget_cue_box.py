# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: -all
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.15.0
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# +
from ipywidgets import Label

import scwidgets
from scwidgets import CueBox

# -

scwidgets.get_css_style()

widget1 = Label("Text")
cued_widget1 = CueBox(widget1)
cued_widget1

widget2 = Label("Text")
cued_widget2 = CueBox(widget2)
cued_widget2

widget2.value = "Changed Text"
