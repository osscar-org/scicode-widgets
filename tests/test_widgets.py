import pytest
import requests
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By


def test_notebook_running(notebook_service):
    """Tests if juypter notebook is running

    :param notebook_service: see conftest.py
    """
    url, token = notebook_service
    nb_path = "tree"
    response = requests.get(f"{url}/{nb_path}?token={token}")
    # status code 200 means it was successful
    assert response.status_code == 200


def test_widget_cue_box(selenium_driver):
    """
    Basic test checks if button with description "Text" exists

    :param selenium_driver: see conftest.py
    """
    driver = selenium_driver("tests/notebooks/widget_cue_box.ipynb")

    # Each cell of the notebook, the cell number can be retrieved from the
    # attribute "data-windowed-list-index"
    nb_cells = driver.find_elements(
        By.CLASS_NAME, "lm-Widget.jp-Cell.jp-CodeCell.jp-Notebook-cell"
    )

    # Checks if the labels widget with value "Text" exists in cell 2
    widget1 = nb_cells[2].find_element(
        By.CLASS_NAME, "lm-Widget.jupyter-widgets.widget-inline-hbox.widget-label"
    )
    assert widget1.text == "Text"

    # Checks if the labels widget with unchanged value has the correct css style
    nb_cells[2].find_element(
        By.CLASS_NAME,
        "lm-Widget.lm-Panel.jupyter-widgets.widget-container"
        ".widget-box.scwidget-cue-box.scwidget-cue-box",
    )
    # we assume error is raised because the widget should not be cued
    with pytest.raises(NoSuchElementException, match=r".*Unable to locate element.*"):
        nb_cells[2].find_element(
            By.CLASS_NAME,
            "lm-Widget.lm-Panel.jupyter-widgets.widget-container"
            ".widget-box.scwidget-cue-box.scwidget-cue-box--cue",
        )

    # Checks if the labels widget with value "Cahnged Text" exists in cell 3
    widget2 = nb_cells[3].find_element(
        By.CLASS_NAME, "lm-Widget.jupyter-widgets.widget-inline-hbox.widget-label"
    )
    assert widget2.text == "Changed Text"

    # Checks if the labels widget with changed value has the correct css style
    nb_cells[3].find_element(
        By.CLASS_NAME,
        "lm-Widget.lm-Panel.jupyter-widgets.widget-container.widget-box"
        ".scwidget-cue-box.scwidget-cue-box",
    )
    nb_cells[3].find_element(
        By.CLASS_NAME,
        "lm-Widget.lm-Panel.jupyter-widgets.widget-container.widget-box"
        ".scwidget-cue-box.scwidget-cue-box--cue",
    )
