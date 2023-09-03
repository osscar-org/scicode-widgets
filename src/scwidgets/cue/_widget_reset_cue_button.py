from typing import Callable, Dict, List, Optional, Union

from ipywidgets import Button

from ._widget_cue import CueWidget


class ResetCueButton(Button, CueWidget):
    """
    A button that resets the cueing of the :param cue_widgets: on a successful action.

    :param cue_widgets:
       List of cue boxes the button resets on successuful click
       We assert that all boxes observe the same traits of the same widget
    :param action:
        A callable that returns a boolean that specifies if the action was successul.
        If is called on a button click. The cues in :param cue_widgets:
        are removed if it
        was successful, if False nothing happens.
    :param disable_on_successful_action:
        Specifies if the button should be disabled on a successful action

    Further accepts the same (keyword) arguments as :py:class:`ipywidgets.Button`.
    """

    def __init__(
        self,
        cue_widgets: Union[CueWidget, List[CueWidget]],
        action: Callable[[], bool],
        disable_on_successful_action: bool = True,
        css_style: Optional[Dict[str, str]] = None,
        *args,
        **kwargs,
    ):
        if "cued" in kwargs.keys():
            raise ValueError(
                "ResetCueButton determines cueing from cue_widgets,"
                ' "cued" cannot be given as argument'
            )

        if css_style is None:
            css_style = {
                "base": "scwidget-reset-cue-button",
                "cue": "scwidget-reset-cue-button--cue",
            }
        if "base" not in css_style.keys():
            raise ValueError('css_style is missing key "base".')
        if "cue" not in css_style.keys():
            raise ValueError('css_style is missing key "cue".')

        if not (isinstance(cue_widgets, list)):
            cue_widgets = [cue_widgets]

        self._action = action
        self._disable_on_successful_action = disable_on_successful_action

        self._css_style = css_style

        Button.__init__(self, *args, **kwargs)

        widgets_to_observe = []
        traits_to_observe = []
        for cue_widget in cue_widgets:
            widgets_to_observe.extend(cue_widget.widgets_to_observe)
            traits_to_observe.extend(cue_widget.traits_to_observe)
        CueWidget.__init__(self, widgets_to_observe, traits_to_observe)
        self.cued = any([cue_widget.cued for cue_widget in cue_widgets])
        self._cue_widgets = cue_widgets

        self.on_click(self._on_click)

        self.add_class(self._css_style["base"])

    @property
    def cue_widgets(self) -> List[CueWidget]:
        return self._cue_widgets

    @cue_widgets.setter
    def cue_widgets(self, cue_widgets: List[CueWidget]):
        self.unobserve_widgets()

        # set new cue widgets
        widgets_to_observe = []
        traits_to_observe = []
        for cue_widget in cue_widgets:
            widgets_to_observe.extend(cue_widget.widgets_to_observe)
            traits_to_observe.extend(cue_widget.traits_to_observe)
        CueWidget.__init__(self, widgets_to_observe, traits_to_observe)
        self.cued = any([cue_widget.cued for cue_widget in cue_widgets])
        self._cue_widgets = cue_widgets

    @property
    def cued(self):
        return self._cued

    @cued.setter
    def cued(self, cued: bool):
        if cued:
            self.add_class(self._css_style["cue"])
            self.disabled = False
        else:
            self.remove_class(self._css_style["cue"])
        self._cued = cued

    @property
    def action(self):
        return self._action

    @action.setter
    def action(self, action):
        self._action = action

    @property
    def disable_on_successful_action(self):
        return self._disable_on_successful_action

    @disable_on_successful_action.setter
    def disable_on_successful_action(self, disable_on_successful_action: bool):
        self._disable_on_successful_action = disable_on_successful_action

    def _on_click(self, button: Button):
        self.disabled = True
        success = False
        try:
            success = self._action()
        except Exception as e:
            raise e
        finally:
            for cue_box in self._cue_widgets:
                cue_box.cued = False
            self.cued = False
            self.disabled = success and self._disable_on_successful_action
