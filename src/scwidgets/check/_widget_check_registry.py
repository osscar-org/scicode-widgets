# postpones evaluation of annotations
# see https://stackoverflow.com/a/33533514
from __future__ import annotations

from collections import OrderedDict
from typing import Callable, List, Optional, Union

from ipywidgets import Button, HBox, Layout, Output, VBox, Widget

from ._check import Check, ChecksLog


class CheckableWidget:
    """
    A base class for any widget to inherit from to be compatible with the
    :py:class:`CheckRegistry`. The logic is th

    :param check_registry:
        the check registry that registers the checks for this widget
    """

    def __init__(self, check_registry: CheckRegistry):
        self._check_registry = check_registry
        self._check_registry.register_widget(self)

    def compute_output_to_check(
        self, *input_args: Check.FunInParamT
    ) -> Check.FunOutParamsT:
        """
        The widget returns the output that will verified by the added checks.
        """
        raise NotImplementedError("compute_output_to_check has not been implemented")

    def handle_checks_result(self, result: Union[ChecksLog, Exception]) -> None:
        """
        Function that controls how results of the checks are handled.
        """
        raise NotImplementedError("handle_checks_result has not been implemented")

    def add_check(
        self,
        asserts: Union[List[Check.AssertFunT], Check.AssertFunT],
        inputs_parameters: Union[List[dict], dict],
        outputs_references: Optional[
            Union[List[Check.FunOutParamsT], Check.FunOutParamsT]
        ] = None,
        fingerprint: Optional[
            Callable[[Check.FunOutParamsT], Check.FingerprintT]
        ] = None,
    ):
        if not (hasattr(self, "_check_registry")) or self._check_registry is None:
            raise ValueError(
                "No check registry given on initialization, no checks can be added"
            )

        self._check_registry.add_check(
            self, asserts, inputs_parameters, outputs_references, fingerprint
        )

    def compute_and_set_references(self):
        self._check_registry.compute_and_set_references(self)

    @property
    def checks(self):
        return self._check_registry._checks[self]

    @property
    def check_registry(self):
        return self._check_registry

    @property
    def nb_conducted_asserts(self):
        return self._check_registry.nb_conducted_asserts(self)


class CheckRegistry(VBox):
    """
    Manages the assignment of checks to widgets and the execution of checks. It allows
    to run the checks of all widgets and properly pipes the result to the corresponding
    function of the widget.
    """

    def __init__(self, *args, **kwargs):
        self._checks = OrderedDict()
        self._names = OrderedDict()
        self._set_all_references_button = Button(description="Set all references")
        self._check_all_widgets_button = Button(description="Check all widgets")
        self._output = Output()
        kwargs["layout"] = kwargs.pop("layout", Layout(width="100%"))
        VBox.__init__(
            self,
            [
                HBox([self._set_all_references_button, self._check_all_widgets_button]),
                self._output,
            ],
            *args,
            **kwargs,
        )

        self._set_all_references_button.on_click(
            self._on_click_set_all_references_button
        )
        self._check_all_widgets_button.on_click(self._on_click_check_all_widgets_button)

    @property
    def checks(self):
        """
        all registerd checks from widgets to checks
        """
        return self._checks

    def nb_conducted_asserts(self, widget: CheckableWidget):
        """
        The total number of asserts that will be conducted for the widget

        :param widget:
            the checks of the widget are targeted
        """
        return sum([check.nb_conducted_asserts for check in self._checks[widget]])

    def register_widget(self, widget: CheckableWidget, name: Optional[str] = None):
        self._checks[widget] = []
        if name is None:
            self._names[widget] = len(self._checks)
        else:
            self._names[widget] = name

    def add_check(
        self,
        widget: CheckableWidget,
        asserts: Union[List[Check.AssertFunT], Check.AssertFunT],
        inputs_parameters: Union[List[dict], dict],
        outputs_references: Optional[
            Union[List[Check.FunOutParamsT], Check.FunOutParamsT]
        ] = None,
        fingerprint: Optional[
            Callable[[Check.FunOutParamsT], Check.FingerprintT]
        ] = None,
    ):
        if not (issubclass(type(widget), CheckableWidget)):
            raise ValueError("Argument widget must be subclass of CheckableWidget")
        if widget not in self._checks.keys():
            raise ValueError(
                "Argument widget must be first registered before checks can be added."
            )
        check = Check(
            widget.compute_output_to_check,
            asserts,
            inputs_parameters,
            outputs_references,
            fingerprint,
        )
        self._checks[widget].append(check)

    def compute_and_set_references(self, widget: Widget):
        for check in self._checks[widget]:
            try:
                check.compute_and_set_references()
            except Exception as exception:
                widget.handle_checks_result(exception)
                raise exception

    def compute_outputs(self, widget: Widget):
        for check in self._checks[widget]:
            try:
                return check.compute_outputs()
            except Exception as exception:
                widget.handle_checks_result(exception)
                raise exception

    def compute_and_set_all_references(self):
        for widget in self._checks.keys():
            self.compute_and_set_references(widget)

    def check_widget(self, widget: Widget) -> ChecksLog:
        results = ChecksLog()
        try:
            for check in self._checks[widget]:
                result = check.check_function()
                results.extend(result)
                widget.handle_checks_result(result)
        except Exception as exception:
            widget.handle_checks_result(exception)
            raise exception
        return results

    def check_all_widgets(
        self,
    ) -> OrderedDict[CheckableWidget, Union[ChecksLog, Exception]]:
        messages: OrderedDict[
            CheckableWidget, Union[ChecksLog, Exception]
        ] = OrderedDict()
        for widget in self._checks.keys():
            try:
                messages[widget] = self.check_widget(widget)
            except Exception as exception:
                messages[widget] = exception
        return messages

    def _on_click_set_all_references_button(self, change: dict):
        self._output.clear_output()
        with self._output:
            self.compute_and_set_all_references()
            print("Successful set all references.")

    def _on_click_check_all_widgets_button(self, change: dict):
        self._output.clear_output()
        widgets_results = self.check_all_widgets()
        for widget, widget_results in widgets_results.items():
            with self._output:
                if isinstance(widget_results, Exception):
                    print(f"Widget {self._names[widget]} raised error:")
                    raise widget_results
                elif isinstance(widget_results, ChecksLog):
                    if widget_results.successful:
                        print(
                            f"Widget {self._names[widget]} all checks were successful."
                        )
                    else:
                        print(
                            f"Widget {self._names[widget]} not all checks were "
                            "successful:"
                        )
                        print(widget_results.message())
                else:
                    raise ValueError(
                        f"Not supported result type {type(widget_results)}. "
                        "Only results of type `Exception` and `CheckResult` "
                        "are supported."
                    )
