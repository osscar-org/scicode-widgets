import types
from copy import deepcopy
from platform import python_version
from typing import Dict, List, Optional, Union

from ipywidgets import HBox, Layout, Output, VBox, Widget
from widget_code_input.utils import CodeValidationError

from ..check import Check, CheckableWidget, CheckRegistry, ChecksLog
from ..cue import CheckCueBox, CheckResetCueButton, UpdateCueBox, UpdateResetCueButton
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

    :param update_mode:
        determines how the parameters are refreshed on change

    """

    def __init__(
        self,
        code: Union[CodeInput, types.FunctionType],
        check_registry: Optional[CheckRegistry] = None,
        parameters: Optional[Dict[str, Union[Check.FunInParamT, Widget]]] = None,
        update_mode: str = "release",
        *args,
        **kwargs,
    ):
        allowed_update_modes = ["manual", "continuous", "release"]
        if update_mode not in allowed_update_modes:
            raise ValueError(
                f"Got update mode {update_mode!r} but only "
                f"{allowed_update_modes} are allowed."
            )
        self._update_mode = update_mode

        if isinstance(code, types.FunctionType):
            code = CodeInput(function=code)

        CheckableWidget.__init__(self, check_registry)

        self._code = code
        self._output = Output()
        self._parameters = deepcopy(parameters)
        self._cue_code = self._code

        if self._check_registry is None:
            self._check_button = None
        else:
            self._cue_code = CheckCueBox(
                self._code, "function_body", self._cue_code, cued=True
            )
            self._check_button = CheckResetCueButton(
                [self._cue_code],
                self._on_click_check_action,
                disable_on_successful_action=kwargs.pop(
                    "disable_check_button_on_successful_action", False
                ),
                disable_during_action=kwargs.pop(
                    "disable_check_button_during_action", True
                ),
                description="Check Code",
                button_tooltip="Check the correctness of your code",
            )

        if self._parameters is None:
            self._update_button = None
            self._parameter_panel = VBox([])
        else:
            compatibility_result = self._code.compatible_with_signature(
                list(self._parameters.keys())
            )
            if compatibility_result != "":
                raise ValueError(compatibility_result)

            # set up update button and cueing
            # -------------------------------
            self._cue_code = UpdateCueBox(
                self._code,
                "function_body",
                self._cue_code,
                cued=True,
                layout=Layout(width="98%", height="auto"),
            )

            # set up parameter panel
            # ----------------------

            self._parameter_panel = ParameterPanel(**self._parameters)
            if self._update_mode == "continuous":
                self._parameter_panel.set_parameters_widget_attr(
                    "continuous_update", True
                )
            elif self._update_mode == "release":
                self._parameter_panel.set_parameters_widget_attr(
                    "continuous_update", False
                )

            if self._update_mode in ["continuous", "release"]:
                self._parameter_panel.observe_parameters(
                    self._on_trait_parameters_changed, "value"
                )
                # the button only cues on cue_code change
                widgets_to_observe = [self._code]
                traits_to_observe = ["function_body"]
                # assume when continuous that the function is fast
                # and that disabling causes flicker
                disable_during_action = False

                self._cue_parameter_panel = UpdateCueBox(
                    [],
                    [],
                    self._parameter_panel,
                )
            else:
                widgets_to_observe = None
                traits_to_observe = None
                disable_during_action = True

                self._cue_parameter_panel = UpdateCueBox(
                    self._parameter_panel.parameters_widget,
                    self._parameter_panel.parameters_trait,
                    self._parameter_panel,
                )

            self._update_button = UpdateResetCueButton(
                [self._cue_code, self._cue_parameter_panel],  # type: ignore[arg-type]
                self._on_click_update_action,
                disable_on_successful_action=kwargs.pop(
                    "disable_update_button_on_successful_action", False
                ),
                disable_during_action=kwargs.pop(
                    "disable_update_button_during_action", disable_during_action
                ),
                widgets_to_observe=widgets_to_observe,
                traits_to_observe=traits_to_observe,
                description="Run Code",
                button_tooltip="Runs the code with the specified parameters",
            )

        if self._check_button is None and self._update_button is None:
            self._buttons_panel = HBox([])
        elif self._check_button is None:
            self._buttons_panel = HBox([self._update_button])
        elif self._update_button is None:
            self._buttons_panel = HBox([self._check_button])
        else:
            self._buttons_panel = HBox([self._check_button, self._update_button])

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

    def _on_trait_parameters_changed(self, change: dict):
        if self._update_button is None:
            self._output.clear_output(wait=True)
            error = ValueError(
                "Invalid state: _on_trait_parameters_changed was "
                "invoked but no update button was defined"
            )
            with self._output:
                raise error
            raise error
        self._update_button.click()

    def _on_click_check_action(self) -> bool:
        self._output.clear_output(wait=True)
        try:
            self.check()
        except Exception as e:
            with self._output:
                if python_version() >= "3.11":
                    e.add_note("This is most likely not related to your code input.")
                raise e
        return True

    def check(self) -> Union[ChecksLog, Exception]:
        self._output.clear_output(wait=True)
        return CheckableWidget.check(self)

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
                        print("Check was successful.")
                    else:
                        print("Check failed:")
                        print(result.message())
                else:
                    print(result)

    def _on_click_update_action(self) -> bool:
        self._output.clear_output(wait=True)
        raised_error = False
        # runs code and displays output
        with self._output:
            try:
                result = self._code.run(**self.panel_parameters)
                print("Output:")
                print(result)
            except CodeValidationError as e:
                raised_error = True
                raise e
            except Exception as e:
                raised_error = True
                # we give the student the additional information that this is most
                # likely not because of his code
                if python_version() >= "3.11":
                    e.add_note("This is most likely not related to your code input.")
                raise e
        return not (raised_error)

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
