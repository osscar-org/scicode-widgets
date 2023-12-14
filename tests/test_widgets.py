import time
from typing import List

import numpy as np
import pytest
import requests
from imageio.v3 import imread
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from skimage.metrics import structural_similarity
from skimage.transform import resize


def crop_const_color_borders(image: np.ndarray, const_color: int = 255):
    if np.all(image == const_color):
        return image[:0, :0, :0]

    for i1 in range(len(image)):
        if np.any(image[i1, :, :] != const_color):
            break
    for i2 in range(image.shape[0] - 1, -1, -1):
        if np.any(image[i2, :, :] != const_color):
            break
    for j1 in range(len(image)):
        if np.any(image[:, j1, :] != const_color):
            break
    for j2 in range(image.shape[1] - 1, -1, -1):
        if np.any(image[:, j2, :] != const_color):
            break
    return image[i1:i2, j1:j2, :]


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


def cue_box_class_name(cue_type: str, cued: bool):
    class_name = CUED_CUE_BOX_CLASS_NAME if cued else CUE_BOX_CLASS_NAME
    if cue_type is None:
        return class_name
    return class_name.replace("cue-box", f"{cue_type}-cue-box")


def scwidget_cue_box_class_name(cue_type: str, cued: bool):
    if cued:
        class_name = "scwidget-cue-box--cue"
    else:
        class_name = "scwidget-cue-box"
    if cue_type is None:
        return class_name
    return class_name.replace("cue-box", f"{cue_type}-cue-box")


RESET_CUE_BUTTON_CLASS_NAME = (
    "lm-Widget.jupyter-widgets.jupyter-button.widget-button"
    ".scwidget-reset-cue-button"
)
CUED_RESET_CUE_BUTTON_CLASS_NAME = (
    "lm-Widget.jupyter-widgets.jupyter-button.widget-button"
    ".scwidget-reset-cue-button.scwidget-reset-cue-button--cue"
)


def reset_cue_button_class_name(cue_type: str, cued: bool):
    class_name = (
        CUED_RESET_CUE_BUTTON_CLASS_NAME if cued else RESET_CUE_BUTTON_CLASS_NAME
    )
    if cue_type is None:
        return class_name
    return class_name.replace("reset-cue-button", f"{cue_type}-reset-cue-button")


def scwidget_reset_cue_button_class_name(cue_type: str, cued: bool):
    if cued:
        class_name = "scwidget-reset-cue-button--cue"
    else:
        class_name = "scwidget-reset-cue-button"
    if cue_type is None:
        return class_name
    return class_name.replace("reset-cue-button", f"{cue_type}-reset-cue-button")


BUTTON_CLASS_NAME = "lm-Widget.jupyter-widgets.jupyter-button.widget-button"
OUTPUT_CLASS_NAME = "lm-Widget.jp-RenderedText.jp-mod-trusted.jp-OutputArea-output"
TEXT_INPUT_CLASS_NAME = "widget-input"
CODE_MIRROR_CLASS_NAME = "CodeMirror-code"
MATPLOTLIB_CANVAS_CLASS_NAME = "jupyter-widgets.jupyter-matplotlib-canvas-container"


