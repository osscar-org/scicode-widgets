# postpones evaluation of annotations
# see https://stackoverflow.com/a/33533514
from __future__ import annotations

import functools
import inspect
import types
from copy import deepcopy
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar, Union


class Check:
    """
    A check verifies the correctness of a function for a set of inputs parameters using
    a list of univariate and bivariate asserts with the option to obscure the reference
    outputs.

    :param function_to_check:
        The code_obj must have a `compute_output_to_check` function that accepts each
        input parameters in :params input parameters:
    :param inputs_parameters:
        A dict or a list of dictionaries each containing the argument name and its value
        as (key, value) pair that is used as input for the function
        `compute_output_to_check` of
        :param code_obj:
    :param outputs_references:
        A list or a list of lists each containing the expected output of the function
        `compute_output_to_check` of :param code_obj: for the inputsin the :param
        input_parameters:
    :param asserts:
        A list of assert functions. An assert function can the output parameters of
        :param function_to_check: to run assert. If output references has been set it
        can take additional output references to compare with. If a fingerprint is given
        then the fingerprints are compared while assert functions with a single argument
        are always applied on the output parameters.
    :param fingerprint:
        A one-way function that takes as input the output parameters of function :param
        function_to_check: and obscures the :param output_references:.
    """

    FunInParamT = TypeVar("FunInParamT", bound=Any)
    FunOutParamsT = Tuple[Any, ...]

    FingerprintT = TypeVar("FingerprintT", bound=Any)
    AssertFunT = Union[
        Callable[[FunOutParamsT, FunOutParamsT], str],
        Callable[[FingerprintT, FingerprintT], str],
        Callable[[FunOutParamsT], str],
    ]

    def __init__(
        self,
        function_to_check: Callable[..., FunOutParamsT],
        asserts: Union[List[AssertFunT], AssertFunT],
        inputs_parameters: Union[List[Dict[str, FunInParamT]], Dict[str, FunInParamT]],
        outputs_references: Optional[Union[List[tuple], tuple]] = None,
        fingerprint: Optional[
            Callable[[Check.FunOutParamsT], Check.FingerprintT]
        ] = None,
    ):
        self._function_to_check = function_to_check
        self._asserts = []
        self._univariate_asserts: List[Callable[[tuple], str]] = []
        self._bivariate_asserts = []
        if not (isinstance(asserts, list)):
            asserts = [asserts]

        for i, assert_f in enumerate(asserts):
            n_positional_arguments = len(
                [
                    parameters
                    for parameters in inspect.signature(assert_f).parameters.values()
                    if parameters.default is inspect._empty
                ]
            )
            self._asserts.append(assert_f)
            if n_positional_arguments == 1:
                # type checker cannot infer type change
                self._univariate_asserts.append(assert_f)  # type: ignore[arg-type]
            elif n_positional_arguments == 2:
                self._bivariate_asserts.append(assert_f)
            else:
                raise ValueError(
                    f"Only assert function with 1 or 2 positional arguments are allowed"
                    f"but assert function {i} has {n_positional_arguments} positional"
                    f"arguments"
                )

        # We sadly cannot verify if the number of input argumets match because they can
        # be hidden in **kwargs
        if isinstance(inputs_parameters, dict):
            inputs_parameters = [inputs_parameters]

        if outputs_references is not None:
            if isinstance(outputs_references, tuple):
                outputs_references = [outputs_references]
            assert len(inputs_parameters) == len(outputs_references), (
                "Number of inputs_parameters and outputs_references are mismatching: "
                "len inputs parameters != len outputs parameters "
                f"[{len(inputs_parameters)} != {len(outputs_references)}]."
            )

        self._inputs_parameters = inputs_parameters
        self._outputs_references = outputs_references
        self._fingerprint = fingerprint

    @property
    def function_to_check(self):
        return self._function_to_check

    @function_to_check.setter
    def function_to_check(self, function_to_check):
        self._function_to_check = function_to_check

    @property
    def fingerprint(self):
        return deepcopy(self._fingerprint)

    @property
    def asserts(self):
        return deepcopy(self._asserts)

    @property
    def univariate_asserts(self):
        return deepcopy(self._univariate_asserts)

    @property
    def bivariate_asserts(self):
        return deepcopy(self._bivariate_asserts)

    @property
    def inputs_parameters(self):
        return deepcopy(self._inputs_parameters)

    @property
    def outputs_references(self):
        return deepcopy(self._outputs_references)

    @property
    def nb_conducted_asserts(self):
        return len(self._asserts) * len(self._inputs_parameters)

    def compute_outputs(self):
        outputs = []
        for input_parameters in self._inputs_parameters:
            output = self._function_to_check(**input_parameters)
            if not (isinstance(output, tuple)):
                output = (output,)
            if self._fingerprint is not None:
                output = self._fingerprint(*output)
                if not (isinstance(output, tuple)):
                    output = (output,)
            outputs.append(output)
        return outputs

    def compute_and_set_references(self):
        self._outputs_references = self.compute_outputs()

    def check_function(self) -> ChecksLog:
        """
        Returns for each input (first depth list) the result message for each assert
        (second depth list).  If a result message is empty, the assert was successful,
        otherwise it contains information about the failure.
        """
        if len(self._bivariate_asserts) > 0:
            if self._outputs_references is None:
                raise ValueError(
                    "outputs_references are None but asserts exist that require "
                    "outputs_references (second positional argument)"
                )
            assert len(self._inputs_parameters) == len(self._outputs_references), (
                "Number of inputs and reference outputs  "
                "are mismatching: len inputs parameters != len outputs parameters "
                f"[{len(self._inputs_parameters)} != {len(self._outputs_references)}]."
            )

        check_result = ChecksLog()
        for i, input_parameters in enumerate(self._inputs_parameters):
            output = self._function_to_check(**input_parameters)
            if not (isinstance(output, tuple)):
                output = (output,)

            for assert_f in self._univariate_asserts:
                assert_result = assert_f(output)
                check_result.append(assert_result, assert_f, input_parameters)

            if self._fingerprint is not None:
                output = self._fingerprint(*output)
                if not (isinstance(output, tuple)):
                    output = (output,)

            for assert_f in self._bivariate_asserts:  # type: ignore[assignment]
                assert len(output) == len(
                    self._outputs_references[i]  # type: ignore[index]
                ), (
                    "Number of output parameters and reference output parameters "
                    "are mismatching: "
                    "len output parameters != len outputs references "
                    f"[{len(output)} != "
                    f"{len(self._outputs_references[i])}]."  # type: ignore[index]
                )

                assert_result = assert_f(
                    output, self._outputs_references[i]  # type: ignore[index, call-arg]
                )
                check_result.append(assert_result, assert_f, input_parameters)
        return check_result


