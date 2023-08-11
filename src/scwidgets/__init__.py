__version__ = "0.0.0-dev"
__authors__ = "the scicode-widgets developer team"

import os

from IPython.core.display import HTML

from ._widget_cue_box import CheckCueBox, CueBox, SaveCueBox, UpdateCueBox
from ._widget_reset_cue_button import ResetCueButton

__all__ = ["CheckCueBox", "CueBox", "SaveCueBox", "UpdateCueBox", "ResetCueButton"]


def get_css_style() -> HTML:
    """
    When reimporting scwidgets the objects displayed by the package are destroyed,
    because the cell output is refreshed.
    Since the module is loaded from cache when reimported one cannot rexecute the
    code on reimport, so we rely on the user to do it on a separate scell to keep the
    displayed html with the css style it avice in the notebook
    """
    with open(os.path.join(os.path.dirname(__file__), "css/widgets.css")) as file:
        style_txt = file.read()

    return HTML(
        "HTML with scicode-widget css style sheet. \
                Please keep this cell output alive. \
                <style>"
        + style_txt
        + "</style>"
    )