@pytest.mark.parametrize(
    "nb_filename, mpl_backend",
    [
        ("tests/notebooks/widget_cue_figure-ipympl.ipynb", "ipympl"),
        ("tests/notebooks/widget_cue_figure-inline.ipynb", "inline"),
    ],
)
def test_widget_figure(selenium_driver, nb_filename, mpl_backend):
    """
    We separate the widget figure tests for different backends to different files
    because a backend switch within a running notebook causes undefined behavior
    of matplotlib (e.g. the figures are not anymore displayed when they should be)

    :param selenium_driver: see conftest.py
    """
    # TODO for inline i need to get the image directly from the panel
    driver = selenium_driver(nb_filename)

    # Each cell of the notebook, the cell number can be retrieved from the
    # attribute "data-windowed-list-index"
    nb_cells = driver.find_elements(
        By.CLASS_NAME, "lm-Widget.jp-Cell.jp-CodeCell.jp-Notebook-cell"
    )

    if "inline" == mpl_backend:
        WebDriverWait(nb_cells[20], 5).until(
            expected_conditions.visibility_of_all_elements_located(
                (By.TAG_NAME, "img"),
            )
        )
        matplotlib_canvases = driver.find_elements(By.TAG_NAME, "img")
    elif "ipympl" == mpl_backend:
        WebDriverWait(nb_cells[20], 5).until(
            expected_conditions.visibility_of_all_elements_located(
                (By.CLASS_NAME, MATPLOTLIB_CANVAS_CLASS_NAME),
            )
        )
        driver.find_elements(By.CLASS_NAME, MATPLOTLIB_CANVAS_CLASS_NAME)
        matplotlib_canvases = driver.find_elements(
            By.CLASS_NAME, MATPLOTLIB_CANVAS_CLASS_NAME
        )
    else:
        raise ValueError(f"matplotlib backend {mpl_backend!r} is not known.")
    assert len(matplotlib_canvases) >= 5, (
        "Not all matplotlib canvases have been correctly " "loaded."
    )
    assert len(matplotlib_canvases) == 5, (
        "Test that plt.show() does not show any plot "
        "failed. For each test there should be only "
        "one plot."
    )

    def test_cue_figure(web_element: WebElement, ref_png_filename: str, rtol=5e-2):
        # images can have different white border and slightly
        # different shape so we cut the border of and resize them
        image = imread(web_element.screenshot_as_png)
        image = crop_const_color_borders(image)
        ref_image = imread(ref_png_filename)
        ref_image = crop_const_color_borders(ref_image)
        # scale up
        resized_image = resize(
            image, ref_image.shape, cval=255, mode="constant", preserve_range=True
        )
        image = np.array(resized_image, dtype=ref_image.dtype)
        ssim = structural_similarity(image, ref_image, channel_axis=2)
        # structural similarity index returns a value in the range [0,1]
        # so it atol is always rtol in this case
        np.testing.assert_allclose(ssim, 1, atol=rtol, rtol=rtol, equal_nan=False)

    time.sleep(0.2)
    # Test 1.1
    # inline does not show a plot
    if mpl_backend == "inline":
        # in inline mode no image is shown by the figure but somehow
        # an image of the python logo is show, we ignore this case
        pass
    elif mpl_backend == "ipympl":
        image = imread(matplotlib_canvases[0].screenshot_as_png)
        assert crop_const_color_borders(image).shape == (0, 0, 0), "Image is not white"
    # Test 1.2
    test_cue_figure(
        matplotlib_canvases[1], "tests/screenshots/widget_cue_figure/empty_axis.png"
    )
    # Test 1.3
    test_cue_figure(
        matplotlib_canvases[2],
        "tests/screenshots/widget_cue_figure/update_figure_plot.png",
    )
    # Test 1.4
    test_cue_figure(
        matplotlib_canvases[3],
        "tests/screenshots/widget_cue_figure/update_figure_set.png",
    )
    # Test 1.5
    test_cue_figure(
        matplotlib_canvases[4],
        "tests/screenshots/widget_cue_figure/update_figure_plot.png",
    )


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
        time.sleep(0.1)
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

    def test_reset_cue_button(
        nb_cell, disable_on_successful_action, failing_action, error_in_action
    ):
        cue_box_widgets = nb_cell.find_elements(By.CLASS_NAME, CUE_BOX_CLASS_NAME)
        assert len(cue_box_widgets) == 3
        buttons = nb_cell.find_elements(By.CLASS_NAME, RESET_CUE_BUTTON_CLASS_NAME)
        assert len(buttons) == 1
        reset_cue_button = buttons[0]
        assert reset_cue_button.get_property("title") == "Reset Cue"
        text_inputs = nb_cell.find_elements(By.CLASS_NAME, TEXT_INPUT_CLASS_NAME)
        text_input = text_inputs[0]
        unused_text_input = text_inputs[1]
        assert text_input.get_attribute("value") == "Text"
        assert unused_text_input.get_attribute("value") == "Unused"
        assert reset_cue_button.is_enabled()

        # Checks if all widgets are uncued on init
        assert (
            sum(
                [
                    cue_box_widget.get_attribute("class")
                    == CUED_CUE_BOX_CLASS_NAME.replace(".", " ")
                    for cue_box_widget in cue_box_widgets
                ]
            )
            == 0
        )
        assert reset_cue_button.get_attribute(
            "class"
        ) == RESET_CUE_BUTTON_CLASS_NAME.replace(".", " ")

        # Check if unused text input does not effect cueing of button
        unused_text_input.send_keys("a")
        time.sleep(0.1)
        assert unused_text_input.get_attribute("value") == "Unuseda"
        assert (
            sum(
                [
                    cue_box_widget.get_attribute("class")
                    == CUED_CUE_BOX_CLASS_NAME.replace(".", " ")
                    for cue_box_widget in cue_box_widgets
                ]
            )
            == 1
        )
        assert reset_cue_button.get_attribute(
            "class"
        ) == RESET_CUE_BUTTON_CLASS_NAME.replace(".", " ")

        # Checks if buttons becomes disabled only on successful action
        reset_cue_button.click()
        if (
            disable_on_successful_action
            and not (failing_action)
            and not (error_in_action)
        ):
            WebDriverWait(driver, 1).until_not(
                expected_conditions.element_to_be_clickable(reset_cue_button)
            )
            assert not (reset_cue_button.is_enabled())
        else:
            time.sleep(0.1)
            assert reset_cue_button.is_enabled()

        # Checks if two more widgets are cued on change
        text_input.send_keys("a")
        assert text_input.get_attribute("value") == "Texta"

        WebDriverWait(driver, 1).until(
            expected_conditions.element_to_be_clickable(reset_cue_button)
        )
        assert (
            sum(
                [
                    cue_box_widget.get_attribute("class")
                    == CUED_CUE_BOX_CLASS_NAME.replace(".", " ")
                    for cue_box_widget in cue_box_widgets
                ]
            )
            == 3
        )
        assert reset_cue_button.get_attribute(
            "class"
        ) == CUED_RESET_CUE_BUTTON_CLASS_NAME.replace(".", " ")
        assert reset_cue_button.is_enabled()

        # Check if cue is reset once pressed on the button
        reset_cue_button.click()
        if (
            disable_on_successful_action
            and not (failing_action)
            and not (error_in_action)
        ):
            WebDriverWait(driver, 1).until_not(
                expected_conditions.element_to_be_clickable(reset_cue_button)
            )
            assert not (reset_cue_button.is_enabled())
        else:
            time.sleep(0.1)
            assert reset_cue_button.is_enabled()

        assert (
            sum(
                [
                    cue_box_widget.get_attribute("class")
                    == CUED_CUE_BOX_CLASS_NAME.replace(".", " ")
                    for cue_box_widget in cue_box_widgets
                ]
            )
            == 1
        )
        assert reset_cue_button.get_attribute(
            "class"
        ) == RESET_CUE_BUTTON_CLASS_NAME.replace(".", " ")

    # Test 2.1
    test_reset_cue_button(
        nb_cells[8],
        disable_on_successful_action=True,
        failing_action=False,
        error_in_action=False,
    )

    # Test 2.2
    test_reset_cue_button(
        nb_cells[9],
        disable_on_successful_action=True,
        failing_action=True,
        error_in_action=False,
    )

    # Test 2.3
    test_reset_cue_button(
        nb_cells[10],
        disable_on_successful_action=False,
        failing_action=False,
        error_in_action=False,
    )

    # Test 2.4
    test_reset_cue_button(
        nb_cells[11],
        disable_on_successful_action=False,
        failing_action=True,
        error_in_action=False,
    )

    # Test 2.5
    test_reset_cue_button(
        nb_cells[12],
        disable_on_successful_action=True,
        failing_action=False,
        error_in_action=True,
    )


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
        time.sleep(0.1)
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
        time.sleep(0.1)
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
        time.sleep(0.1)
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
        nb_cell,
        expected_texts_on_update: List[str],
        expected_texts_on_check: List[str],
        include_checks=True,
        include_params=True,
        tunable_params=False,
        update_mode="manual",
    ):
        ########################################################
        # asserts for correct initialization of check elements #
        ########################################################
        if include_checks:
            check_boxes = nb_cell.find_elements(
                By.CLASS_NAME, cue_box_class_name("check", False)
            )
            check_buttons = nb_cell.find_elements(
                By.CLASS_NAME, reset_cue_button_class_name("check", False)
            )
            assert len(check_boxes) == 1
            assert len(check_buttons) == 1
            check_code_input = check_boxes[0]
            assert "def function_to_check" in check_code_input.text
            assert scwidget_cue_box_class_name(
                "check", True
            ) in check_code_input.get_attribute("class")

            check_button = check_buttons[0]
            assert check_button.text == "Check Code"
            assert check_button.is_enabled()
            assert scwidget_reset_cue_button_class_name(
                "check", True
            ) in check_button.get_attribute("class")

        #########################################################
        # asserts for correct initialization of update elements #
        #########################################################
        if include_params:
            update_boxes = nb_cell.find_elements(
                By.CLASS_NAME, cue_box_class_name("update", False)
            )
            assert len(update_boxes) == 2
            update_code_input = update_boxes[0]
            assert "def function_to_check" in update_code_input.text
            assert scwidget_cue_box_class_name(
                "update", True
            ) in update_code_input.get_attribute("class")
            parameter_panel = update_boxes[1]
            # in these tests it should not be contain inything
            if not (tunable_params):
                assert parameter_panel.size["height"] == 0
            else:
                assert scwidget_cue_box_class_name(
                    "update", True
                ) in parameter_panel.get_attribute("class")

            update_buttons = nb_cell.find_elements(
                By.CLASS_NAME, reset_cue_button_class_name("update", False)
            )
            assert len(update_buttons) == 1
            update_button = update_buttons[0]
            assert update_button.text == "Run Code"
            assert update_button.is_enabled()
            assert scwidget_reset_cue_button_class_name(
                "update", True
            ) in update_button.get_attribute("class")

        #################################################
        # asserts for behavior on click of check button #
        #################################################
        if include_checks:
            check_button.click()
            time.sleep(0.5)
            assert not (
                scwidget_cue_box_class_name("check", True)
                in check_code_input.get_attribute("class")
            )
            assert not (
                scwidget_reset_cue_button_class_name("check", True)
                in check_button.get_attribute("class")
            )
            assert check_button.is_enabled()
            outputs = nb_cell.find_elements(By.CLASS_NAME, OUTPUT_CLASS_NAME)
            for text in expected_texts_on_check:
                assert sum([output.text.count(text) for output in outputs]) == 1

        ##################################################
        # asserts for behavior on click of update button #
        ##################################################
        if include_params:
            update_button.click()
            time.sleep(0.2)
            assert not (
                scwidget_cue_box_class_name("update", True)
                in update_code_input.get_attribute("class")
            )
            assert not (
                scwidget_reset_cue_button_class_name("update", True)
                in update_button.get_attribute("class")
            )
            assert update_button.is_enabled()
            if tunable_params:
                assert not (
                    scwidget_cue_box_class_name("update", True)
                    in parameter_panel.get_attribute("class")
                )
            outputs = nb_cell.find_elements(By.CLASS_NAME, OUTPUT_CLASS_NAME)
            for text in expected_texts_on_update:
                assert sum([output.text.count(text) for output in outputs]) == 1

        #####################################
        # asserts on reaction on text input #
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
        # assert (scwidget_cue_box_class_name("check", True) in
        #               check_code_input.get_attribute("class"))
        # assert (scwidget_cue_box_class_name("update", True) in
        #                update_code_input.get_attribute("class"))
        # assert check_button.is_enabled()
        # assert check_button.is_enabled()

        if tunable_params:
            outputs = nb_cell.find_elements(By.CLASS_NAME, OUTPUT_CLASS_NAME)
            assert len(outputs) == 2
            before_parameter_change_text = outputs[0].text + outputs[1].text

            slider_input_box = nb_cell.find_element(By.CLASS_NAME, "widget-readout")
            slider_input_box.send_keys(Keys.BACKSPACE)
            slider_input_box.send_keys(Keys.BACKSPACE)
            slider_input_box.send_keys(2)
            slider_input_box.send_keys(Keys.ENTER)
            time.sleep(0.2)

            # if update mode manual, then cue box should be seen
            assert scwidget_cue_box_class_name(
                "update", (update_mode == "manual")
            ) in parameter_panel.get_attribute("class")
            assert scwidget_reset_cue_button_class_name(
                "update", (update_mode == "manual")
            ) in update_button.get_attribute("class")

            if update_mode == "manual":
                # Check if output has changed only after click when manual
                outputs = nb_cell.find_elements(By.CLASS_NAME, OUTPUT_CLASS_NAME)
                assert len(outputs) == 2
                after_parameter_change_text = outputs[0].text + outputs[1].text
                assert before_parameter_change_text == after_parameter_change_text
                update_button.click()

            outputs = nb_cell.find_elements(By.CLASS_NAME, OUTPUT_CLASS_NAME)
            assert len(outputs) == 2
            after_parameter_change_text = outputs[0].text + outputs[1].text
            assert before_parameter_change_text != after_parameter_change_text

    # Test 1.1
    test_code_demo(
        nb_cells[3],
        ["SomeText", "Output"],
        ["Check was successful"],
        include_checks=True,
        include_params=True,
        tunable_params=False,
        update_mode="manual",
    )

    # Test 1.2
    test_code_demo(
        nb_cells[4],
        ["SomeText", "Output"],
        ["Check failed"],
        include_checks=True,
        include_params=True,
        tunable_params=False,
        update_mode="manual",
    )

    # Test 1.3
    test_code_demo(
        nb_cells[5],
        ["SomeText", "NameError: name 'bug' is not defined"],
        ["NameError: name 'bug' is not defined"],
        include_checks=True,
        include_params=True,
        tunable_params=False,
        update_mode="manual",
    )
    # Test 1.4
    test_code_demo(
        nb_cells[6],
        ["SomeText", "Output"],
        ["Check was successful"],
        include_checks=True,
        include_params=True,
        tunable_params=True,
        update_mode="manual",
    )

    # Test 1.5
    test_code_demo(
        nb_cells[7],
        ["SomeText", "Output"],
        ["Check was successful"],
        include_checks=True,
        include_params=True,
        tunable_params=True,
        update_mode="continuous",
    )

    # Test 1.6
    test_code_demo(
        nb_cells[8],
        ["SomeText", "Output"],
        ["Check was successful"],
        include_checks=True,
        include_params=True,
        tunable_params=True,
        update_mode="release",
    )

    # Test 2:
    # -------
    # TODO test only update, no check

    # Test 3:
    # -------
    # TODO test only checks, no run
