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
from ipywidgets import Text

import scwidgets
from scwidgets import CueBox

scwidgets.get_css_style()
# -

# Test 1:
# -------
# Check if CueBox shows cue when changed

text_input1 = Text("Text")
cued_text_input1 = CueBox(text_input1, cued=False)
cued_text_input1
