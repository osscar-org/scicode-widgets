# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: -all
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.15.0
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# +
import os
import sys

sys.path.insert(0, os.path.abspath("../.."))
from tests.test_check import single_param_check  # noqa: E402
from tests.test_code import get_code_exercise  # noqa: E402

# -


# Test 1:
# -------
# Test if CodeExercise shows correct output

# Test 1.1
get_code_exercise(
    [single_param_check(use_fingerprint=False, failing=False, buggy=False)],
    include_checks=True,
    include_params=True,
    tunable_params=False,
    update_mode="manual",
)

# Test 1.2
get_code_exercise(
    [single_param_check(use_fingerprint=False, failing=True, buggy=False)],
    include_checks=True,
    include_params=True,
    tunable_params=False,
    update_mode="manual",
)

# Test 1.3
get_code_exercise(
    [single_param_check(use_fingerprint=False, failing=False, buggy=True)],
    include_checks=True,
    include_params=True,
    tunable_params=False,
    update_mode="manual",
)

# Test 1.4
get_code_exercise(
    [single_param_check(use_fingerprint=False, failing=False, buggy=False)],
    include_checks=True,
    include_params=True,
    tunable_params=True,
    update_mode="manual",
)

# Test 1.5
get_code_exercise(
    [single_param_check(use_fingerprint=False, failing=False, buggy=False)],
    include_checks=True,
    include_params=True,
    tunable_params=True,
    update_mode="continuous",
)

# Test 1.6
get_code_exercise(
    [single_param_check(use_fingerprint=False, failing=False, buggy=False)],
    include_checks=True,
    include_params=True,
    tunable_params=True,
    update_mode="release",
)


# Test 2:
# -------
# Test if CodeExercise works correct for only update


# +
# Test 2.1
# Test if update button is shown even if params are None
def function_to_check():
    print("SomeText")
    return 5


get_code_exercise(
    [],
    code=function_to_check,
    include_checks=False,
    include_params=False,
    tunable_params=False,
    update_mode="release",
)
# -

# Test 2.2
# TODO
# get_code_exercise(
#    [single_param_check(use_fingerprint=False, failing=True, buggy=False)],
#    include_checks=False,
#    include_params=True,
#    tunable_params=True,
# )

# Test 2.3
# TODO
# get_code_exercise(
#    [single_param_check(use_fingerprint=True, failing=True, buggy=False)],
#    include_checks=False,
#    include_params=True,
#    tunable_params=True,
# )


# Test 3:
# -------
# Test if CodeExercise works correct for only checks

# Test 3.1
# TODO
# get_code_exercise(
#    [single_param_check(use_fingerprint=False, failing=True, buggy=False)],
#    include_checks=True,
#    include_params=False,
# )

# Test 3.2
# TODO
# get_code_exercise(
#    [single_param_check(use_fingerprint=True, failing=True, buggy=False)],
#    include_checks=True,
#    include_params=False,
# )
