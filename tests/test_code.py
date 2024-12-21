import os
from typing import Callable, List, Literal, Union

import matplotlib.pyplot as plt
import numpy as np
import pytest
from ipywidgets import fixed
from matplotlib.figure import Figure
from widget_code_input.utils import CodeValidationError

from scwidgets.check import Check, CheckRegistry, CheckResult
from scwidgets.code import CodeInput, ParametersPanel
from scwidgets.cue import CueObject
from scwidgets.exercise import CodeExercise, ExerciseRegistry

from .test_check import multi_param_check, single_param_check


class TestParametersPanel:

    def test_parameters(self):
        from ipywidgets import fixed

        panel = ParametersPanel(**{"x": (0, 1, 0.5), "y": (2, 3, 1), "z": fixed(5)})
        assert panel.parameters == {"x": 0.0, "y": 2, "z": 5}
        assert panel.panel_parameters == {"x": 0.0, "y": 2}


class TestCodeInput:
    # fmt: off
    @staticmethod
    def mock_function_0():
        return 0

    @staticmethod
    def mock_function_1(x: int, y: int = 5, z=lambda: 0):
        """
        This is an example function.
        It adds two numbers.
        """
        if x > 0:
            return x + y
        else:
            return y + z()

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

    @staticmethod
    def mock_function_7(x, **kwargs):
        return kwargs
    # fmt: on

    def test_get_function_paramaters(self):
        assert (
            CodeInput.get_function_parameters(self.mock_function_1)
            == "x: int, y: int = 5, z=lambda: 0"
        )
        assert CodeInput.get_function_parameters(self.mock_function_2) == "x"
        assert CodeInput.get_function_parameters(self.mock_function_6) == "x: List[int]"
        assert CodeInput.get_function_parameters(self.mock_function_7) == "x, **kwargs"

    def test_get_docstring(self):
        assert (
            CodeInput.get_docstring(self.mock_function_1)
            == "\nThis is an example function.\nIt adds two numbers.\n"
        )
        assert (
            CodeInput.get_docstring(self.mock_function_2)
            == "This is an example function. It adds two numbers."
        )
        assert (
            CodeInput.get_docstring(self.mock_function_2)
            == "This is an example function. It adds two numbers."
        )

    def test_get_function_body(self):
        assert (
            CodeInput.get_function_body(self.mock_function_1)
            == "if x > 0:\n    return x + y\nelse:\n    return y + z()"
        )
        assert CodeInput.get_function_body(self.mock_function_2) == "return x"
        assert CodeInput.get_function_body(self.mock_function_3) == "return x"
        assert (
            CodeInput.get_function_body(self.mock_function_4)
            == "return x  # noqa: E702"
        )
        assert (
            CodeInput.get_function_body(self.mock_function_5)
            == "def x():\n    return 5\nreturn x()"
        )
        assert CodeInput.get_function_body(self.mock_function_6) == "return x"
        with pytest.raises(
            ValueError,
            match=r"Did not find any def definition. .*",
        ):
            CodeInput.get_function_body(lambda x: x)

    def test_invalid_code_theme_raises_error(self):
        with pytest.raises(
            ValueError, match=r"Given code_theme 'invalid_theme' invalid.*"
        ):
            CodeInput(TestCodeInput.mock_function_1, code_theme="invalid_theme")

    def test_call(self):
        code = CodeInput(self.mock_function_1)
        assert code(1, 1) == 2
        assert code(0, 1) == 1

    def test_builtins(self):
        """Tests if import work when they are specified by builtins."""
        import numpy as np

        # to check if annotation works
        def function(arr: np.ndarray):
            return arr + builtins_variable  # noqa: F821

        code_input = CodeInput(function, builtins={"np": np, "builtins_variable": 0})
        code_input.unwrapped_function(np.array([0]))

        # check if builtins is overwritten,
        # the builtins_variable should not be there anymore afterwards
        code_input.builtins = {"np": np}
        with pytest.raises(
            NameError, match=r".*name 'builtins_variable' is not defined.*"
        ):
            code_input.unwrapped_function(np.array([0]))


