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
from scwidgets.exercise import CodeExercise, ExerciseRegistry, TextExercise

sys.path.insert(0, os.path.abspath("../.."))

# -

scwidgets.get_css_style()


# Test 1:
# -------
# Test if ExerciseRegistry shows correct output

exercise_registry = ExerciseRegistry("pytest")
exercise_registry


# Test 2:
# -------
# Test if TextExercise shows correct output

text_exercise = TextExercise(
    exercise_registry=exercise_registry, exercise_key="exercise_1"
)
text_exercise

# Test 3:
# -------
# Test if CodeExercise shows correct output


# +
def foo(x):
    return x


code_ex = CodeExercise(
    foo,
    parameters={"x": (0, 2, 1)},
    update_mode="manual",
    exercise_registry=exercise_registry,
    exercise_key="exercise_2",
)
code_ex
# -
