import time
from typing import List

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
    "lm-Widget.lm-Panel.jupyter-widgets.widget-container"
    ".widget-box.widget-vbox.scwidget-cue-box"
)
CUED_CUE_BOX_CLASS_NAME = (
    "lm-Widget.lm-Panel.jupyter-widgets.widget-container"
    ".widget-box.widget-vbox.scwidget-cue-box.scwidget-cue-box--cue"
)


CODE_MIRROR_CLASS_NAME = "CodeMirror-code"


def cue_box_class_name(cue_box_name: str, cued: bool):
    class_name = CUED_CUE_BOX_CLASS_NAME if cued else CUE_BOX_CLASS_NAME
    if cue_box_name is None:
        return class_name
    return class_name.replace("cue-box", f"{cue_box_name}-cue-box")


def cue_class_name(cue_box_name: str, cued: bool):
    if cued:
        class_name = "scwidget-cue-box--cue"
    else:
        class_name = "scwidget-cue-box"
    if cue_box_name is None:
        return class_name
    return class_name.replace("cue-box", f"{cue_box_name}-cue-box")


BUTTON_CLASS_NAME = "lm-Widget.jupyter-widgets.jupyter-button.widget-button"
OUTPUT_CLASS_NAME = "lm-Widget.jp-RenderedText.jp-mod-trusted.jp-OutputArea-output"
TEXT_INPUT_CLASS_NAME = "widget-input"


def test_widgets_cue(selenium_driver):
    """
    Basic test checks if button with description "Text" exists

    :param selenium_driver: see conftest.py
    """
    driver = selenium_driver("tests/notebooks/widgets_cue.ipynb")

    # Each cell of the notebook, the cell number can be retrieved from the
    # attribute "data-windowed-list-index"
    nb_cells = driver.find_elements(
        By.CLASS_NAME, "lm-Widget.jp-Cell.jp-CodeCell.jp-Notebook-cell"
    )
    # Test 1:
    # -------
    # Check if CueBox shows cue when changed

    # Checks if the labels widget with value "Text" exists in cell 1
    def test_cue_box_cued(nb_cell, cue_box_name, cued_on_init):
        # we wait till cue boxs have been already loaded
        WebDriverWait(driver, 5).until(
            expected_conditions.text_to_be_present_in_element_attribute(
                (By.CLASS_NAME, cue_box_class_name(cue_box_name, False)),
                "class",
                cue_box_class_name(cue_box_name, False).replace(".", " "),
            )
        )
        # we select the specific one in the nb_cell
        cue_box_widget = nb_cell.find_element(
            By.CLASS_NAME, cue_box_class_name(cue_box_name, False)
        )

        # because cued widgets can be found by the base class name (noncued)
        # we check here that the class string is strictly equal
        assert cue_box_class_name(cue_box_name, cued_on_init).replace(
            ".", " "
        ) == cue_box_widget.get_attribute("class")

        text_input = nb_cell.find_element(By.CLASS_NAME, TEXT_INPUT_CLASS_NAME)
        assert text_input.get_attribute("value") == "Text"
        # some input that changes the widget

        # Check if cue is added once text input is changed
        text_input.send_keys("a")
        assert text_input.get_attribute("value") == "Texta"
        assert cue_box_class_name(cue_box_name, True).replace(
            ".", " "
        ) == cue_box_widget.get_attribute("class")

    # Test 1.1
    test_cue_box_cued(nb_cells[2], None, True)
    # Test 1.2
    test_cue_box_cued(nb_cells[3], None, False)
    # Test 1.3
    test_cue_box_cued(nb_cells[4], "save", False)
    # Test 1.4
    test_cue_box_cued(nb_cells[5], "check", False)
    # Test 1.5
    test_cue_box_cued(nb_cells[6], "update", False)

    # Test 2:
    # -------
    # Check if successful action ResetCueButton resets cue and failing action does not

    nb_cell = nb_cells[7]
    buttons = nb_cell.find_elements(By.CLASS_NAME, BUTTON_CLASS_NAME)
    reset_cue_button = buttons[0]
    assert reset_cue_button.get_property("title") == "Reset Cue"
    failing_reset_cue_button = buttons[1]
    assert failing_reset_cue_button.get_property("title") == "Failing Reset Cue"
    text_input = nb_cell.find_element(By.CLASS_NAME, TEXT_INPUT_CLASS_NAME)
    assert text_input.get_attribute("value") == "Text"
    assert not (reset_cue_button.is_enabled())
    assert not (failing_reset_cue_button.is_enabled())

    # Checks if two widgets are uncued on init
    cue_box_widgets = nb_cell.find_elements(By.CLASS_NAME, CUE_BOX_CLASS_NAME)
    assert len(cue_box_widgets) == 4

    # Checks if two widgets are cued on change
    text_input.send_keys("a")
    assert text_input.get_attribute("value") == "Texta"

    WebDriverWait(driver, 1).until(
        expected_conditions.element_to_be_clickable(reset_cue_button)
    )
    cued_widgets = nb_cell.find_elements(By.CLASS_NAME, CUED_CUE_BOX_CLASS_NAME)
    assert reset_cue_button.is_enabled()
    assert failing_reset_cue_button.is_enabled()
    assert len(cued_widgets) == 4

    # Check if cue is reset once pressed on the button
    reset_cue_button.click()
    WebDriverWait(driver, 1).until_not(
        expected_conditions.element_to_be_clickable(reset_cue_button)
    )
    assert not (reset_cue_button.is_enabled())
    cued_widgets = nb_cell.find_elements(By.CLASS_NAME, CUED_CUE_BOX_CLASS_NAME)
    # cued_widgets = [uncued_widget.get_attribute("class") for widget in uncued_widgets
    #        if "scwidget-cue-box--cue" in widget.get_attribute("class")]
    assert len(cued_widgets) == 2

    failing_reset_cue_button.click()
    assert failing_reset_cue_button.is_enabled()
    cued_widgets = nb_cell.find_elements(By.CLASS_NAME, CUED_CUE_BOX_CLASS_NAME)
    assert len(cued_widgets) == 2


