import requests
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


CUE_BOX_CLASS_NAME = (
    "lm-Widget.lm-Panel.jupyter-widgets.widget-container" ".widget-box.scwidget-cue-box"
)
BUTTON_CLASS_NAME = "lm-Widget.jupyter-widgets.jupyter-button.widget-button"
TEXT_INPUT_CLASS_NAME = "widget-input"


def test_widgets(selenium_driver):
    """
    Basic test checks if button with description "Text" exists

    :param selenium_driver: see conftest.py
    """
    driver = selenium_driver("tests/notebooks/widgets.ipynb")

    # Each cell of the notebook, the cell number can be retrieved from the
    # attribute "data-windowed-list-index"
    nb_cells = driver.find_elements(
        By.CLASS_NAME, "lm-Widget.jp-Cell.jp-CodeCell.jp-Notebook-cell"
    )
    # Test 1:
    # -------
    # Check if CueBox shows cue when changed

    # Checks if the labels widget with value "Text" exists in cell 1
    text_input = nb_cells[1].find_element(By.CLASS_NAME, TEXT_INPUT_CLASS_NAME)
    assert text_input.get_attribute("value") == "Text"
    # some input that changes the widget
    cue_box_widget = nb_cells[1].find_element(By.CLASS_NAME, CUE_BOX_CLASS_NAME)

    # Check if cue is added once text input is changed
    text_input.send_keys("a")
    assert text_input.get_attribute("value") == "Texta"
    assert "scwidget-cue-box--cue" in cue_box_widget.get_attribute("class")
