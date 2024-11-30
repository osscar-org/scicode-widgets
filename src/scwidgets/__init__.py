__version__ = "0.1.0-dev0"
__authors__ = "the scicode-widgets developer team"

from ._css_style import CssStyle, get_css_style
from .check import *  # noqa: F403
from .code import *  # noqa: F403
from .cue import *  # noqa: F403
from .exercise import *  # noqa: F403

__all__ = [  # noqa: F405
    # css_style
    "CssStyle",
    "get_css_style",
    # cue
    "CueWidget",
    "CheckCueBox",
    "CueBox",
    "SaveCueBox",
    "UpdateCueBox",
    "ResetCueButton",
    "SaveResetCueButton",
    "CheckResetCueButton",
    "UpdateResetCueButton",
    "CueOutput",
    "CueObject",
    "CueFigure",
    # code
    "CodeInput",
    "ParameterPanel",
    # check
    "Check",
    "CheckResult",
    "AssertResult",
    "CheckRegistry",
    "CheckableWidget",
    "assert_equal",
    "assert_shape",
    "assert_numpy_allclose",
    "assert_type",
    "assert_numpy_floating_sub_dtype",
    "assert_numpy_sub_dtype",
    # exercise
    "CodeExercise",
    "TextExercise",
    "ExerciseWidget",
    "ExerciseRegistry",
]
