from termcolor import colored


class Printer:
    # move to output
    @staticmethod
    def print_error_message(message: str):
        print(colored(message, "red", attrs=["bold"]))

    @staticmethod
    def print_success_message(message: str):
        print(colored(message, "green", attrs=["bold"]))

    @staticmethod
    def print_info_message(message: str):
        print(colored(message, "blue", attrs=["bold"]))
