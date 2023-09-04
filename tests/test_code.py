from typing import List

import numpy as np
import pytest
from ipywidgets import fixed
from widget_code_input.utils import CodeValidationError

from scwidgets.check import Check, CheckRegistry, ChecksLog
from scwidgets.code import CodeDemo, CodeInput

from .test_check import multi_param_check, single_param_check


class TestCodeInput:
    # fmt: off
    @staticmethod
    def mock_function_1(x, y):
        """
        This is an example function.
        It adds two numbers.
        """
        if x > 0:
            return x + y
        else:
            return y

    @staticmethod
    def mock_function_2(x):
        """This is an example function. It adds two numbers."""
        return x

    @staticmethod
    def mock_function_3(x): return x

    @staticmethod
    def mock_function_4(x): """This returns identity"""; return x  # noqa: E702

    @staticmethod
    def mock_function_5(x):
        def x():
            return 5
        return x()

    @staticmethod
    def mock_function_6(x: List[int]) -> List[int]:
        return x
    # fmt: on

    def test_get_code(self):
        assert (
            CodeInput.get_code(self.mock_function_1)
            == "if x > 0:\n    return x + y\nelse:\n    return y\n"
        )
        assert CodeInput.get_code(self.mock_function_2) == "return x\n"
        assert CodeInput.get_code(self.mock_function_3) == "return x\n"
        assert CodeInput.get_code(self.mock_function_4) == "return x  # noqa: E702\n"
        assert (
            CodeInput.get_code(self.mock_function_5)
            == "def x():\n    return 5\nreturn x()\n"
        )
        assert CodeInput.get_code(self.mock_function_6) == "return x\n"
        with pytest.raises(
            ValueError,
            match=r"Did not find any def definition. .*",
        ):
            CodeInput.get_code(lambda x: x)


def get_code_demo(
    checks: List[Check],
    include_checks=True,
    include_params=True,
    tunable_params=False,
    update_mode="manual",
):
    # Important:
    # we take the the function_to_check from the first check as code input
    code_input = CodeInput(checks[0].function_to_check)
    if tunable_params:
        # convert single value arrays to tuples
        for value in checks[0].inputs_parameters[0].values():
            assert (
                np.prod(value.shape) == 1
            ), "conversion to tuple does not work properly for multidim array"
        parameters = {
            key: value.reshape(-1)[0]
            for key, value in checks[0].inputs_parameters[0].items()
        }
    else:
        # we convert the arguments to fixed one
        parameters = {
            key: fixed(value) for key, value in checks[0].inputs_parameters[0].items()
        }
    code_demo = CodeDemo(
        code=code_input,
        check_registry=CheckRegistry() if include_checks is True else None,
        parameters=parameters if include_params is True else None,
        update_mode=update_mode,
    )

    if include_checks is True:
        for check in checks:
            code_demo.add_check(
                check.asserts,
                check.inputs_parameters,
                check.outputs_references,
                check.fingerprint,
            )
    return code_demo


class TestCodeDemo:
    @pytest.mark.parametrize(
        "code_demo",
        [
            get_code_demo(
                [single_param_check(use_fingerprint=False, failing=False, buggy=False)]
            ),
            get_code_demo(
                [
                    single_param_check(
                        use_fingerprint=False, failing=False, buggy=False
                    ),
                    single_param_check(
                        use_fingerprint=True, failing=False, buggy=False
                    ),
                ]
            ),
            get_code_demo([multi_param_check(use_fingerprint=False, failing=False)]),
            get_code_demo([multi_param_check(use_fingerprint=True, failing=False)]),
        ],
    )
    def test_successful_check_widget(self, code_demo):
        result = code_demo.check()
        assert isinstance(result, ChecksLog)
        assert result.successful
        assert len(result.assert_results) == code_demo.nb_conducted_asserts

    @pytest.mark.parametrize(
        "code_demo",
        [
            get_code_demo(
                [single_param_check(use_fingerprint=False, failing=True, buggy=False)]
            ),
            get_code_demo(
                [
                    single_param_check(
                        use_fingerprint=False, failing=True, buggy=False
                    ),
                    single_param_check(use_fingerprint=True, failing=True, buggy=False),
                ]
            ),
            get_code_demo([multi_param_check(use_fingerprint=False, failing=True)]),
            get_code_demo([multi_param_check(use_fingerprint=True, failing=True)]),
        ],
    )
    def test_compute_and_set_references(self, code_demo):
        code_demo.compute_and_set_references()

        result = code_demo.check()
        assert isinstance(result, ChecksLog)
        assert result.successful
        assert len(result.assert_results) == code_demo.nb_conducted_asserts

    @pytest.mark.parametrize(
        "code_demo",
        [
            get_code_demo(
                [single_param_check(use_fingerprint=False, failing=False, buggy=False)]
            ),
            get_code_demo([multi_param_check(use_fingerprint=False, failing=False)]),
            get_code_demo(
                [single_param_check(use_fingerprint=False, failing=False, buggy=False)],
                include_params=True,
                tunable_params=True,
            ),
        ],
    )
    def test_run_code(self, code_demo):
        output = code_demo.run_code(**code_demo.panel_parameters)
        assert np.allclose((output,), code_demo.checks[0].outputs_references[0])

    @pytest.mark.parametrize(
        "code_demo",
        [
            get_code_demo(
                [single_param_check(use_fingerprint=False, failing=False, buggy=True)]
            ),
        ],
    )
    def test_erroneous_run_code(self, code_demo):
        with pytest.raises(
            CodeValidationError,
            match="NameError in code input: name 'bug' is not defined.*",
        ):
            code_demo.run_code(**code_demo.panel_parameters)
