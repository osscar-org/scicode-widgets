__version__ = "0.0.0-dev"
__authors__ = "the scicode-widgets developer team"

from ._check_registry import (
    CheckRegistry,
    CheckRegistryDummy
)
from ._save_registry import (
    SaveRegistry,
)

from ._widget_cue_box import (
    CueBox,
    SaveCueBox,
    CheckCueBox,
    UpdateCueBox
)

from ._widget_cue_button import (
    CueButton,
    SaveCueButton,
    CheckCueButton,
    UpdateCueButton
)

import os
import IPython
with open(os.path.join(os.path.dirname(__file__), 'scwidget_style.css')) as file:
    style_txt = file.read()
    style_html = IPython.display.HTML("<style>"+style_txt+"</style>")
    IPython.display.display(style_html)
