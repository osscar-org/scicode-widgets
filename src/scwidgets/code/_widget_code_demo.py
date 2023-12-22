# postpones evaluation of annotations
# see https://stackoverflow.com/a/33533514
from __future__ import annotations

import types
from platform import python_version
from typing import Any, Callable, Dict, List, Optional, Union

from ipywidgets import Box, HBox, Layout, VBox, Widget
from widget_code_input.utils import CodeValidationError

from .._utils import Printer
from ..answer import AnswerRegistry, AnswerWidget
from ..check import Check, CheckableWidget, CheckRegistry, ChecksLog
from ..cue import (
    CheckCueBox,
    CheckResetCueButton,
    CueOutput,
    SaveCueBox,
    SaveResetCueButton,
    UpdateCueBox,
    UpdateResetCueButton,
)
from ._widget_code_input import CodeInput
from ._widget_parameter_panel import ParameterPanel


class CodeDemo(VBox, CheckableWidget, AnswerWidget):
    """
    A widget to demonstrate code interactively in a variety of ways. It is a combination
    of the several widgets that allow to check check, run and visualize code.

    :param code:
        A function or CodeInput that is the input of code

    :param check_registry:
        a check registry that is used to register checks

    :param parameters:
        Input parameters for the :py:class:`ParameterPanel` class or an initialized
        :py:class:`ParameterPanel` object. Specifies the arguments in the parameter
        panel.

    :param update_mode:
        Determines how the parameters are refreshed on changes of the code input
        or parameters

    :param cue_outputs:
        List of CueOuputs that are drawn an refreshed

    :param update_func:
        A function that is run during the update process. The function takes as argument
        the CodeDemo, so it can update all cue_ouputs

    """

    def __init__(
        self,
        code: Union[None, CodeInput, types.FunctionType] = None,
        check_registry: Optional[CheckRegistry] = None,
        answer_registry: Optional[AnswerRegistry] = None,
        answer_key: Optional[str] = None,
        parameters: Optional[
            Union[Dict[str, Union[Check.FunInParamT, Widget]], ParameterPanel]
        ] = None,
        update_mode: str = "release",
        cue_outputs: Union[None, CueOutput, List[CueOutput]] = None,
        update_func: Optional[
            Callable[[CodeDemo], Union[Any, Check.FunOutParamsT]]
        ] = None,
        *args,
        **kwargs,
    ):
        allowed_update_modes = ["manual", "continuous", "release"]
        if update_mode not in allowed_update_modes:
            raise TypeError(
                f"Got update mode {update_mode!r} but only "
                f"{allowed_update_modes} are allowed."
            )
        self._update_mode = update_mode

        self._update_func = update_func

        # verify if input argument `parameter` is valid
        if parameters is not None:
            allowed_parameter_types = [dict, ParameterPanel]
            parameter_type_allowed = False
            for allowed_parameter_type in allowed_parameter_types:
                if isinstance(parameters, allowed_parameter_type):
                    parameter_type_allowed = True
            if not (parameter_type_allowed):
                raise TypeError(
                    f"Got parameter {type(parameters)!r} but only "
                    f"{allowed_parameter_types} are allowed."
                )

        # verify if input argument `parameter` is valid
        if isinstance(code, types.FunctionType):
            code = CodeInput(function=code)

        # check compability between code and parameters, can only be checked if
        # update_func is not used because we cannot know how the code input is used
        if update_func is None and code is not None and parameters is not None:
            if isinstance(parameters, dict):
                compatibility_result = code.compatible_with_signature(
                    list(parameters.keys())
                )
            elif isinstance(parameters, ParameterPanel):
                compatibility_result = code.compatible_with_signature(
                    list(parameters.parameters.keys())
                )
            if compatibility_result != "":
                raise ValueError(
                    "Code and parameters do no match:  " + compatibility_result
                )

        if cue_outputs is None:
            cue_outputs = []
        elif not (isinstance(cue_outputs, list)):
            cue_outputs = [cue_outputs]

        CheckableWidget.__init__(self, check_registry)
        AnswerWidget.__init__(self, answer_registry, answer_key)

        self._code = code
        self._output = CueOutput()

        self._parameter_panel: Union[ParameterPanel, None]
        self._parameters: Union[dict, None]
        if isinstance(parameters, dict):
            self._parameter_panel = ParameterPanel(**parameters)
            self._parameters = self._parameter_panel.parameters
        elif isinstance(parameters, ParameterPanel):
            self._parameter_panel = parameters
            self._parameters = self._parameter_panel.parameters
        else:
            self._parameter_panel = None
            self._parameters = None

        self._cue_code = self._code
        self._cue_outputs = cue_outputs

        if self._check_registry is None or self._code is None:
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

        if self._parameter_panel is None:
            self._update_button = None
            self._self._cue_parameter_panel = None
        else:
            # set up update button and cueing
            # -------------------------------

            if self._code is not None:
                self._cue_code = UpdateCueBox(
                    self._code,
                    "function_body",
                    self._cue_code,
                    cued=True,
                    layout=Layout(width="98%", height="auto"),
                )

            # set up parameter panel
            # ----------------------

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

                if self._code is not None:
                    # the button only cues on cue_code change
                    widgets_to_observe = [self._code]
                    traits_to_observe = ["function_body"]
                else:
                    widgets_to_observe = None
                    traits_to_observe = None
                # assume when continuous that the function is fast
                # and that disabling causes flicker
                disable_during_action = False
                if self._code is not None:
                    for cue_output in self._cue_outputs:
                        # TODO this has to be made public
                        cue_output._widgets_to_observe = [self._code]
                        cue_output._traits_to_observe = ["function_body"]
                        cue_output.observe_widgets()

                    # TODO set this
                    self._output._widgets_to_observe = [self._code]
                    self._output._traits_to_observe = ["function_body"]
                    self._output.observe_widgets()

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

                for cue_output in self._cue_outputs:
                    if self._code is not None:
                        # TODO this has to be made public
                        cue_output._widgets_to_observe = [
                            self._code
                        ] + self._parameter_panel.parameters_widget
                        cue_output._traits_to_observe = [
                            "function_body"
                        ] + self._parameter_panel.parameters_trait
                        cue_output.observe_widgets()
                    else:
                        # TODO this has to be made public
                        cue_output._widgets_to_observe = (
                            self._parameter_panel.parameters_widget
                        )
                        cue_output._traits_to_observe = (
                            self._parameter_panel.parameters_trait
                        )
                        cue_output.observe_widgets()

            reset_update_cue_widgets = []
            if self._code is not None:
                reset_update_cue_widgets.append(self._cue_code)
            reset_update_cue_widgets.append(self._cue_parameter_panel)
            reset_update_cue_widgets.extend(self._cue_outputs)

            if self._code is not None:
                description = "Run Code"
                button_tooltip = (
                    "Runs the code and updates outputs with the specified parameters"
                )
            else:
                description = "Update"
                button_tooltip = "Updates outputs with the specified parameters"

            self._update_button = UpdateResetCueButton(
                reset_update_cue_widgets,  # type: ignore[arg-type]
                self._on_click_update_action,
                disable_on_successful_action=kwargs.pop(
                    "disable_update_button_on_successful_action", False
                ),
                disable_during_action=kwargs.pop(
                    "disable_update_button_during_action", disable_during_action
                ),
                widgets_to_observe=widgets_to_observe,
                traits_to_observe=traits_to_observe,
                description=description,
                button_tooltip=button_tooltip,
            )

        if self._answer_registry is None or (
            self._code is None and self._parameter_panel is None
        ):
            self._save_button = None
            self._load_button = None
            self._save_cue_box = None
        else:
            save_widgets_to_observe = [self._code]
            save_traits_to_observe = ["function_body"]
            if self._parameter_panel is not None:
                save_widgets_to_observe.extend(self._parameter_panel.parameters_widget)
                save_traits_to_observe.extend(self._parameter_panel.parameters_trait)
            self._cue_code = SaveCueBox(
                save_widgets_to_observe,
                save_traits_to_observe,
                self._cue_code,
                cued=True,
            )

            self._save_cue_box = self._cue_code
            self._save_button = SaveResetCueButton(
                self._cue_code,
                self._on_click_save_action,
                cued=True,
                disable_on_successful_action=kwargs.pop(
                    "disable_save_button_on_successful_action", False
                ),
                disable_during_action=kwargs.pop(
                    "disable_save_button_during_action", True
                ),
                description="Save code",
                button_tooltip="Loads your code and parameters from the loaded file",
            )
            self._load_button = SaveResetCueButton(
                self._cue_code,
                self._on_click_load_action,
                cued=True,
                disable_on_successful_action=kwargs.pop(
                    "disable_load_button_on_successful_action", False
                ),
                disable_during_action=kwargs.pop(
                    "disable_load_button_during_action", True
                ),
                description="Load code",
                button_tooltip="Saves your code and parameters to the loaded file",
            )

            # click on load button resets cue of save buton and vise-versa
            self._save_button.set_cue_widgets(
                [
                    widget
                    for widget in [
                        self._cue_code,
                        self._cue_parameter_panel,
                        self._load_button,
                    ]
                    if widget is not None
                ]
            )
            self._load_button.set_cue_widgets(
                [
                    widget
                    for widget in [
                        self._cue_code,
                        self._cue_parameter_panel,
                        self._save_button,
                    ]
                    if widget is not None
                ]
            )

        demo_children = []
        if self._code is not None:
            demo_children.append(self._cue_code)
        if self._parameters is not None:
            demo_children.append(self._cue_parameter_panel)

        buttons = []
        if self._check_button is None and self._update_button is None:
            self._code_buttons = HBox([])
        elif self._check_button is None:
            self._code_buttons = HBox([self._update_button])
        elif self._update_button is None:
            self._code_buttons = HBox([self._check_button])
        else:
            self._code_buttons = HBox([self._check_button, self._update_button])
        buttons.append(self._code_buttons)

        if self._save_button is not None and self._load_button is not None:
            self._answer_buttons = HBox(
                [self._save_button, self._load_button],
                layout=Layout(justify_content="flex-end"),
            )
        else:
            self._answer_buttons = Box([])
        buttons.append(self._answer_buttons)

        self._buttons_panel = HBox(
            buttons, layout=Layout(justify_content="space-between")
        )

        demo_children.extend(
            [
                self._buttons_panel,
                self._output,
            ]
        )
        demo_children.extend(self._cue_outputs)

        VBox.__init__(
            self,
            demo_children,
            *args,
            **kwargs,
        )

    @property
    def answer(self) -> dict:
        return {
            "code": None if self._code is None else self._code.function_body,
            "parameter_panel": None
            if self._parameter_panel is None
            else self._parameter_panel.parameters,
        }

    @answer.setter
    def answer(self, answer: dict):
        if self._save_cue_box is not None:
            self._save_cue_box.unobserve_widgets()
        if self._save_button is not None:
            self._save_button.unobserve_widgets()
        if self._load_button is not None:
            self._load_button.unobserve_widgets()

        if answer["code"] is not None and self._code is not None:
            self._code.function_body = answer["code"]
        if answer["parameter_panel"] is not None and self._parameter_panel is not None:
            self._parameter_panel.parameters = answer["parameter_panel"]

        if self._save_cue_box is not None:
            self._save_cue_box.observe_widgets()
        if self._save_button is not None:
            self._save_button.observe_widgets()
        if self._load_button is not None:
            self._load_button.observe_widgets()

    @property
    def panel_parameters(self) -> Dict[str, Check.FunInParamT]:
        if self._parameter_panel is not None:
            parameter_panel = self._parameter_panel
            return parameter_panel.parameters
        return {}

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
        raised_error = False
        with self._output:
            try:
                self.check()
            except Exception as e:
                raised_error = True
                if python_version() >= "3.11":
                    e.add_note("This error is most likely not related to your code.")
                raise e
        return not (raised_error)

    def _on_click_save_action(self) -> bool:
        self._output.clear_output(wait=True)
        raised_error = False
        with self._output:
            try:
                result = self.save()
                if isinstance(result, str):
                    Printer.print_success_message(result)
                elif isinstance(result, Exception):
                    raise result
                else:
                    print(result)
            except Exception as e:
                raised_error = True
                Printer.print_error_message("Error raised while saving file:")
                raise e
        return not (raised_error)

    def _on_click_load_action(self) -> bool:
        self._output.clear_output(wait=True)
        raised_error = False
        with self._output:
            try:
                result = self.load()
                if isinstance(result, str):
                    Printer.print_success_message(result)
                elif isinstance(result, Exception):
                    raise result
                else:
                    print(result)
            except Exception as e:
                raised_error = True
                Printer.print_error_message("Error raised while loading file:")
                raise e
        return not (raised_error)

    def check(self) -> Union[ChecksLog, Exception]:
        self._output.clear_output(wait=True)
        return CheckableWidget.check(self)

    def compute_output_to_check(self, *args, **kwargs) -> Check.FunOutParamsT:
        return self.run_code(*args, **kwargs)

    def handle_checks_result(self, result: Union[ChecksLog, Exception]):
        self._output.clear_output(wait=True)
        with self._output:
            if isinstance(result, Exception):
                raise result
            elif isinstance(result, ChecksLog):
                if result.successful:
                    Printer.print_success_message("Check was successful.")
                else:
                    Printer.print_error_message("Check failed:")
                    print(result.message())
            else:
                print(result)

    def handle_save_result(self, result: Union[str, Exception]):
        self._output.clear_output(wait=True)
        with self._output:
            if isinstance(result, Exception):
                raise result
            else:
                if self._load_button is not None:
                    self._load_button.cued = False
                if self._save_button is not None:
                    self._save_button.cued = False
                if self._save_cue_box is not None:
                    self._save_cue_box.cued = False
                Printer.print_success_message(result)

    def handle_load_result(self, result: Union[str, Exception]):
        self._output.clear_output(wait=True)
        with self._output:
            if isinstance(result, Exception):
                raise result
            else:
                if self._load_button is not None:
                    self._load_button.cued = False
                if self._save_button is not None:
                    self._save_button.cued = False
                if self._save_cue_box is not None:
                    self._save_cue_box.cued = False
                Printer.print_success_message(result)

    @property
    def code(self):
        return self._code

    @property
    def cue_outputs(self):
        return self._cue_outputs

    def _on_click_update_action(self) -> bool:
        self._output.clear_output(wait=True)
        raised_error = False
        # runs code and displays output
        with self._output:
            try:
                for cue_output in self.cue_outputs:
                    if hasattr(cue_output, "clear_display"):
                        cue_output.clear_display(wait=True)

                if self._update_func is not None:
                    self._update_func(self)
                elif self._code is not None:
                    self.run_code(**self.panel_parameters)

                for cue_output in self.cue_outputs:
                    if hasattr(cue_output, "draw_display"):
                        cue_output.draw_display()

            except CodeValidationError as e:
                raised_error = True
                raise e
            except Exception as e:
                raised_error = True
                raise e

        return not (raised_error)

    def run_code(self, *args, **kwargs) -> Check.FunOutParamsT:
        """
        Runs the `code` with the given (keyword) arguments and returns the output of the
        `code`. If no `code` was given on intialization, then a `ValueError` is raised.
        """
        try:
            if self._code is None:
                raise ValueError(
                    "run_code was invoked, but no code was given on initializaion"
                )
            return self._code.run(*args, **kwargs)
        except CodeValidationError as e:
            raise e
        except Exception as e:
            # we give the student the additional information that this is most likely
            # not because of his code
            if python_version() >= "3.11":
                e.add_note("This might be not related to your code input.")
            raise e
