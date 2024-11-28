import re

import numpy as np
import pytest

from scwidgets.check import (
    Check,
    CheckableWidget,
    CheckRegistry,
    CheckResult,
    assert_equal,
    assert_numpy_allclose,
    assert_numpy_floating_sub_dtype,
    assert_shape,
    assert_type,
)


def test_assert_equal():
    output_parameters = (42,)
    output_references = (42,)
    result = assert_equal(output_parameters, output_references)
    assert result.successful

    output_parameters = (42,)
    output_references = (41,)
    result = assert_equal(output_parameters, output_references)
    assert not result.successful


def test_assert_shape():
    output_parameters = (np.array([1, 2, 3]),)
    output_references = (np.array([1, 2, 3]),)
    result = assert_shape(output_parameters, output_references)
    assert result.successful


def test_assert_invalid_parameters_to_check():
    with pytest.raises(
        ValueError, match='Got parameters_to_check="invalid" but only .*'
    ):
        assert_shape([1, 2, 3], [1, 2, 3], parameters_to_check="invalid")


def test_assert_numpy_allclose():
    output_parameters = (np.array([1.0, 2.0]),)
    output_references = (np.array([1.1, 2.2]),)
    result = assert_numpy_allclose(output_parameters, output_references)
    assert "Output is not close to reference" in result.message()


def test_assert_type():
    output_parameters = (42,)
    output_references = (42,)
    result = assert_type(output_parameters, output_references)
    assert result.successful


def test_assert_numpy_floating_sub_dtype():
    output_parameters = (np.array([1.0, 2.0]),)
    result = assert_numpy_floating_sub_dtype(output_parameters)
    assert result.successful


def test_assert_invalid_output_parameter_dtype():
    output_parameters = (np.array([1, 2]),)
    result = assert_numpy_floating_sub_dtype(output_parameters)
    assert (
        "Output expected to be sub dtype numpy.floating " "but got numpy.int64."
    ) in result.message()


def no_param_check(failing):

    def function_to_check(parameter):
        print("SomeText")
        return parameter * 2

    def custom_assert() -> str:
        # property-based tests with the student code
        if failing:
            return "Check does not fulfill property"
        return ""

    return Check(
        function_to_check=function_to_check,
        asserts=[custom_assert],
    )


def single_param_check(use_fingerprint=False, failing=False, buggy=False):
    if buggy:

        def function_to_check(parameter):
            print("SomeText")
            # these comments are important so SomeText is not printed in the error log,
            # so we can assume that it occurs only once
            #
            #
            #
            bug  # noqa : F821
            return parameter * 2

    else:

        def function_to_check(parameter):
            print("SomeText")
            return parameter * 2

    inputs_parameters = [
        {"parameter": np.array([1.0])},
        {"parameter": np.array([2.0])},
    ]
    if failing:
        outputs_references = [(np.array([2.0]),), (np.array([3.0]),)]
    else:
        outputs_references = [(np.array([2.0]),), (np.array([4.0]),)]

    if use_fingerprint:

        def fingerprint(output_parameter):
            return np.sum(output_parameter)

        for i, output_references in enumerate(outputs_references):
            outputs_references[i] = (fingerprint(*output_references),)
    else:
        fingerprint = None

    return Check(
        function_to_check=function_to_check,
        asserts=[
            assert_type,
            assert_shape,
            assert_numpy_floating_sub_dtype,
            assert_numpy_allclose,
        ],
        inputs_parameters=inputs_parameters,
        outputs_references=outputs_references,
        fingerprint=fingerprint,
    )


