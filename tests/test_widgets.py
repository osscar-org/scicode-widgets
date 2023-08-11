import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait


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
CUED_CUE_BOX_CLASS_NAME = (
    "lm-Widget.lm-Panel.jupyter-widgets.widget-container"
    ".widget-box.scwidget-cue-box.scwidget-cue-box--cue"
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

    # Test 2:
    # -------
    # Check if successful action ResetCueButton resets cue and failing action does not

    buttons = nb_cells[2].find_elements(By.CLASS_NAME, BUTTON_CLASS_NAME)
    reset_cue_button = buttons[0]
    assert reset_cue_button.get_property("title") == "Reset Cue"
    failing_reset_cue_button = buttons[1]
    assert failing_reset_cue_button.get_property("title") == "Failing Reset Cue"
    text_input = nb_cells[2].find_element(By.CLASS_NAME, TEXT_INPUT_CLASS_NAME)
    assert text_input.get_attribute("value") == "Text"
    assert not (reset_cue_button.is_enabled())
    assert not (failing_reset_cue_button.is_enabled())

    # Checks if two widgets are uncued on init
    cue_box_widgets = nb_cells[2].find_elements(By.CLASS_NAME, CUE_BOX_CLASS_NAME)
    assert len(cue_box_widgets) == 4

    # Checks if two widgets are cued on change
    text_input.send_keys("a")
    assert text_input.get_attribute("value") == "Texta"

    WebDriverWait(driver, 1).until(
        expected_conditions.element_to_be_clickable(reset_cue_button)
    )
    cued_widgets = nb_cells[2].find_elements(By.CLASS_NAME, CUED_CUE_BOX_CLASS_NAME)
    assert reset_cue_button.is_enabled()
    assert failing_reset_cue_button.is_enabled()
    assert len(cued_widgets) == 4

    # Check if cue is reset once pressed on the button
    reset_cue_button.click()
    WebDriverWait(driver, 1).until_not(
        expected_conditions.element_to_be_clickable(reset_cue_button)
    )
    assert not (reset_cue_button.is_enabled())
    cued_widgets = nb_cells[2].find_elements(By.CLASS_NAME, CUED_CUE_BOX_CLASS_NAME)
    # cued_widgets = [uncued_widget.get_attribute("class") for widget in uncued_widgets
    #        if "scwidget-cue-box--cue" in widget.get_attribute("class")]
    assert len(cued_widgets) == 2

    failing_reset_cue_button.click()
    assert failing_reset_cue_button.is_enabled()
    cued_widgets = nb_cells[2].find_elements(By.CLASS_NAME, CUED_CUE_BOX_CLASS_NAME)
    assert len(cued_widgets) == 2
