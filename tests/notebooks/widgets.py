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
from ipywidgets import Text, VBox

import scwidgets
from scwidgets import CheckCueBox, CueBox, ResetCueButton, SaveCueBox, UpdateCueBox

scwidgets.get_css_style()
# -

# Test 1:
# -------
# Check if CueBox shows cue when changed


def test_1(CueBoxClass, cued):
    text_input = Text("Text")
    cued_text_input = CueBoxClass(text_input, cued=cued)
    return cued_text_input


# Test 1.1
test_1(CueBox, True)

# Test 1.2
test_1(CueBox, False)

# Test 1.3
test_1(SaveCueBox, False)

# Test 1.4
test_1(CheckCueBox, False)

# Test 1.5
test_1(UpdateCueBox, False)

# Test 2:
# -------
# Check if successful action ResetCueButton resets cue and failing action does not

# +
text_input2 = Text("Text")


def action_success():
    return True


def action_fail():
    return False


reset_cue_button = ResetCueButton([], action_success, description="Reset Cue")
failing_reset_cue_button = ResetCueButton(
    [], action_fail, description="Failing Reset Cue"
)
cue_reset_cue_button = CueBox(text_input2, "value", reset_cue_button, cued=False)
cue_failing_reset_cue_button = CueBox(
    text_input2, "value", failing_reset_cue_button, cued=False
)
cue1_text_input2 = CueBox(text_input2, cued=False)
cue2_text_input2 = CueBox(text_input2, "value", cue1_text_input2, cued=False)
reset_cue_button.cue_boxes = [cue_reset_cue_button, cue1_text_input2]
failing_reset_cue_button.cue_boxes = [cue_failing_reset_cue_button, cue2_text_input2]
VBox([cue2_text_input2, cue_reset_cue_button, cue_failing_reset_cue_button])
