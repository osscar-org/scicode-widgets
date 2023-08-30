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

import scwidgets

sys.path.insert(0, os.path.abspath("../.."))
from tests.test_check import single_param_check  # noqa: E402
from tests.test_code import get_code_demo  # noqa: E402

# -

scwidgets.get_css_style()


def run_code_demo(checks, include_checks, include_params, tunable_params):
    return get_code_demo(checks, include_checks, include_params, tunable_params)


# Test 1:
# -------
# Test if CodeDemo shows correct output

# Test 1.1
run_code_demo(
    [single_param_check(use_fingerprint=False, failing=False, buggy=False)],
    include_checks=True,
    include_params=True,
    tunable_params=False,
)

# Test 1.2
run_code_demo(
    [single_param_check(use_fingerprint=False, failing=True, buggy=False)],
    include_checks=True,
    include_params=True,
    tunable_params=False,
)

# Test 1.3
run_code_demo(
    [single_param_check(use_fingerprint=False, failing=False, buggy=True)],
    include_checks=True,
    include_params=True,
    tunable_params=False,
)

# Test 1.4
run_code_demo(
    [single_param_check(use_fingerprint=False, failing=False, buggy=False)],
    include_checks=True,
    include_params=True,
    tunable_params=True,
)


# Test 2:
# -------
# Test if CodeDemo works correct for only checks

# Test 2.1
# TODO
# run_code_demo([single_param_check(use_fingerprint=False, failing=True, buggy=False)],
#        include_checks=True, include_params=False)

# Test 2.2
# TODO
# run_code_demo([single_param_check(use_fingerprint=True, failing=True, buggy=False)],
#        include_checks=True, include_params=False)

# Test 3:
# -------
# Test if CodeDemo works correct for only update

# Test 3.1
# TODO
# run_code_demo([single_param_check(use_fingerprint=False, failing=True, buggy=False)],
#        include_checks=False, include_params=True, tunable_params)

# Test 3.2
# TODO
# run_code_demo([single_param_check(use_fingerprint=True, failing=True, buggy=False)],
#        include_checks=False, include_params=True, tunable_params)
