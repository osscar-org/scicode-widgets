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
from scwidgets.check import CheckRegistry

sys.path.insert(0, os.path.abspath("../.."))
from tests.test_check import mock_checkable_widget  # noqa: E402
from tests.test_check import single_param_check  # noqa: E402

# -

scwidgets.get_css_style()


def create_check_registry(use_fingerprint, failing, buggy):
    check_registry = CheckRegistry()

    check = single_param_check(
        use_fingerprint=use_fingerprint, failing=failing, buggy=buggy
    )
    _ = mock_checkable_widget(check_registry, check.function_to_check, [check])
    return check_registry


# Test 1:
# -------
# Test if CheckRegistry shows correct output

# Test 1.1
create_check_registry(use_fingerprint=False, failing=False, buggy=False)

# Test 1.2
create_check_registry(use_fingerprint=True, failing=False, buggy=False)

# Test 1.3
create_check_registry(use_fingerprint=False, failing=True, buggy=False)

# Test 1.4
create_check_registry(use_fingerprint=True, failing=True, buggy=False)

# Test 1.5
create_check_registry(use_fingerprint=False, failing=False, buggy=True)