def test_widget_check_registry(selenium_driver):
    """
    Basic test checks if button with description "Text" exists

    :param selenium_driver: see conftest.py
    """
    driver = selenium_driver("tests/notebooks/widget_check_registry.ipynb")

    # Each cell of the notebook, the cell number can be retrieved from the
    # attribute "data-windowed-list-index"
    nb_cells = driver.find_elements(
        By.CLASS_NAME, "lm-Widget.jp-Cell.jp-CodeCell.jp-Notebook-cell"
    )

    # Test 1:
    # -------
    # Check if CheckRegistry

    def test_button_clicks(
        nb_cell,
        expected_text_on_check_all_widgets: str,
        expected_text_on_set_all_references: str,
        expected_text_on_set_all_references_and_check: str,
    ):
        """
        clicks the check_all_widgets button, asserts that :param
        expected_text_on_check_all_widgets: is in output.  clicks the set_all_references
        button, asserts that :param expected_text_on_set_all_references: is in output.
        then clicks again the check_all_widgets button, asserts that :param
        expected_text_on_check_all_widgets: is in output.

        :param expected_text_on_check_all_widgets:
            output message after the button click on "Check all widgets"
        :param expected_text_on_set_all_references:
            output message after the button click on "Check all widgets"
        :param expected_text_on_set_all_references_and_check:
            output message after the button click on "Check all widgets"

        """

        buttons = nb_cell.find_elements(By.CLASS_NAME, BUTTON_CLASS_NAME)
        set_all_references_button = buttons[0]
        assert set_all_references_button.get_property("title") == "Set all references"
        check_all_widgets_button = buttons[1]
        assert check_all_widgets_button.get_property("title") == "Check all widgets"

        WebDriverWait(driver, 5).until(
            expected_conditions.element_to_be_clickable(check_all_widgets_button)
        ).click()
        outputs = nb_cell.find_elements(By.CLASS_NAME, OUTPUT_CLASS_NAME)
        assert (
            sum(
                [
                    output.text.count(expected_text_on_check_all_widgets)
                    for output in outputs
                ]
            )
            == 1
        )

        WebDriverWait(driver, 5).until(
            expected_conditions.element_to_be_clickable(set_all_references_button)
        ).click()
        outputs = nb_cell.find_elements(By.CLASS_NAME, OUTPUT_CLASS_NAME)
        assert (
            sum(
                [
                    output.text.count(expected_text_on_set_all_references)
                    for output in outputs
                ]
            )
            == 1
        )

        WebDriverWait(driver, 5).until(
            expected_conditions.element_to_be_clickable(check_all_widgets_button)
        ).click()
        outputs = nb_cell.find_elements(By.CLASS_NAME, OUTPUT_CLASS_NAME)
        assert (
            sum(
                [
                    output.text.count(expected_text_on_set_all_references_and_check)
                    for output in outputs
                ]
            )
            == 1
        )

    # Test 1.1 use_fingerprint=False, failing=False, buggy=False
    test_button_clicks(
        nb_cells[3],
        "Widget 1 all checks were successful.",
        "Successful set all references.",
        "Widget 1 all checks were successful.",
    )

    # Test 1.2 use_fingerprint=True, failing=False, buggy=False
    test_button_clicks(
        nb_cells[4],
        "Widget 1 all checks were successful.",
        "Successful set all references.",
        "Widget 1 all checks were successful.",
    )

    # Test 1.3 use_fingerprint=False, failing=False, buggy=False
    test_button_clicks(
        nb_cells[5],
        "Widget 1 not all checks were successful",
        "Successful set all references.",
        "Widget 1 all checks were successful.",
    )

    # Test 1.4 use_fingerprint=False, failing=False, buggy=False
    test_button_clicks(
        nb_cells[6],
        "Widget 1 not all checks were successful",
        "Successful set all references.",
        "Widget 1 all checks were successful.",
    )

    # Test 1.5 use_fingerprint=False, failing=False, buggy=True
    test_button_clicks(
        nb_cells[7],
        "Widget 1 raised error",
        "NameError: name 'bug' is not defined",
        "Widget 1 raised error",
    )


