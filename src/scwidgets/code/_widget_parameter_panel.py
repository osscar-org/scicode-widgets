from typing import Callable, Dict, List, Union

from ipywidgets import Output, VBox, Widget, interactive
from traitlets.utils.sentinel import Sentinel

from ..check import Check


class ParameterPanel(VBox):
    """
    A wrapper around ipywidgets.interactive to have more control how to connect the
    parameters and the observation of parameters by buttons and the panels

    :param parameters:
        Can be any input that is allowed as keyword arguments in ipywidgets.interactive
        for the parameters. _options and other widget layout parameter are controlled
        by CodeDemo.

    """

    def __init__(
        self,
        **parameters: Dict[str, Union[Check.FunInParamT, Widget]],
    ):
        if "_option" in parameters.keys():
            raise ValueError(
                "Found interactive argument `_option` in paramaters, but "
                "CodeDemo controls this parameter to ensure correct initialization."
            )

        # we use a dummy function because interactive executes it once on init
        # and the actual function might be expensive to compute
        def dummy_function(**kwargs):
            pass

        self._interactive_widget = interactive(dummy_function, **parameters)
        assert isinstance(self._interactive_widget.children[-1], Output), (
            "Assumed that interactive returns an output as last child. "
            "Parameter will be wrongly initialized if this is not True."
        )
        self._parameters_widget = list(self._interactive_widget.children[:-1])
        super().__init__(self._parameters_widget)

    @property
    def parameters_widget(self) -> List[Widget]:
        return self._parameters_widget

    @property
    def parameters_trait(self) -> List[str]:
        return ["value"] * len(self._parameters_widget)

    @property
    def parameters(self) -> dict:
        return self._interactive_widget.kwargs.copy()

    @parameters.setter
    def parameters(self, parameters: dict):
        # self._interactive_widget.kwargs is not sync with the trait
        # we assume that kwargs has the same order as in the widget children
        # to change the value of the children
        for i, key in enumerate(self._interactive_widget.kwargs):
            self._interactive_widget.children[i].value = parameters[key]

    def observe_parameters(
        self,
        handler: Callable[[dict], None],
        trait_name: Union[str, Sentinel, List[str]],
        notification_type: Union[None, str, Sentinel] = "change",
    ):
        """ """
        for widget in self._parameters_widget:
            widget.observe(handler, trait_name, notification_type)

    def unobserve_parameters(
        self,
        handler: Callable[[dict], None],
        trait_name: Union[str, Sentinel, List[str]],
        notification_type: Union[None, str, Sentinel] = "change",
    ):
        for widget in self._parameters_widget:
            widget.unobserve(handler, trait_name, notification_type)

    def set_parameters_widget_attr(self, name: str, value):
        for widget in self._parameters_widget:
            if hasattr(widget, name):
                setattr(widget, name, value)
