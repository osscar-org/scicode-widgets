from typing import Dict, List, Union

from ipywidgets import Output, VBox, Widget, interactive

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
        parameters: Dict[str, Union[Check.FunInParamT, Widget]],
        **kwargs,
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
        for widget in self._parameters_widget:
            widget.unobserve_all()
        super().__init__(self._parameters_widget)

    @property
    def parameters_widget(self) -> List[Widget]:
        return self._parameters_widget

    @property
    def parameters(self):
        return self._interactive_widget.kwargs
