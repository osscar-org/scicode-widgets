# ---
# jupyter:
#   jupytext:
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

import matplotlib
import matplotlib.pyplot as plt

from scwidgets.cue import CueFigure


def run_cue_figure():
    fig = plt.figure()
    return CueFigure(fig)


matplotlib.use("module://matplotlib_inline.backend_inline")


# #### Test 1.1
# Tests initalization of figure

cf = run_cue_figure()
cf

# just checks if no error is raised when no axes is present
cf.clear_figure()

# Tests if plots are properly closed inside the CueFigure
# so the output in this celll should be empty
plt.show()

# #### Test 1.2
# Tests if axis is drawn on figure

cf = run_cue_figure()
cf

cf.figure.gca()

# axes should be retained using clear_figure
cf.clear_figure()
cf.draw_display()

# Tests if plots are properly closed inside the CueFigure
# so the output in this celll should be empty
plt.show()

# +
# cf.figure.savefig("../screenshots/widget_cue_figure/empty_axis.png")
# -

# #### Test 1.3
# Tests draw_display

cf = run_cue_figure()
cf

ax = cf.figure.gca()
ax.plot([0, 0.5], [0, 0.5])
cf.draw_display()

# Tests if plots are properly closed
plt.show()


# +
# screenshot for references
# cf.figure.savefig("../screenshots/widget_cue_figure/update_figure_plot.png")
# -

# #### Test 1.4
# Tests update_figure using set operation


# +
def update_figure(cf, x, y):
    ax = cf.figure.gca()
    ax.plot([0, 1], [0, 1])
    line = ax.lines[0]
    line.set_data(x, y)


cf = run_cue_figure()
cf
# -

cf.clear_display()
update_figure(cf, [0, 0.5], [0, 0.5])
cf.draw_display()

# Tests if plots are properly closed
plt.show()


# +
# screenshot for references
# cf.figure.savefig("../screenshots/widget_cue_figure/update_figure_set.png")
# -

# #### Test 1.5
# Tests update_figure using plot operation


# +
def update_figure(cf, x, y):
    cf.figure.gca().plot(x, y)


cf = run_cue_figure()
cf
# -

cf.clear_display()
update_figure(cf, [0, 0.5], [0, 0.5])
cf.draw_display()

# Tests if plots are properly closed
plt.show()