def get_code_exercise(
    checks: List[Check],
    code: Union[None, Literal["from_first_check"], Callable] = "from_first_check",
    include_checks=True,
    include_params=True,
    tunable_params=False,
    update_func_argless=False,
    update_mode="manual",
):
    """
    :param code: "from_first_check" uses the `function_to_check` from the first
        check for the construction of a code input
    """
    # Important:
    # we take the the function_to_check from the first check as code input
    if code == "from_first_check":
        if len(checks) == 0:
            raise ValueError(
                "For option 'from_first_check' either nonempty "
                "checks must given or code"
            )
        code_input = CodeInput(checks[0].function_to_check)
    elif code is None:
        code_input = None
    else:
        code_input = CodeInput(code)

    if len(checks) > 0 and tunable_params:
        # convert single value arrays to tuples
        for value in checks[0].inputs_parameters[0].values():
            assert (
                np.prod(value.shape) == 1
            ), "conversion to tuple does not work properly for multidim array"
        parameters = {
            key: value.reshape(-1)[0]
            for key, value in checks[0].inputs_parameters[0].items()
        }
    elif len(checks) > 0:
        # we convert the arguments to fixed one
        parameters = {
            key: fixed(value) for key, value in checks[0].inputs_parameters[0].items()
        }
    elif tunable_params:
        parameters = {"x": (2, 5, 1)}
    else:
        parameters = None

    if update_func_argless:

        def update_print():
            if code_input is None:
                output = code_ex.parameters
            else:
                output = code_ex.run_code(**code_ex.parameters)
            code_ex.output.object = f"Output:\n{output}"

    else:

        def update_print(code_ex: CodeExercise):
            if code_input is None:
                output = code_ex.parameters
            else:
                output = code_ex.run_code(**code_ex.parameters)
            code_ex.output.object = f"Output:\n{output}"

    code_ex = CodeExercise(
        code=code_input,
        check_registry=CheckRegistry() if include_checks is True else None,
        parameters=parameters if include_params is True else None,
        outputs=[CueObject("Not initialized")],
        update=update_print,
        update_mode=update_mode,
    )

    if include_checks is True:
        for check in checks:
            code_ex.add_check(
                check.asserts,
                check.inputs_parameters,
                check.outputs_references,
                check.fingerprint,
            )
    return code_ex


