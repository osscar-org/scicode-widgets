import inspect
import re
from typing import Callable

from widget_code_input import WidgetCodeInput

from ..check import Check


class CodeInput(WidgetCodeInput):
    """
    Small wrapper around WidgetCodeInput that controls the output
    """

    def __init__(
        self,
        function=None,
        function_name=None,
        function_parameters=None,
        docstring=None,
        function_body=None,
        code_theme="north",
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

    def run(self, *args, **kwargs) -> Check.FunOutParamsT:
        return self.get_function_object()(*args, **kwargs)

    @staticmethod
    def get_code(func: Callable):
        source_lines, _ = inspect.getsourcelines(func)
        for line in source_lines:
            if "lambda" in line:
                raise ValueError("Lambda functions are not supported.")

        source = "".join(source_lines)

        # Remove function definition
        source = re.sub(r"^\s*def\s+[^\(]*\(.*\):.*?[;\n]", "", source)
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