def multi_param_check(use_fingerprint=False, failing=False):
    def function_to_check(parameter1, parameter2, parameter3=None):
        return parameter1 + parameter2, parameter3 * parameter2

    if failing:
        outputs_references = [
            (
                np.array([1.0]),
                np.array([2.0]),
            )
        ]
    else:
        outputs_references = [
            (
                np.array([3.0]),
                np.array([6.0]),
            )
        ]

    if use_fingerprint:

        def fingerprint(output_parameter1, output_parameter2):
            return np.sum(output_parameter1) + np.sum(output_parameter2)

        for i, output_references in enumerate(outputs_references):
            outputs_references[i] = (fingerprint(*output_references),)
    else:
        fingerprint = None

    return Check(
        function_to_check=function_to_check,
        asserts=[
            assert_type,
            assert_shape,
            assert_numpy_floating_sub_dtype,
            assert_numpy_allclose,
        ],
        inputs_parameters=[
            {
                "parameter1": np.array([1.0]),
                "parameter2": np.array([2.0]),
                "parameter3": np.array([3.0]),
            }
        ],
        outputs_references=outputs_references,
        fingerprint=fingerprint,
    )


class TestCheck:
    @pytest.mark.parametrize(
        "check",
        [
            no_param_check(failing=False),
            single_param_check(use_fingerprint=False, failing=False),
            multi_param_check(use_fingerprint=False, failing=False),
            single_param_check(use_fingerprint=True, failing=False),
            multi_param_check(use_fingerprint=True, failing=False),
        ],
    )
    def test_succesful_check_function(self, check):
        result = check.check_function()
        assert result.successful

    @pytest.mark.parametrize(
        "check",
        [
            single_param_check(use_fingerprint=False, failing=True),
            multi_param_check(use_fingerprint=False, failing=True),
            single_param_check(use_fingerprint=True, failing=True),
            multi_param_check(use_fingerprint=True, failing=True),
        ],
    )
    def test_compute_and_set_references(self, check):
        # we overwrite failing outputs_references
        check.compute_and_set_references()
        # now checks should be successful again
        result = check.check_function()
        assert isinstance(result, CheckResult)
        assert result.successful

    @pytest.mark.parametrize(
        "check",
        [
            no_param_check(failing=True),
            single_param_check(use_fingerprint=False, failing=True),
            multi_param_check(use_fingerprint=False, failing=True),
            single_param_check(use_fingerprint=True, failing=True),
            multi_param_check(use_fingerprint=True, failing=True),
        ],
    )
    def test_failing_check_all_widgets(self, check):
        result = check.check_function()
        assert isinstance(result, CheckResult)
        assert not (result.successful)

    def test_invalid_asserts_arguments_count(self):
        def function_to_check(parameter):
            return parameter * 2

        with pytest.raises(
            ValueError,
            match=r"Only assert function with 1 or 2 positional arguments are allowed",
        ):
            Check(
                function_to_check=function_to_check,
                asserts=[lambda output, ref, invalid: None],  # Three arguments
                inputs_parameters=[{"parameter": np.array([1])}],
                outputs_references=[(np.array([2]),)],
                fingerprint=None,
            ).check_function()

    def test_mismatching_parameters_references_length(self):
        def function_to_check(parameter):
            return parameter * 2

        error_message = (
            "Number of output parameters and reference output parameters are "
            "mismatching: len output parameters != len outputs references [1 != 2]."
        )
        with pytest.raises(AssertionError, match=re.escape(error_message)):
            Check(
                function_to_check=function_to_check,
                asserts=[assert_shape],
                inputs_parameters=[{"parameter": np.array([1])}],
                outputs_references=[(np.array([2]), "invalid")],
                fingerprint=None,
            ).check_function()


def mock_checkable_widget(check_registry, compute_output_to_check, checks=None):
    class MockCheckableWidget(CheckableWidget):
        def __init__(self, check_registry):
            self.results = []
            super().__init__(check_registry)

        def compute_output_to_check(self):
            pass

        def handle_checks_result(self, result):
            self.results.extend(result)

    checkable_widget = MockCheckableWidget(check_registry)
    checkable_widget.compute_output_to_check = compute_output_to_check
    if checks is None:
        checks = []
    for check in checks:
        checkable_widget.compute_output_to_check = check.function_to_check
        checkable_widget.add_check(
            check.asserts,
            check.inputs_parameters,
            check.outputs_references,
            check.fingerprint,
        )
    return checkable_widget


