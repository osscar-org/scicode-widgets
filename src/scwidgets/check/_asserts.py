import functools
from collections import abc
from typing import Iterable, Union

import numpy as np

from ._check import AssertResult, Check

AssertFunctionOutputT = Union[str, AssertResult]


def assert_shape(
    output_parameters: Check.FunOutParamsT,
    output_references: Check.FunOutParamsT,
    parameters_to_check: Union[Iterable[int], str] = "auto",
) -> AssertResult:
    assert len(output_parameters) == len(
        output_references
    ), "output_parameters and output_references have to have the same length"

    parameter_indices: Iterable[int]
    if isinstance(parameters_to_check, str):
        if parameters_to_check == "auto":
            parameter_indices = []
            for i in range(len(output_references)):
                if hasattr(output_references[i], "shape"):
                    parameter_indices.append(i)
        elif parameters_to_check == "all":
            parameter_indices = range(len(output_parameters))
        else:
            raise ValueError(
                f'Got parameters_to_check="{parameters_to_check}" but only "all" '
                ' and "auto" are accepted as string'
            )
    elif isinstance(parameters_to_check, abc.Iterable):
        parameter_indices = parameters_to_check  # type: ignore[assignment]
    else:
        raise TypeError(
            "Only str and Iterable are accepted for parameters_to_check, "
            f"but got type {type(parameters_to_check)}."
        )

    failed_parameter_indices = []
    failed_parameter_values = []
    messages = []
    for i in parameter_indices:
        if output_parameters[i].shape != output_references[i].shape:
            message = (
                f"Expected shape {output_references[i].shape})"
                f"but got {output_parameters[i].shape}."
            )
            failed_parameter_indices.append(i)
            failed_parameter_values.append(output_parameters[i])
            messages.append(message)

    return AssertResult(
        assert_name="assert_shape",
        parameter_indices=failed_parameter_indices,
        parameter_values=failed_parameter_values,
        messages=messages,
    )


def assert_numpy_allclose(
    output_parameters: Check.FunOutParamsT,
    output_references: Check.FunOutParamsT,
    parameters_to_check: Union[Iterable[int], str] = "auto",
    rtol=1e-05,
    atol=1e-08,
    equal_nan=False,
) -> AssertResult:
    assert len(output_parameters) == len(
        output_references
    ), "output_parameters and output_references have to have the same length"

    parameter_indices: Iterable[int]
    if isinstance(parameters_to_check, str):
        if parameters_to_check == "auto":
            parameter_indices = []
            for i in range(len(output_references)):
                try:
                    np.allclose(output_references[i], output_references[i])
                    parameter_indices.append(i)
                except Exception:
                    pass
        elif parameters_to_check == "all":
            parameter_indices = range(len(output_parameters))
        else:
            raise ValueError(
                f'Got parameters_to_check="{parameters_to_check}" but only "all" '
                ' and "auto" are accepted as string'
            )
    elif isinstance(parameters_to_check, abc.Iterable):
        parameter_indices = parameters_to_check  # type: ignore[assignment]
    else:
        raise TypeError(
            "Only str and Iterable are accepted for parameters_to_check, "
            f"but got type {type(parameters_to_check)}."
        )

    failed_parameter_indices = []
    failed_parameter_values = []
    messages = []
    for i in parameter_indices:
        is_allclose = np.allclose(
            output_parameters[i],
            output_references[i],
            atol=atol,
            rtol=rtol,
            equal_nan=equal_nan,
        )

        if not (is_allclose):
            diff = np.abs(
                np.asarray(output_parameters[i]) - np.asarray(output_references[i])
            )
            abs_diff = np.sum(diff)
            rel_diff = np.sum(diff / np.abs(output_references[i]))

            message = (
                f"Output is not close to reference absolute difference "
                f"is {abs_diff}, relative difference is {rel_diff}."
            )
            failed_parameter_indices.append(i)
            failed_parameter_values.append(output_parameters[i])
            messages.append(message)

    return AssertResult(
        assert_name="assert_numpy_allclose",
        parameter_indices=failed_parameter_indices,
        parameter_values=failed_parameter_values,
        messages=messages,
    )


def assert_type(
    output_parameters: Check.FunOutParamsT,
    output_references: Check.FunOutParamsT,
    parameters_to_check: Union[Iterable[int], str] = "all",
) -> AssertResult:
    assert len(output_parameters) == len(
        output_references
    ), "output_parameters and output_references have to have the same length"

    parameter_indices: Iterable[int]
    if isinstance(parameters_to_check, str):
        if parameters_to_check == "all":
            parameter_indices = range(len(output_parameters))
        else:
            raise ValueError(
                f'Got parameters_to_check="{parameters_to_check}" but only "all" '
                "is accepted as string"
            )
    elif isinstance(parameters_to_check, abc.Iterable):
        parameter_indices = parameters_to_check  # type: ignore[assignment]
    else:
        raise TypeError(
            "Only str and Iterable are accepted for parameters_to_check, "
            f"but got type {type(parameters_to_check)}."
        )

    failed_parameter_indices = []
    failed_parameter_values = []
    messages = []
    for i in parameter_indices:
        if not (isinstance(output_parameters[i], type(output_references[i]))):
            message = (
                f"Expected type {type(output_references[i])} "
                f"but got {type(output_parameters[i])}."
            )
            failed_parameter_indices.append(i)
            failed_parameter_values.append(output_parameters[i])
            messages.append(message)
    return AssertResult(
        assert_name="assert_type",
        parameter_indices=failed_parameter_indices,
        parameter_values=failed_parameter_values,
        messages=messages,
    )


def assert_numpy_sub_dtype(
    output_parameters: Union[Check.FunOutParamsT, tuple[Check.FingerprintT]],
    numpy_type: Union[np.dtype, type],
    parameters_to_check: Union[Iterable[int], str] = "all",
) -> AssertResult:
    if parameters_to_check == "all":
        parameter_indices = range(len(output_parameters))
    elif isinstance(parameters_to_check, abc.Iterable):
        parameter_indices = parameters_to_check  # type: ignore[assignment]
    else:
        raise TypeError(
            "Only str and Iterable are accepted for parameters_to_check, "
            f"but got type {type(parameters_to_check)}."
        )

    failed_parameter_indices = []
    failed_parameter_values = []
    messages = []
    for i in parameter_indices:
        if not (isinstance(output_parameters[i], np.ndarray)):
            failed_parameter_indices.append(i)
            failed_parameter_values.append(output_parameters[i])
            message = (
                f"Output expected to be numpy array "
                f"but got {type(output_parameters[i])}."
            )
            messages.append(message)
        if not (np.issubdtype(output_parameters[i].dtype, numpy_type)):
            if isinstance(numpy_type, np.dtype):
                type_name = numpy_type.type.__name__
            else:
                type_name = numpy_type.__name__
            failed_parameter_indices.append(i)
            failed_parameter_values.append(output_parameters[i])
            message = (
                f"Output expected to be sub dtype "
                f"numpy.{type_name} but got "
                f"numpy.{output_parameters[i].dtype.type.__name__}."
            )
            messages.append(message)
    if isinstance(numpy_type, np.dtype):
        type_name = numpy_type.type.__name__
    else:
        type_name = numpy_type.__name__
    return AssertResult(
        assert_name=f"assert_numpy_{type_name}_sub_dtype",
        parameter_indices=failed_parameter_indices,
        parameter_values=failed_parameter_values,
        messages=messages,
    )


assert_numpy_floating_sub_dtype = functools.partial(
    assert_numpy_sub_dtype, numpy_type=np.floating
)
