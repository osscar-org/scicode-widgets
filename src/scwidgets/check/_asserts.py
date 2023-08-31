import functools
from collections import abc
from typing import Iterable, TypeVar, Union

import numpy as np

from ._check import Check

AssertResultT = TypeVar("AssertResultT", bound="str")


def assert_shape(
    output_parameters: Check.FunOutParamsT,
    output_references: Check.FunOutParamsT,
    parameters_to_check: Union[Iterable[int], str] = "auto",
) -> str:
    assert len(output_parameters) == len(
        output_references
    ), "output_parameters and output_references have to have the same length"

    parameter_indices: Iterable[int]
    if isinstance(parameters_to_check, str):
        if parameters_to_check == "auto":
            parameter_indices = []
            for i in range(len(output_parameters)):
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

    for i in parameter_indices:
        if output_parameters[i].shape != output_references[i].shape:
            return (
                f"For parameter {i} expected shape {output_references[i].shape} "
                f"but got {output_parameters[i].shape}."
            )
    return ""


def assert_numpy_allclose(
    output_parameters: Check.FunOutParamsT,
    output_references: Check.FunOutParamsT,
    parameters_to_check: Union[Iterable[int], str] = "auto",
    rtol=1e-05,
    atol=1e-08,
    equal_nan=False,
) -> str:
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
            return (
                f"Output parameter {i} is not close to reference absolute difference "
                f"is {abs_diff}, relative difference is {rel_diff}."
            )
    return ""


def assert_type(
    output_parameters: Check.FunOutParamsT,
    output_references: Check.FunOutParamsT,
    parameters_to_check: Union[Iterable[int], str] = "all",
) -> str:
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

    for i in parameter_indices:
        if not (isinstance(output_parameters[i], type(output_references[i]))):
            return (
                f"Expected type {type(output_references[i])} "
                f"but got {type(output_parameters[i])}."
            )
    return ""


def assert_numpy_sub_dtype(
    output_parameters: Union[Check.FunOutParamsT, tuple[Check.FingerprintT]],
    numpy_type: Union[np.dtype, type],
    parameters_to_check: Union[Iterable[int], str] = "all",
) -> str:
    if parameters_to_check == "all":
        parameter_indices = range(len(output_parameters))
    elif isinstance(parameters_to_check, abc.Iterable):
        parameter_indices = parameters_to_check  # type: ignore[assignment]
    else:
        raise TypeError(
            "Only str and Iterable are accepted for parameters_to_check, "
            f"but got type {type(parameters_to_check)}."
        )

    for i in parameter_indices:
        if not (isinstance(output_parameters[i], np.ndarray)):
            return (
                f"Output parameter {i} expected to be numpy array "
                f"but got {type(output_parameters[i])}."
            )
        if not (np.issubdtype(output_parameters[i].dtype, numpy_type)):
            if isinstance(numpy_type, np.dtype):
                type_name = numpy_type.type.__name__
            else:
                type_name = numpy_type.__name__
            return (
                f"Output parameter {i} expected to be sub dtype "
                f"numpy.{type_name} but got "
                f"numpy.{output_parameters[i].dtype.type.__name__}."
            )
    return ""


assert_numpy_floating_sub_dtype = functools.partial(
    assert_numpy_sub_dtype, numpy_type=np.floating
)
