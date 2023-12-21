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
from scwidgets.answer import AnswerRegistry
from scwidgets.code import CodeDemo
from scwidgets.exercise import Textarea

sys.path.insert(0, os.path.abspath("../.."))

# -

scwidgets.get_css_style()


# Test 1:
# -------
# Test if AnswerRegistry shows correct output

answer_registry = AnswerRegistry("pytest")
answer_registry


# Test 2:
# -------
# Test if Textarea shows correct output

textarea = Textarea(answer_registry=answer_registry, answer_key="exercise_1")
textarea

# Test 3:
# -------
# Test if CodeDemo shows correct output


# +
def foo():
    return


code_demo = CodeDemo(foo, answer_registry=answer_registry, answer_key="exercise_2")
code_demo
# -
