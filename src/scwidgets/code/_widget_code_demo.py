import types
from platform import python_version
from typing import Dict, List, Optional, Union

from ipywidgets import HBox, Layout, Output, VBox, Widget
from widget_code_input.utils import CodeValidationError

from ..check import Check, CheckableWidget, CheckRegistry, ChecksLog
from ..cue import CheckCueBox, ResetCueButton, UpdateCueBox
from ._widget_code_input import CodeInput
from ._widget_parameter_panel import ParameterPanel


class CodeDemo(VBox, CheckableWidget):
    """
    A widget to demonstrate code interactively in a variety of ways. It is a combination
    of the several widgets that allow to check check, run and visualize code.

    :param code:
        An or function or CodeInput that is usually the input of code for a student to
        fill in a solution

    :param check_registry:
        a check registry that is used to register checks

    :param parameters:
        Can be any input that is allowed as keyword arguments in ipywidgets.interactive
        for the parameters. _options and other widget layout parameter are controlled
        by CodeDemo.
    """

    def __init__(
        self,
        code: Union[CodeInput, types.FunctionType],
        check_registry: Optional[CheckRegistry] = None,
        parameters: Optional[Dict[str, Union[Check.FunInParamT, Widget]]] = None,
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
            self._parameter_panel = VBox([])
        else:
            compatibility_result = self._code.compatible_with_signature(
                list(self._parameters.keys())
            )
            if compatibility_result != "":
                raise ValueError(compatibility_result)

            # set up update button and cueing
            # -------------------------------
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

            # set up parameter panel
            # ----------------------
            self._parameter_panel = ParameterPanel(self._parameters)
            self._cue_parameter_panel = UpdateCueBox(
                self._parameter_panel.parameters_widget, "value", self._parameter_panel
            )
            self._cue_update_button = UpdateCueBox(
                [self._code] + self._parameter_panel.parameters_widget,
                ["function_body"]
                + ["value"] * len(self._parameter_panel.parameters_widget),
                self._update_button,
                cued=True,
            )

            self._update_button.cue_boxes = [
                self._cue_code,
                self._cue_update_button,
                self._cue_parameter_panel,
            ]

        if self._check_button is None and self._update_button is None:
            self._buttons_panel = HBox([])
        elif self._check_button is None:
            self._buttons_panel = HBox([self._cue_update_button])
        elif self._update_button is None:
            self._buttons_panel = HBox([self._cue_check_button])
        else:
            self._buttons_panel = HBox(
                [self._cue_check_button, self._cue_update_button]
            )

        VBox.__init__(
            self,
            [
                self._cue_code,
                self._cue_parameter_panel,
                self._buttons_panel,
                self._output,
            ],
            *args,
            **kwargs,
        )

    @property
    def panel_parameters(self) -> Dict[str, Check.FunInParamT]:
        return self._parameter_panel.parameters

    def _on_click_update_action(self) -> bool:
        self._output.clear_output()
        try:
            self._on_action_run_code(**self.panel_parameters)
            return True
        except Exception as e:
            self._output_results([e])
            return True

    def _on_click_check_action(self) -> bool:
        self._output.clear_output()
        try:
            self.check()
        except Exception as e:
            with self._output:
                if python_version() >= "3.11":
                    e.add_note("This is most likely not related to your code input.")
                raise e
        return True

    def compute_output_to_check(self, *args, **kwargs) -> Check.FunOutParamsT:
        return self.run_code(*args, **kwargs)

    def handle_checks_result(self, result: Union[ChecksLog, Exception]):
        self._output_results([result])

    def _output_results(self, results: List[Union[str, ChecksLog, Exception]]):
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

    def _on_action_run_code(self, *args, **kwargs):
        # runs code and displays output
        with self._output:
            try:
                result = self._code.run(*args, **kwargs)
                print("Output:")
                print(result)
            except CodeValidationError as e:
                raise e
            except Exception as e:
                # we give the student the additional information that this is most
                # likely not because of his code
                if python_version() >= "3.11":
                    e.add_note("This is most likely not related to your code input.")
                raise e

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
