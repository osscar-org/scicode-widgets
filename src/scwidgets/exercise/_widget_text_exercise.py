from typing import Optional, Union

from ipywidgets import HTML, HBox, HTMLMath, Layout, Output, Textarea, VBox

from .._css_style import CssStyle
from .._utils import Formatter
from ..cue import SaveCueBox, SaveResetCueButton
from ._widget_exercise_registry import ExerciseRegistry, ExerciseWidget


class TextExercise(VBox, ExerciseWidget):
    """
    :param textarea:
        a custom textarea with custom styling, if not specified the standard parameters
        are given.

    the (keyword) arguments are passed to VBox
    """

    def __init__(
        self,
        value: Optional[str] = None,
        exercise_key: Optional[str] = None,
        exercise_registry: Optional[ExerciseRegistry] = None,
        exercise_description: Optional[str] = None,
        exercise_title: Optional[str] = None,
        *args,
        **kwargs,
    ):
        self._exercise_description = exercise_description
        if exercise_description is None:
            self._exercise_description_html = None
        else:
            self._exercise_description_html = HTMLMath(self._exercise_description)
        if exercise_title is None:
            if exercise_key is None:
                self._exercise_title = None
                self._exercise_title_html = None
            else:
                self._exercise_title = exercise_key
                self._exercise_title_html = HTML(f"<b>{exercise_key}</b>")
        else:
            self._exercise_title = exercise_title
            self._exercise_title_html = HTML(f"<b>{exercise_title}</b>")

        if self._exercise_description_html is not None:
            self._exercise_description_html.add_class("exercise-description")
        if self._exercise_title_html is not None:
            self._exercise_title_html.add_class("exercise-title")

        layout = kwargs.pop("layout", Layout(width="auto", height="150px"))
        self._textarea = Textarea(value, *args, layout=layout, **kwargs)
        self._cue_textarea = self._textarea
        self._output = Output()

        if exercise_registry is None:
            self._save_button = None
            self._load_button = None
            self._button_panel = None
        else:
            self._cue_textarea = SaveCueBox(
                self._textarea, "value", self._cue_textarea, cued=True
            )
            self._save_button = SaveResetCueButton(
                self._cue_textarea,
                self._on_click_save_action,
                disable_on_successful_action=kwargs.pop(
                    "disable_save_button_on_successful_action", False
                ),
                disable_during_action=kwargs.pop(
                    "disable_save_button_during_action", True
                ),
                description="Save answer",
                button_tooltip="Saves answer to the loaded file",
            )

            self._cue_code = SaveCueBox(
                self._textarea, "value", self._cue_textarea, cued=True
            )
            self._load_button = SaveResetCueButton(
                self._cue_textarea,
                self._on_click_load_action,
                disable_on_successful_action=kwargs.pop(
                    "disable_load_button_on_successful_action", False
                ),
                disable_during_action=kwargs.pop(
                    "disable_load_button_during_action", True
                ),
                description="Load answer",
                button_tooltip="Loads answer from the loaded file",
            )

            # click on load button resets cue of save buton and vise-versa
            self._save_button.set_cue_widgets([self._cue_textarea, self._load_button])
            self._load_button.set_cue_widgets([self._cue_textarea, self._save_button])
            self._button_panel = HBox(
                [self._save_button, self._load_button],
                layout=Layout(justify_content="flex-end"),
            )

        ExerciseWidget.__init__(self, exercise_registry, exercise_key)

        widget_children = [CssStyle()]
        if self._exercise_title_html is not None:
            widget_children.append(self._exercise_title_html)
        if self._exercise_description_html is not None:
            widget_children.append(self._exercise_description_html)
        widget_children.append(self._cue_textarea)
        if self._button_panel:
            widget_children.append(self._button_panel)

        widget_children.append(self._output)

        VBox.__init__(
            self,
            widget_children,
        )

    @property
    def exercise_title(self) -> Union[str, None]:
        return self._exercise_title

    @property
    def exercise_description(self) -> Union[str, None]:
        return self._exercise_description

    @property
    def answer(self) -> dict:
        return {"textarea": self._textarea.value}

    @answer.setter
    def answer(self, answer: dict):
        # this function should only be used by the AnsweRegistry to set value
        # because we don't want to cue if a loading changes the the value we disable it
        if hasattr(self._cue_textarea, "unobserve_widgets"):
            self._cue_textarea.unobserve_widgets()
        if self._save_button is not None:
            self._save_button.unobserve_widgets()
        if self._load_button is not None:
            self._load_button.unobserve_widgets()

        self._textarea.value = answer["textarea"]

        if hasattr(self._cue_textarea, "unobserve_widgets"):
            self._cue_textarea.observe_widgets()
        if self._save_button is not None:
            self._save_button.observe_widgets()
        if self._load_button is not None:
            self._load_button.observe_widgets()

    def _on_click_save_action(self) -> bool:
        self._output.clear_output(wait=True)
        raised_error = False
        with self._output:
            try:
                result = self.save()
                if isinstance(result, str):
                    print(Formatter.color_success_message(result))
                elif isinstance(result, Exception):
                    raise result
                else:
                    print(result)
            except Exception as e:
                print(Formatter.color_error_message("Error raised while saving file:"))
                raised_error = True
                raise e
        return not (raised_error)

    def _on_click_load_action(self) -> bool:
        self._output.clear_output(wait=True)
        raised_error = False
        with self._output:
            try:
                result = self.load()
                if isinstance(result, str):
                    print(Formatter.color_success_message(result))
                elif isinstance(result, Exception):
                    raise result
                else:
                    print(result)
                return True
            except Exception as e:
                print(Formatter.color_error_message("Error raised while loading file:"))
                raised_error = True
                raise e
        return not (raised_error)

    def handle_save_result(self, result: Union[str, Exception]) -> None:
        self._output.clear_output(wait=True)
        with self._output:
            if isinstance(result, Exception):
                print(Formatter.color_error_message("Error raised while saving file:"))
                raise result
            else:
                # answer changes, so we have to disable the automatic cueing
                if self._load_button is not None:
                    self._load_button.cued = False
                if self._save_button is not None:
                    self._save_button.cued = False
                if self._cue_textarea is not None:
                    self._cue_textarea.cued = False
                print(Formatter.color_success_message(result))

    def handle_load_result(self, result: Union[str, Exception]) -> None:
        self._output.clear_output(wait=True)
        with self._output:
            if isinstance(result, Exception):
                print(Formatter.color_error_message("Error raised while loading file:"))
                raise result
            else:
                if self._load_button is not None:
                    self._load_button.cued = False
                if self._save_button is not None:
                    self._save_button.cued = False
                if self._cue_textarea is not None:
                    self._cue_textarea.cued = False
                print(Formatter.color_success_message(result))
