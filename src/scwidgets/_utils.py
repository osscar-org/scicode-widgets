import re

from termcolor import colored


class Printer:
    # TODO rename to Formatter
    #      remove print funcs
    LINE_LENGTH = 120
    INFO_COLOR = "blue"
    ERROR_COLOR = "red"
    SUCCESS_COLOR = "green"

    @staticmethod
    def format_title_message(message: str) -> str:
        return message.center(Printer.LINE_LENGTH - len(message) // 2, "-")

    @staticmethod
    def break_lines(message: str) -> str:
        return "\n ".join(re.findall(r".{1," + str(Printer.LINE_LENGTH) + "}", message))

    @staticmethod
    def color_error_message(message: str) -> str:
        return colored(message, Printer.ERROR_COLOR, attrs=["bold"])

    @staticmethod
    def print_error_message(message: str):
        print(Printer.color_error_message(message))

    @staticmethod
    def color_success_message(message: str) -> str:
        return colored(message, Printer.SUCCESS_COLOR, attrs=["bold"])

    @staticmethod
    def print_success_message(message: str):
        print(Printer.color_success_message(message))

    @staticmethod
    def color_info_message(message: str):
        return colored(message, Printer.INFO_COLOR, attrs=["bold"])

    @staticmethod
    def print_info_message(message: str):
        print(Printer.color_info_message(message))

    @staticmethod
    def color_assert_failed(message: str) -> str:
        return colored(message, "light_" + Printer.ERROR_COLOR)

    @staticmethod
    def color_assert_info(message: str) -> str:
        return colored(message, "light_" + Printer.INFO_COLOR)

    @staticmethod
    def color_assert_success(message: str) -> str:
        return colored(message, "light_" + Printer.SUCCESS_COLOR)
