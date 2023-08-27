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


def run_code_demo(checks):
    return get_code_demo(checks)


# Test 1:
# -------
# Test if CodeDemo shows correct output

# Test 1.1
run_code_demo([single_param_check(use_fingerprint=False, failing=False, buggy=False)])

# Test 1.2
run_code_demo([single_param_check(use_fingerprint=False, failing=True, buggy=False)])

# Test 1.3
run_code_demo([single_param_check(use_fingerprint=False, failing=False, buggy=True)])
