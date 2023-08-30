import types
from copy import deepcopy
from platform import python_version
from typing import Dict, List, Optional, Union

from ipywidgets import HBox, Layout, Output, VBox
from widget_code_input.utils import CodeValidationError

from ..check import Check, CheckableWidget, CheckRegistry, ChecksLog
from ..cue import CheckCueBox, ResetCueButton, UpdateCueBox
from ._widget_code_input import CodeInput


class CodeDemo(VBox, CheckableWidget):
    """
    A widget to demonstrate code interactively in a variety of ways. It is a combination
    of the several widgets that allow to check check, run and visualize code.

    :param code:
        An or function or CodeInput that is usually the input of code for a student to
        fill in a solution

    :param check_registry:
        a check registry that is used to register checks
    """

    def __init__(
        self,
        code: Union[CodeInput, types.FunctionType],
        check_registry: Optional[CheckRegistry] = None,
        parameters: Optional[Dict[str, Check.FunInParamT]] = None,
        *args,
        **kwargs,
    ):
        if isinstance(code, types.FunctionType):
            code = CodeInput(function=code)

        CheckableWidget.__init__(self, check_registry)

        self._code = code
        self._output = Output()
        self._parameters = parameters
        self._cue_code = self._code

        if self._check_registry is None:
            self._check_button = None
            self._cue_check_button = None
        else:
            self._check_button = ResetCueButton(
                [],
                self._on_click_check_action,
                description="Check Code",
                disable_on_successful_action=False,
                button_tooltip="Check the correctness of your code",
            )
            self._cue_code = CheckCueBox(
                self._code, "function_body", self._cue_code, cued=True
            )
            self._cue_check_button = CheckCueBox(
                self._code,
                "function_body",
                self._check_button,
                cued=True,
                layout=Layout(width="98%", height="auto"),
            )
            self._check_button.cue_boxes = [self._cue_code, self._cue_check_button]

        if self._parameters is None:
            self._update_button = None
            self._cue_update_button = None
        else:
            self._update_button = ResetCueButton(
                [],
                self._on_click_update_action,
                disable_on_successful_action=False,
                description="Run Code",
                button_tooltip="Runs the code with the specified parameters",
            )
            self._cue_code = UpdateCueBox(
                self._code,
                "function_body",
                self._cue_code,
                cued=True,
                layout=Layout(width="98%", height="auto"),
            )
            self._cue_update_button = UpdateCueBox(
                self._code, "function_body", self._update_button, cued=True
            )
            self._update_button.cue_boxes = [self._cue_code, self._cue_update_button]

        if self._check_button is None and self._update_button is None:
            self._buttons_panel = HBox([])
        elif self._check_button is None:
            self._buttons_panel = HBox([self._update_button])
        elif self._update_button is None:
            self._buttons_panel = HBox([self._check_button])
        else:
            self._buttons_panel = HBox(
                [self._cue_check_button, self._cue_update_button]
            )
        VBox.__init__(
            self, [self._cue_code, self._buttons_panel, self._output], *args, **kwargs
        )

    @property
    def parameters(self):
        return deepcopy(self._parameters)

    def _on_click_update_action(self) -> bool:
        try:
            if self._parameters is None:
                raise ValueError(
                    "parameters is None but update action has been invoked, "
                    "this is an invalid state and must be a bug in the initalization "
                    "of the widget."
                )
            result = self.run_code(**self._parameters)
            self._output_result(["Output:", str(result)])
            return True
        except Exception as e:
            self._output_result([e])
            return True

    def _on_click_check_action(self) -> bool:
        try:
            result = self.check()
        except Exception as e:
            result = e
        self.handle_checks_result(result)
        return True

    def compute_output_to_check(self, *args, **kwargs) -> Check.FunOutParamsT:
        return self.run_code(*args, **kwargs)

    def handle_checks_result(self, result: Union[ChecksLog, Exception]):
        self._output_result([result])

    def _output_result(self, results: List[Union[str, ChecksLog, Exception]]):
        self._output.clear_output()
        with self._output:
            for result in results:
                if isinstance(result, Exception):
                    raise result
                elif isinstance(result, ChecksLog):
                    if result.successful:
                        print("All checks were successful.")
                    else:
                        print("Some checks failed:")
                        print(result.message())
                else:
                    print(result)

    def run_code(self, *args, **kwargs) -> Check.FunOutParamsT:
        try:
            return self._code.run(*args, **kwargs)
        except CodeValidationError as e:
            raise e
        except Exception as e:
            # we give the student the additional information that this is most likely
            # not because of his code
            if python_version() >= "3.11":
                e.add_note("This might might be not related to your code input.")
            raise e