class ChecksLog:
    def __init__(self):
        self._assert_results = []
        self._assert_names = []
        self._inputs_parameters = []

    def append(
        self,
        assert_result: str,
        assert_f: Optional[Check.AssertFunT] = None,
        input_parameters: Optional[dict] = None,
    ):
        self._assert_results.append(assert_result)
        self._assert_names.append(self._get_name_from_assert(assert_f))
        self._inputs_parameters.append(input_parameters)

    def extend(self, check_results: ChecksLog):
        self._assert_results.extend(check_results._assert_results)
        self._assert_names.extend(check_results._assert_names)
        self._inputs_parameters.extend(check_results._inputs_parameters)

    @property
    def successful(self):
        return len([result for result in self._assert_results if result != ""]) == 0

    def message(self) -> str:
        messages = [
            f"Test failed for input:\n"
            f"  {self._inputs_parameters[i]}\n"
            f"  {self._assert_names[i]} failed: {result}\n"
            for i, result in enumerate(self._assert_results)
            if result != ""
        ]
        return "\n".join(messages)

    def _get_name_from_assert(self, assert_f: Any) -> str:
        if isinstance(assert_f, types.FunctionType):
            return assert_f.__name__
        elif isinstance(assert_f, functools.partial):
            return assert_f.func.__name__
        else:
            return str(assert_f)

    @property
    def assert_results(self):
        return deepcopy(self._assert_results)

    @property
    def assert_names(self):
        return deepcopy(self._assert_names)

    @property
    def inputs_parameters(self):
        return deepcopy(self._inputs_parameters)
