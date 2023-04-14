import functools
import ipywidgets

"""
input_parameters = [{'a': 1, 'b':2}] : list of dicts, each dict one corresponds to one check with current configuration, arguments are only kwargs
args is reserved for
output_parameters = [output_for_input1, output_for_input2]
fingerprint(output1):
    return output1
"""

class CheckRegistry:
    def __init__(self):
        self._checks = {}

    def register_checks(self, widget):
        """initialize checks, if checks exist then it resets them"""
        self._checks[widget] = []

    def add_check(self, widget, inputs_parameters, reference_outputs=None, process_output=None, custom_assert=None, equal=None):
        check = Check(widget, inputs_parameters, reference_outputs, process_output, custom_assert, equal)
        self._checks[widget].append(check)

    def compute_and_set_reference_outputs(self, widget, change=None):
        for check in self._checks[widget]:
            check.compute_and_set_reference_outputs()

    def print_reference_outputs(self, widget, fingerprint=None):
        if fingerprint is None:
            fingerprint = lambda x: x
        for i, check in enumerate(self._checks[widget]):
            print(f"Check {i}:\n{[fingerprint(reference_output) for reference_output in check.compute_reference_outputs()]}")

    def check_widget_outputs(self, widget, change=None):
        check_successes = []
        for check in self._checks[widget]:
            check_successes.append( check.check_widget_outputs() )
        return all(check_successes)

class CheckRegistryDummy:
    def __init__(self):
        self._checks = {}

    def register_checks(self, widget):
        """initialize checks, if checks exist then it resets them"""
        self._checks[widget] = []

    def check_widget_outputs(self, widget, change=None):
        return True



class Check:
    """
    A check is collection of asserts with the same configuration.

    The widget must have a `compute_output` function with all arguments named.

    inputs_parameters: list of dict,
        the dict contains the named arguments used with compute_output
    reference_outputs: list of outputs,
        each entry is one output of the the compute_output function of the widget
    process_output : function,
        can raise assert errors
    custom_assert : function
        can raise assert errors
    equal : function
        returns boolean


    workflow of a check for each input:
        output = widget.compute_output(**input)
        output = process_output(output) -> can raise assertion errors [if not None]
        if process_output is None:
            type assert for output
            len/shape assert for output
        custom_assert(output, reference_output) -> can raise assertion errors     [if not None]
        equal(output, reference_output) -> can raise assertion errors  [if not None]

    """
    def __init__(self, widget, inputs_parameters, reference_outputs=None, process_output=None, custom_assert=None, equal=None):
        if not(hasattr(widget, "compute_output")):
            raise ValueError("Widget does not have function with name 'compute_and_set_reference_outputs', which is needed to produce refeference outputs.")

        if reference_outputs is not None and len(reference_outputs) != len(inputs_parameters):
            raise ValueError(f"Number of inputs and outputs must be the same: len(inputs_parameters) != len(reference_outputs) ({len(inputs_parameters)} != {len(reference_outputs)})")

        self._widget = widget
        self._inputs_parameters = inputs_parameters
        self._reference_outputs = reference_outputs
        self._process_output = process_output
        self._custom_assert = custom_assert
        self._equal = equal

    def compute_and_set_reference_outputs(self):
        self._reference_outputs = self.compute_reference_outputs()

    def compute_reference_outputs(self):
        reference_outputs = []
        for input_parameters in self._inputs_parameters:
            try:
                reference_output = self._widget.compute_output(**input_parameters)
            except Exception as e:
                raise e
            reference_outputs.append(reference_output)
        return reference_outputs

    def check_widget_outputs(self):
        if self._reference_outputs is None:
            raise ValueError("Reference outputs are None. Please first run comppute_and_set_reference_outputs or specify reference_outputs on initialization.")
        assert len(self._inputs_parameters) == len(self._reference_outputs), "number of inputs and reference outputs mismatching. Something went wrong in setting reference outputs"
        for i in range(len(self._reference_outputs)):
            output = self._widget.compute_output(**self._inputs_parameters[i])

            if self._process_output is not None:
                try:
                    output = self._process_output(output)
                except AssertionError as e:
                    print(f"Assert failed: {e}")
                    return False

            if self._process_output is None:
                if not(isinstance(output, type(self._reference_outputs[i]))):
                    print(f"TypeAssert failed: Expected type {type(self._reference_outputs[i])} but got {type(output)}.")
                    return False
                elif hasattr(self._reference_outputs[i], "shape") and (output.shape != self._reference_outputs[i].shape):
                    print(f"ShapeAssert failed: Expected shape {self._reference_outputs[i].shape} but got {output.shape}.")
                    return False
                elif hasattr(self._reference_outputs[i], "__len__") and (len(output) != len(self._reference_outputs[i])):
                    print(f"LenAssert failed: Expected len {self._reference_outputs[i]} but got {len(output)}.")
                    return False

            if self._custom_assert is not None:
                try:
                    self._custom_assert(output, self._reference_outputs[i])
                except AssertionError as e:
                    print(f"Assert failed: {e}")
                    return False

            if (self._equal is not None) and \
                    not(self._equal(output, self._reference_outputs[i])):
                print(f"EqualAssert failed: Expected {self._reference_outputs[i]} but got {output}.")
                return False
        return True
