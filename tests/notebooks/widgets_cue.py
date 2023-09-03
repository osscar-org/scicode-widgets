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
from scwidgets.cue import CheckCueBox, CueBox, ResetCueButton, SaveCueBox, UpdateCueBox

scwidgets.get_css_style()
# -

# Test 1:
# -------
# Check if CueBox shows cue when changed


def create_cue_box(CueBoxClass, cued):
    text_input = Text("Text")
    cued_text_input = CueBoxClass(text_input, cued=cued)
    return cued_text_input


# Test 1.1
create_cue_box(CueBox, True)

# Test 1.2
create_cue_box(CueBox, False)

# Test 1.3
create_cue_box(SaveCueBox, False)

# Test 1.4
create_cue_box(CheckCueBox, False)

# Test 1.5
create_cue_box(UpdateCueBox, False)

# Test 2:
# -------
# Check if successful action ResetCueButton resets cue and failing action does not


def create_reset_cue_button(
    disable_on_successful_action: bool, failing_action: bool, error_in_action: bool
):
    text_input = Text("Text")

    unused_text_input = Text("Unused")

    def action():
        if error_in_action:
            raise ValueError("Error")
        return not (failing_action)

    reset_cue_button = ResetCueButton(
        [],
        action,
        description="Reset Cue",
        disable_on_successful_action=disable_on_successful_action,
    )
    cue_text_input = CueBox(text_input, "value", cued=False)
    cue_reset_cue_button = CueBox(text_input, "value", reset_cue_button, cued=False)
    cue_unused_text_input = CueBox(unused_text_input, "value", cued=False)

    # by setting it to a different widget we test if unobserve behavior works
    reset_cue_button.cue_widgets = [cue_unused_text_input]
    reset_cue_button.cue_widgets = [cue_text_input, cue_reset_cue_button]
    return VBox([cue_text_input, cue_unused_text_input, cue_reset_cue_button])


# Test 2.1
create_reset_cue_button(
    disable_on_successful_action=True, failing_action=False, error_in_action=False
)

# Test 2.2
create_reset_cue_button(
    disable_on_successful_action=True, failing_action=True, error_in_action=False
)

# Test 2.3
create_reset_cue_button(
    disable_on_successful_action=False, failing_action=False, error_in_action=False
)

# Test 2.4
create_reset_cue_button(
    disable_on_successful_action=False, failing_action=True, error_in_action=False
)

# Test 2.5
create_reset_cue_button(
    disable_on_successful_action=True, failing_action=False, error_in_action=True
)