def test_widgets_code(selenium_driver):
    """
    Tests the widget of the module code

    :param selenium_driver: see conftest.py
    """
    driver = selenium_driver("tests/notebooks/widget_code_demo.ipynb")

    # Each cell of the notebook, the cell number can be retrieved from the
    # attribute "data-windowed-list-index"
    nb_cells = driver.find_elements(
        By.CLASS_NAME, "lm-Widget.jp-Cell.jp-CodeCell.jp-Notebook-cell"
    )
    # Test 1:
    # -------
    WebDriverWait(driver, 5).until(
        expected_conditions.text_to_be_present_in_element_attribute(
            (By.CLASS_NAME, BUTTON_CLASS_NAME),
            "title",
            "Check Code",
        )
    )

    def test_code_demo(
        nb_cell, expected_texts_on_update: List[str], expected_texts_on_check: List[str]
    ):
        ########################################################
        # asserts for correct initialization of check elements #
        ########################################################
        check_elements = nb_cell.find_elements(
            By.CLASS_NAME, cue_box_class_name("check", False)
        )
        assert len(check_elements) == 2
        check_code_input = check_elements[0]
        assert "def function_to_check" in check_code_input.text
        assert cue_class_name("check", True) in check_code_input.get_attribute("class")

        check_button = check_elements[1]
        assert check_button.text == "Check Code"
        assert check_button.is_enabled()
        assert cue_class_name("check", True) in check_button.get_attribute("class")

        #########################################################
        # asserts for correct initialization of update elements #
        #########################################################
        update_elements = nb_cell.find_elements(
            By.CLASS_NAME, cue_box_class_name("update", False)
        )
        assert len(update_elements) == 3
        update_code_input = update_elements[0]
        assert "def function_to_check" in update_code_input.text
        assert cue_class_name("update", True) in update_code_input.get_attribute(
            "class"
        )
        parameter_panel = update_elements[1]
        # in these tests it should not be contain inything
        assert parameter_panel.size["height"] == 0

        update_button = update_elements[2]
        assert update_button.text == "Run Code"
        assert update_button.is_enabled()
        assert cue_class_name("update", True) in update_button.get_attribute("class")

        #################################################
        # asserts for behavior on click of check button #
        #################################################
        check_button.click()
        time.sleep(0.1)
        assert not (
            cue_class_name("check", True) in check_code_input.get_attribute("class")
        )
        assert not (
            cue_class_name("check", True) in check_button.get_attribute("class")
        )
        assert check_button.is_enabled()
        outputs = nb_cell.find_elements(By.CLASS_NAME, OUTPUT_CLASS_NAME)
        for text in expected_texts_on_check:
            assert sum([output.text.count(text) for output in outputs]) == 1

        ##################################################
        # asserts for behavior on click of update button #
        ##################################################
        update_button.click()
        time.sleep(0.1)
        assert not (
            cue_class_name("update", True) in update_code_input.get_attribute("class")
        )
        assert not (
            cue_class_name("update", True) in update_button.get_attribute("class")
        )
        assert update_button.is_enabled()
        outputs = nb_cell.find_elements(By.CLASS_NAME, OUTPUT_CLASS_NAME)
        for text in expected_texts_on_update:
            assert sum([output.text.count(text) for output in outputs]) == 1

        #####################################
        # asserts on reaction on text ipnut #
        #####################################
        # expected_conditions.text_to_be_present_in_element does not work for code input
        code_input = nb_cell.find_elements(By.CLASS_NAME, "CodeMirror-lines")

        code_input = nb_cell.find_elements(By.CLASS_NAME, CODE_MIRROR_CLASS_NAME)[2]
        assert "return" in code_input.text
        # Issue #22
        #   sending keys to code widget does not work at the moment
        #   once this works please add this code
        # code_input.send_keys("a=5\n")
        # time.sleep(0.1)
        # assert (cue_class_name("check", True) in
        #               check_code_input.get_attribute("class"))
        # assert (cue_class_name("update", True) in
        #                update_code_input.get_attribute("class"))
        # assert check_button.is_enabled()
        # assert check_button.is_enabled()

    # Test 1.1
    test_code_demo(nb_cells[3], ["SomeText", "Output"], ["All checks were successful"])
    # Test 1.2
    test_code_demo(nb_cells[4], ["SomeText", "Output"], ["Some checks failed"])
    # Test 1.3
    test_code_demo(
        nb_cells[5],
        ["SomeText", "NameError: name 'bug' is not defined"],
        ["NameError: name 'bug' is not defined"],
    )
    # TODO Test 1.4
    # parameter panel

    # TODO Test 2
    # test only update, no check

    # TODO Test 3
    # test only checks, no run
