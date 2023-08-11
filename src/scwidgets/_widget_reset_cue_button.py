from typing import Callable, List, Union

from ipywidgets import Button

from ._widget_cue_box import CueBox


class ResetCueButton(Button):
    """
    A button that resets the cueing of the :param cue_boxes: on a successful action.

    :param cue_boxes:
       List of cue boxes the button resets on successuful click
       We assert that all boxes observe the same traits of the same widget
    :param action:
        A callable that returns a boolean that specifies if the action was successul.
        If is called on a button click. The cues in :param cue_boxes: are removed if it
        was successful, if False nothing happens.
    :param disable_on_successful_action:
        Specifies if the button should be disabled on a successful action

    Further accepts the same (keyword) arguments as :py:class:`ipywidgets.Button`.
    """

    def __init__(
        self,
        cue_boxes: Union[CueBox, List[CueBox]],
        action: Callable[[], bool],
        disable_on_successful_action: bool = True,
        *args,
        **kwargs,
    ):
        if not (isinstance(cue_boxes, list)):
            cue_boxes = [cue_boxes]

        # we check if all cue boxes have the same widget they observe
        for cue_box in cue_boxes:
            assert (
                cue_boxes[0].widget_to_observe == cue_box.widget_to_observe
            ), "All CueBox's in `cue_boxes` must have same `widget_to_observe`"
            assert (
                cue_boxes[0].traits_to_observe == cue_box.traits_to_observe
            ), "All CueBox's in `cue_boxes` must have same `traits_to_observe`"

        self._cue_boxes = cue_boxes
        self._action = action
        self._disable_on_successful_action = disable_on_successful_action

        super().__init__(*args, **kwargs)

        if len(self._cue_boxes) > 0:
            self._cue_boxes[0].widget_to_observe.observe(
                self._on_cue_boxes_traits_to_observe_changed,
                self._cue_boxes[0].traits_to_observe,
            )
            self.disabled = not (self._cue_boxes[0].cued)

        self.on_click(self._reset_on_successful_action)

    @property
    def cue_boxes(self):
        return self._cue_boxes

    @cue_boxes.setter
    def cue_boxes(self, cue_boxes: Union[CueBox, List[CueBox]]):
        for cue_box in cue_boxes:
            assert (
                cue_boxes[0].widget_to_observe == cue_box.widget_to_observe
            ), "All CueBox's in `cue_boxes` must have same `widget_to_observe`"
            assert (
                cue_boxes[0].traits_to_observe == cue_box.traits_to_observe
            ), "All CueBox's in `cue_boxes` must have same `traits_to_observe`"

        if len(self._cue_boxes) > 0:
            self._cue_boxes[0].widget_to_observe.unobserve(
                self._on_cue_boxes_traits_to_observe_changed,
            )

        self._cue_boxes = cue_boxes
        if len(self._cue_boxes) > 0:
            self._cue_boxes[0].widget_to_observe.observe(
                self._on_cue_boxes_traits_to_observe_changed,
                self._cue_boxes[0].traits_to_observe,
            )
            self.disabled = not (self._cue_boxes[0].cued)

    @property
    def action(self):
        return self._action

    @action.setter
    def action(self, value):
        self._action = value

    @property
    def disable_on_successful_action(self):
        return self._disable_on_successful_action

    @disable_on_successful_action.setter
    def disable_on_successful_action(self, disable_on_successful_action: bool):
        self._disable_on_successful_action = disable_on_successful_action

    def _reset_on_successful_action(self, button: Button):
        success = self._action()
        if success:
            for cue_box in self._cue_boxes:
                cue_box.cued = False
                if self._disable_on_successful_action:
                    self.disabled = True

    def _on_cue_boxes_traits_to_observe_changed(self, change: dict):
        self.disabled = False
