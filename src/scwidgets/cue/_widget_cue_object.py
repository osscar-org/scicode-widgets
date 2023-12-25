# postpones evaluation of annotations
# see https://stackoverflow.com/a/33533514
from __future__ import annotations

from typing import Any, List, Optional, Union

from IPython.display import display
from ipywidgets import Widget
from traitlets.utils.sentinel import Sentinel

from ._widget_cue_output import CueOutput


class CueObject(CueOutput):
    """
    A cued displayable ipywidget.Output for any Python object.  Provides utilities to
    clear and redraw the object, for example after an update.

    :param display_object:
        The object to display
    :param widgets_to_observe:
        The widget to observe if the :param traits_to_observe: has changed.
    :param traits_to_observe:
        The trait from the :param widgets_to_observe: to observe if changed.
        Specify `traitlets.All` to observe all traits.
    :param cued:
        Specifies if it is cued on initialization
    :param css_syle:
        - **base**: the css style of the box during initialization
        - **cue**: the css style that is added when :param
          traits_to_observe: in widget :param widgets_to_observe: changes.
          It is supposed to change the style of the box such that the user has a visual
          cue that :param widget_to_cue: has changed.
    """

    def __init__(
        self,
        display_object: Any = None,
        widgets_to_observe: Union[None, List[Widget], Widget] = None,
        traits_to_observe: Union[
            None, str, List[str], List[List[str]], Sentinel
        ] = None,
        cued: bool = True,
        css_style: Optional[dict] = None,
        *args,
        **kwargs,
    ):
        CueOutput.__init__(
            self,
            widgets_to_observe,
            traits_to_observe,
            cued,
            css_style,
            **kwargs,
        )

        self._display_object = display_object
        self.draw_display()

    @property
    def display_object(self):
        return self._display_object

    @display_object.setter
    def display_object(self, display_object: Any):
        self._display_object = display_object

    def clear_display(self, wait=False):
        self.clear_output(wait=wait)

    def draw_display(self):
        with self:
            if isinstance(self._display_object, str):
                print(self._display_object)
            elif self._display_object is not None:
                display(self._display_object)
