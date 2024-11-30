import inspect
import re
import sys
import traceback
import types
import warnings
from functools import wraps
from typing import List, Optional

from widget_code_input import WidgetCodeInput
from widget_code_input.utils import (
    CodeValidationError,
    format_syntax_error_msg,
    is_valid_variable_name,
)

from ..check import Check


class CodeInput(WidgetCodeInput):
    """
    Small wrapper around WidgetCodeInput that controls the output
    """

    valid_code_themes = ["nord", "solarizedLight", "basicLight"]

    def __init__(
        self,
        function: Optional[types.FunctionType] = None,
        function_name: Optional[str] = None,
        function_parameters: Optional[str] = None,
        docstring: Optional[str] = None,
        function_body: Optional[str] = None,
        code_theme: str = "basicLight",
    ):
        if function is not None:
            function_name = (
                function.__name__ if function_name is None else function_name
            )
            function_parameters = (
                ", ".join(inspect.getfullargspec(function).args)
                if function_parameters is None
                else function_parameters
            )
            docstring = inspect.getdoc(function) if docstring is None else docstring
            function_body = (
                self.get_code(function) if function_body is None else function_body
            )

        # default parameters from WidgetCodeInput
        if function_name is None:
            raise ValueError("function_name must be given if no function is given.")
        function_parameters = "" if function_parameters is None else function_parameters
        docstring = "\n" if docstring is None else docstring
        function_body = "" if function_body is None else function_body
        super().__init__(
            function_name, function_parameters, docstring, function_body, code_theme
        )

        # this list is retrieved from
        # https://github.com/osscar-org/widget-code-input/blob/eb10ca0baee65dd3bf62c9ec5d9cb2f152932ff5/js/widget.js#L249-L253
        if code_theme not in CodeInput.valid_code_themes:
            raise ValueError(
                f"Given code_theme {code_theme!r} invalid. Please use one of "
                f"the values {CodeInput.valid_code_themes}"
            )

    @property
    def function(self) -> types.FunctionType:
        """
        Return the compiled function object.

        This can be assigned to a variable and then called, for instance::

          func = widget.wrapped_function # This can raise a SyntaxError
          retval = func(parameters)

        :raise SyntaxError: if the function code has syntax errors (or if
          the function name is not a valid identifier)
        """
        return inspect.unwrap(self.wrapped_function)

    def __call__(self, *args, **kwargs) -> Check.FunOutParamsT:
        """Calls the wrapped function"""
        return self.wrapped_function(*args, **kwargs)

    def compatible_with_signature(self, parameters: List[str]) -> str:
        """
        This function checks if the arguments are compatible with the function signature
        and returns a nonempty message if this is not the case explaining what the issue
        """
        if "**" in self.function_parameters:
            # function has keyword arguments so it is compatible
            return ""
        for parameter_name in inspect.signature(self.function).parameters.keys():
            if not (parameter_name in parameters):
                return (
                    f"The input parameter {parameter_name} is not compatible with "
                    "the function code."
                )
        return ""

    @property
    def function_parameters_name(self) -> List[str]:
        return self.function_parameters.replace(",", "").split(" ")

    @staticmethod
    def get_code(func: types.FunctionType) -> str:
        source_lines, _ = inspect.getsourcelines(func)

        found_def = False
        def_index = 0
        for i, line in enumerate(source_lines):
            if "def" in line:
                found_def = True
                def_index = i
                break
        if not (found_def):
            raise ValueError(
                "Did not find any def definition. Only functions with a "
                "defition are supported"
            )

        # Remove function definition
        line = re.sub(r"^\s*def\s+[^\(]*\(.*\)(.*?):\n?", "", line)
        source_lines[def_index] = line
        # Remove any potential wrappers
        source_lines = source_lines[i:]

        source = "".join(source_lines)
        # Remove docstrings
        source = re.sub(
            r"((.*?)\'\'\'(.*?)\'\'\'.*?[;\n]|(.*?)\"\"\"(.*?)\"\"\"(.*?)[;\n])",
            "",
            source,
            flags=re.DOTALL,
        )

        # Adjust indentation
        lines = source.split("\n")
        if lines:
            leading_indent = len(lines[0]) - len(lines[0].lstrip())
            source = "\n".join(
                line[leading_indent:] if line.strip() else "" for line in lines
            )

        return source

    @property
    def wrapped_function(self) -> types.FunctionType:
        """
        Return the compiled function object wrapped by an try-catch block
        raising a `CodeValidationError`.

        This can be assigned to a variable and then called, for instance::

          func = widget.wrapped_function # This can raise a SyntaxError
          retval = func(parameters)

        :raise SyntaxError: if the function code has syntax errors (or if
          the function name is not a valid identifier)
        """
        globals_dict = {
            "__builtins__": globals()["__builtins__"],
            "__name__": "__main__",
            "__doc__": None,
            "__package__": None,
        }

        if not is_valid_variable_name(self.function_name):
            raise SyntaxError("Invalid function name '{}'".format(self.function_name))

        # Optionally one could do a ast.parse here already, to check syntax
        # before execution
        try:
            exec(
                compile(self.full_function_code, __name__, "exec", dont_inherit=True),
                globals_dict,
            )
        except SyntaxError as exc:
            raise CodeValidationError(
                format_syntax_error_msg(exc), orig_exc=exc
            ) from exc

        function_object = globals_dict[self.function_name]

        def catch_exceptions(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                """Wrap and check exceptions to return a longer and clearer
                exception."""

                try:
                    return func(*args, **kwargs)
                except Exception as exc:
                    err_msg = format_generic_error_msg(exc, code_widget=self)
                    raise CodeValidationError(err_msg, orig_exc=exc) from exc

            return wrapper

        return catch_exceptions(function_object)


# Temporary fix until https://github.com/osscar-org/widget-code-input/pull/26
# is merged
def format_generic_error_msg(exc, code_widget):
    """
    Return a string reproducing the traceback of a typical error.
    This includes line numbers, as well as neighboring lines.

    It will require also the code_widget instance, to get the actual source code.

    :note: this must be called from withou the exception, as it will get the
        current traceback state.

    :param exc: The exception that is being processed.
    :param code_widget: the instance of the code widget with the code that
        raised the exception.
    """
    error_class, _, tb = sys.exc_info()
    frame_summaries = traceback.extract_tb(tb)
    # The correct frame summary corresponding to widget_code_intput is not
    # always at the end therefore we loop through all of them
    wci_frame_summary = None
    for frame_summary in frame_summaries:
        if frame_summary.filename == "widget_code_input":
            wci_frame_summary = frame_summary
    if wci_frame_summary is None:
        warnings.warn(
            "Could not find traceback frame corresponding to "
            "widget_code_input, we output whole error message.",
            stacklevel=2,
        )

        return exc
    line_number = wci_frame_summary[1]
    code_lines = code_widget.full_function_code.splitlines()

    err_msg = f"{error_class.__name__} in code input: {str(exc)}\n"
    if line_number > 2:
        err_msg += f"     {line_number - 2:4d} {code_lines[line_number - 3]}\n"
    if line_number > 1:
        err_msg += f"     {line_number - 1:4d} {code_lines[line_number - 2]}\n"
    err_msg += f"---> {line_number:4d} {code_lines[line_number - 1]}\n"
    if line_number < len(code_lines):
        err_msg += f"     {line_number + 1:4d} {code_lines[line_number]}\n"
    if line_number < len(code_lines) - 1:
        err_msg += f"     {line_number + 2:4d} {code_lines[line_number + 1]}\n"

    return err_msg