class TestCodeExercise:
    @pytest.mark.parametrize(
        "code_ex",
        [
            get_code_exercise(
                [single_param_check(use_fingerprint=False, failing=False, buggy=False)],
            )
        ],
    )
    def test_parameters_panel(self, code_ex):
        assert code_ex.parameters_panel.parameters == code_ex.parameters

    @pytest.mark.parametrize(
        "code_ex",
        [
            get_code_exercise(
                [single_param_check(use_fingerprint=False, failing=False, buggy=False)]
            ),
            get_code_exercise(
                [
                    single_param_check(
                        use_fingerprint=False, failing=False, buggy=False
                    ),
                    single_param_check(
                        use_fingerprint=True, failing=False, buggy=False
                    ),
                ]
            ),
            get_code_exercise(
                [multi_param_check(use_fingerprint=False, failing=False)]
            ),
            get_code_exercise([multi_param_check(use_fingerprint=True, failing=False)]),
        ],
    )
    def test_successful_check_widget(self, code_ex):
        results = code_ex.check()
        nb_assert_results = 0
        for result in results:
            assert isinstance(result, CheckResult)
            assert result.successful
            nb_assert_results += len(result.assert_results)
        assert nb_assert_results == code_ex.nb_conducted_asserts

    @pytest.mark.parametrize(
        "code_ex",
        [
            get_code_exercise(
                [single_param_check(use_fingerprint=False, failing=True, buggy=False)]
            ),
            get_code_exercise(
                [
                    single_param_check(
                        use_fingerprint=False, failing=True, buggy=False
                    ),
                    single_param_check(use_fingerprint=True, failing=True, buggy=False),
                ]
            ),
            get_code_exercise([multi_param_check(use_fingerprint=False, failing=True)]),
            get_code_exercise([multi_param_check(use_fingerprint=True, failing=True)]),
        ],
    )
    def test_compute_and_set_references(self, code_ex):
        code_ex.compute_and_set_references()

        results = code_ex.check()
        nb_assert_results = 0
        for result in results:
            assert isinstance(result, CheckResult)
            assert result.successful
            nb_assert_results += len(result.assert_results)
        assert nb_assert_results == code_ex.nb_conducted_asserts

    @pytest.mark.parametrize(
        "code_ex",
        [
            get_code_exercise(
                [single_param_check(use_fingerprint=False, failing=False, buggy=False)],
            ),
            get_code_exercise(
                [multi_param_check(use_fingerprint=False, failing=False)]
            ),
            get_code_exercise(
                [single_param_check(use_fingerprint=False, failing=False, buggy=False)],
                include_params=True,
                tunable_params=True,
            ),
        ],
    )
    def test_run_code(self, code_ex):
        output = code_ex.run_code(**code_ex.parameters)
        assert np.allclose((output,), code_ex.checks[0].outputs_references[0])

    @pytest.mark.parametrize(
        "code_ex",
        [
            get_code_exercise(
                [single_param_check(use_fingerprint=False, failing=False, buggy=True)]
            ),
        ],
    )
    def test_erroneous_run_code(self, code_ex):
        with pytest.raises(
            CodeValidationError,
            match="name 'bug' is not defined.*",
        ):
            code_ex.run_code(**code_ex.parameters)

    @pytest.mark.parametrize(
        "function",
        [
            None,
            TestCodeInput.mock_function_1,
        ],
    )
    def test_save_registry(self, function):
        """
        Verifies that the CodeExercise works with an answer_registry.
        """
        name = "test_save_registry-student_name"
        try:

            def print_success(code_ex: CodeExercise | None):
                code_ex.output.object = "Success"

            cue_output = CueObject("Not initialized")
            exercise_registry = ExerciseRegistry()

            code_ex = CodeExercise(
                code=function,
                parameters={"parameter": fixed(5)},
                exercise_registry=exercise_registry,
                key="test_save_registry_ex",
                outputs=[cue_output],
                update=print_success,
            )

            exercise_registry._student_name_text.value = name
            exercise_registry.create_new_file_from_dropdown()
            code_ex._save_button.click()
        finally:
            file_name = f"{name}.json"
            if os.path.exists(file_name):
                os.remove(file_name)

    @pytest.mark.parametrize(
        "code_ex",
        [
            get_code_exercise(
                [],
                code=TestCodeInput.mock_function_0,
                update_func_argless=False,
            ),
            get_code_exercise(
                [],
                code=TestCodeInput.mock_function_0,
                update_func_argless=True,
            ),
        ],
    )
    def test_run_update(self, code_ex):
        """Test run_update"""
        import io
        from contextlib import redirect_stdout

        buffer = io.StringIO()
        code_ex._output = redirect_stdout(buffer)

        def mock_clear_output(wait):
            pass

        code_ex._output.clear_output = mock_clear_output

        # Be aware that the raised error is captured in the code_ex._output
        # To debug failures in the test you have to manually run it in debug
        # mode and execute `code_ex._update_button.click()` Redirecting stderr
        # does des not work
        code_ex.run_update()
        assert "Output:\n0" in buffer.getvalue()

    def test_invalid_update_func(self):
        """Test run_update for wrong input"""

        def failing_update(a, b):
            pass

        with pytest.raises(
            ValueError, match=r".*The given update function has 2 parameters .*"
        ):
            CodeExercise(
                code=TestCodeInput.mock_function_0,
                update=failing_update,
            )

    def test_figure(self):
        """Test figure"""

        code_ex = CodeExercise(outputs=plt.figure())
        assert isinstance(code_ex.figure, Figure)
        assert code_ex.output.figure is code_ex.figure
        assert code_ex.outputs[0] is code_ex.output

    def test_consrtuction_with_registries(self):
        """Because the exercise key is used for the `ExerciseRegistry` and the
        `CheckRegistry` we need to ensure the `CodeExercise` can be run with
        each individual one and both"""
        CodeExercise(
            key="some_key",
            check_registry=CheckRegistry(),
        )
        CodeExercise(
            key="some_key",
            exercise_registry=ExerciseRegistry(),
        )
        CodeExercise(
            key="some_key",
            check_registry=CheckRegistry(),
            exercise_registry=ExerciseRegistry(),
        )
