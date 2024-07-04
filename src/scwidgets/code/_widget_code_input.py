import inspect
import re
import types
from typing import List, Optional

from widget_code_input import WidgetCodeInput

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
        Returns the unwrapped function object
        """
        return inspect.unwrap(self.get_function_object())

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

    def run(self, *args, **kwargs) -> Check.FunOutParamsT:
        return self.get_function_object()(*args, **kwargs)

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