class TestCheckRegistry:
    @pytest.mark.parametrize(
        "checks",
        [
            [no_param_check(failing=False)],
            [
                single_param_check(use_fingerprint=False, failing=False),
                single_param_check(use_fingerprint=True, failing=False),
            ],
            [multi_param_check(use_fingerprint=False, failing=False)],
            [single_param_check(use_fingerprint=True, failing=False)],
            [multi_param_check(use_fingerprint=True, failing=False)],
        ],
    )
    def test_successful_check_all_widgets(self, checks):
        check_registry = CheckRegistry()
        checkable_widget = mock_checkable_widget(
            check_registry, checks[0].function_to_check, checks
        )

        widgets_results = check_registry.check_all_widgets()
        nb_conducted_asserts = 0
        for results in widgets_results.values():
            for result in results:
                assert isinstance(result, CheckResult)
                assert result.successful
                nb_conducted_asserts += len(result.assert_results)
        assert nb_conducted_asserts == checkable_widget.nb_conducted_asserts

        assert len(checkable_widget.results) == len(checks)
        nb_conducted_asserts = 0
        for results in widgets_results.values():
            for result in results:
                assert isinstance(result, CheckResult)
                assert result.successful
                nb_conducted_asserts += len(result.assert_results)
        assert nb_conducted_asserts == checkable_widget.nb_conducted_asserts

    @pytest.mark.parametrize(
        "checks",
        [
            [
                single_param_check(use_fingerprint=False, failing=True),
                single_param_check(use_fingerprint=True, failing=True),
            ],
            [multi_param_check(use_fingerprint=False, failing=True)],
            [single_param_check(use_fingerprint=True, failing=True)],
            [multi_param_check(use_fingerprint=True, failing=True)],
        ],
    )
    def test_compute_and_set_all_references(self, checks):
        check_registry = CheckRegistry()
        checkable_widget = mock_checkable_widget(
            check_registry, checks[0].function_to_check, checks
        )

        # sets all check outputs references to the correct reference
        check_registry.compute_and_set_all_references()

        widgets_results = check_registry.check_all_widgets()

        nb_conducted_asserts = 0
        for results in widgets_results.values():
            for result in results:
                assert isinstance(result, CheckResult)
                assert result.successful
                nb_conducted_asserts += len(result.assert_results)
        assert nb_conducted_asserts == checkable_widget.nb_conducted_asserts

        nb_conducted_asserts = 0
        assert len(checkable_widget.results) == len(checks)
        for result in checkable_widget.results:
            assert isinstance(result, CheckResult)
            assert result.successful
            nb_conducted_asserts += len(result.assert_results)
        assert nb_conducted_asserts == checkable_widget.nb_conducted_asserts

    @pytest.mark.parametrize(
        "checks",
        [
            [no_param_check(failing=True)],
            [
                single_param_check(use_fingerprint=False, failing=True),
                single_param_check(use_fingerprint=True, failing=True),
            ],
            [multi_param_check(use_fingerprint=False, failing=True)],
            [single_param_check(use_fingerprint=True, failing=True)],
            [multi_param_check(use_fingerprint=True, failing=True)],
        ],
    )
    def test_failing_check_all_widgets(self, checks):
        check_registry = CheckRegistry()
        checkable_widget = mock_checkable_widget(
            check_registry, checks[0].function_to_check, checks
        )

        widgets_results = check_registry.check_all_widgets()
        for results in widgets_results.values():
            for result in results:
                assert isinstance(result, CheckResult)
                assert not (result.successful)

        assert len(checkable_widget.results) == len(checks)
        for result in checkable_widget.results:
            assert isinstance(result, CheckResult)
            assert not (result.successful)
