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
import scwidgets
from scwidgets.code import CodeInput

# -

scwidgets.get_css_style()

# Test 1:
# -------
# Test if CodeInput traits are updading the widget view


# +
def foo():
    return "init"


ci = CodeInput(foo)
ci
# -

ci.function_body = """return 'change'"""
