import base64
import glob
import os
import time
from typing import List

import numpy as np
import pytest
import requests
from imageio.v3 import imread
from packaging.version import Version
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from skimage.metrics import structural_similarity
from skimage.transform import resize

from .conftest import JUPYTER_TYPE


def crop_const_color_borders(image: np.ndarray, const_color: int = 255):
    """
    Removes all constant color borders of the image
    """
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


class NotebookCellList(list):
    """
    List of notebook cells that scrolls them into the view when accessing it.  When a
    cell is accessed it always goes to the top to scroll down cell by cell.  We can only
    scroll to an element if it is partially visible, so this method works as long as a
    cell is not larger than the view. We need to put the cells into the view because the
    content of the cells in lab 4 is not loaded otherwise.

    :param driver: see conftest.py selenium_driver function
    """

    def __init__(self, driver):
        self._driver = driver

        nb_cells = driver.find_elements(
            By.CLASS_NAME, "lm-Widget.jp-Cell.jp-CodeCell.jp-Notebook-cell"
        )
        # we scroll through the notebook and remove the cells that are empty
        ActionChains(driver).send_keys(Keys.HOME).perform()
        time.sleep(0.1)
        nb_cells_non_empty = []
        for nb_cell in nb_cells:
            driver.execute_script("arguments[0].scrollIntoView();", nb_cell)
            time.sleep(0.05)
            if nb_cell.text != "":
                nb_cells_non_empty.append(nb_cell)

        super().__init__(nb_cells_non_empty)

    def __getitem__(self, key):
        # have to retrieve from scratch as positions may have changed
        ActionChains(self._driver).send_keys(Keys.HOME).perform()
        time.sleep(0.1)
        for i in range(key):
            self._driver.execute_script(
                "arguments[0].scrollIntoView();", super().__getitem__(i)
            )
            time.sleep(0.05)

        nb_cell = super().__getitem__(key)
        self._driver.execute_script("arguments[0].scrollIntoView();", nb_cell)
        time.sleep(0.05)
        return nb_cell


#########
# Tests #
#########


def test_notebook_running(notebook_service):
    """Tests if juypter notebook is running

    :param notebook_service: see conftest.py
    """
    url, token = notebook_service
    # jupyter lab
    if JUPYTER_TYPE == "lab":
        nb_path = ""
    elif JUPYTER_TYPE == "notebook":
        nb_path = "tree"
    else:
        raise ValueError(
            f"Tests do not support jupyter type {JUPYTER_TYPE!r}. Please use 'notebook'"
            " or 'lab'."
        )
    response = requests.get(f"{url}/{nb_path}?token={token}")
    # status code 200 means it was successful
    assert response.status_code == 200


def test_setup_globals():
    from .conftest import JUPYTER_VERSION

    # black formats this into one line which causes an error in the linter.
    # fmt: off
    global BUTTON_CLASS_NAME, OUTPUT_CLASS_NAME, TEXT_INPUT_CLASS_NAME, \
        CODE_MIRROR_CLASS_NAME, MATPLOTLIB_CANVAS_CLASS_NAME, CUE_BOX_CLASS_NAME, \
        PRIVACY_BUTTON_CLASS_NAME
    global CUED_CUE_BOX_CLASS_NAME, RESET_CUE_BUTTON_CLASS_NAME, \
        CUED_RESET_CUE_BUTTON_CLASS_NAME
    # fmt: on

    if JUPYTER_TYPE == "notebook" and JUPYTER_VERSION >= Version("7.0.0"):
        BUTTON_CLASS_NAME = "lm-Widget.jupyter-widgets.jupyter-button.widget-button"
        OUTPUT_CLASS_NAME = (
            "lm-Widget.jp-RenderedText.jp-mod-trusted.jp-OutputArea-output"
        )
        TEXT_INPUT_CLASS_NAME = "widget-input"
        CODE_MIRROR_CLASS_NAME = "cm-content"
        MATPLOTLIB_CANVAS_CLASS_NAME = (
            "jupyter-widgets.jupyter-matplotlib-canvas-container"
        )
        CUE_BOX_CLASS_NAME = (
            "lm-Widget.lm-Panel.jupyter-widgets.widget-container"
            ".widget-box.widget-vbox.scwidget-cue-box"
        )
        PRIVACY_BUTTON_CLASS_NAME = "bp3-button.bp3-small.jp-toast-button.jp-Button"
    elif JUPYTER_TYPE == "lab" and JUPYTER_VERSION < Version("4.0.0"):
        BUTTON_CLASS_NAME = (
            "lm-Widget.p-Widget.jupyter-widgets.jupyter-button.widget-button"
        )
        OUTPUT_CLASS_NAME = (
            "lm-Widget.p-Widget.jp-RenderedText.jp-mod-trusted.jp-OutputArea-output"
        )
        TEXT_INPUT_CLASS_NAME = "widget-input"
        CODE_MIRROR_CLASS_NAME = "cm-content"

        MATPLOTLIB_CANVAS_CLASS_NAME = (
            "jupyter-widgets.jupyter-matplotlib-canvas-container"
        )
        CUE_BOX_CLASS_NAME = (
            "lm-Widget.p-Widget.lm-Panel.p-Panel.jupyter-widgets."
            "widget-container.widget-box.widget-vbox.scwidget-cue-box"
        )
        PRIVACY_BUTTON_CLASS_NAME = "bp3-button.bp3-small.jp-toast-button.jp-Button"
    elif JUPYTER_TYPE == "lab" and JUPYTER_VERSION >= Version("4.0.0"):
        BUTTON_CLASS_NAME = "lm-Widget.jupyter-widgets.jupyter-button.widget-button"
        OUTPUT_CLASS_NAME = (
            "lm-Widget.jp-RenderedText.jp-mod-trusted.jp-OutputArea-output"
        )

        TEXT_INPUT_CLASS_NAME = "widget-input"
        CODE_MIRROR_CLASS_NAME = "cm-content"

        MATPLOTLIB_CANVAS_CLASS_NAME = (
            "jupyter-widgets.jupyter-matplotlib-canvas-container"
        )
        CUE_BOX_CLASS_NAME = (
            "lm-Widget.lm-Panel.jupyter-widgets.widget-container."
            "widget-box.widget-vbox.scwidget-cue-box"
        )
        PRIVACY_BUTTON_CLASS_NAME = "jp-toast-button.jp-mod-small.jp-Button"
    else:
        raise ValueError(
            f"Tests do not support jupyter type {JUPYTER_TYPE!r} for version"
            f"{JUPYTER_VERSION!r}."
        )

    CUED_CUE_BOX_CLASS_NAME = f"{CUE_BOX_CLASS_NAME}.scwidget-cue-box--cue"

    RESET_CUE_BUTTON_CLASS_NAME = f"{BUTTON_CLASS_NAME}.scwidget-reset-cue-button"
    CUED_RESET_CUE_BUTTON_CLASS_NAME = (
        f"{RESET_CUE_BUTTON_CLASS_NAME}.scwidget-reset-cue-button--cue"
    )


def test_privacy_policy(selenium_driver):
    """
    The first time jupyter lab is started on a fresh installation a privacy popup
    appears that blocks any other button events. This test opens an arbitrary notebook
    to trigger the popup and click it away. This test needs to be run before the widget
    tests so the work correctly.
    """
    if JUPYTER_TYPE == "lab":
        driver = selenium_driver("tests/notebooks/widget_answers.ipynb")
        # we search for the button to appear so we can be sure that the privacy window
        # appeared
        privacy_buttons = driver.find_elements(By.CLASS_NAME, PRIVACY_BUTTON_CLASS_NAME)
        yes_button = None
        for button in privacy_buttons:
            if button.text == "Yes":
                yes_button = button

        if yes_button is not None:
            WebDriverWait(driver, 5).until(
                expected_conditions.element_to_be_clickable(yes_button)
            ).click()


def test_scwidgets_code_input(selenium_driver):
    """
    Tests the widget of the module code

    :param selenium_driver: see conftest.py
    """
    driver = selenium_driver("tests/notebooks/widget_scwidgets_code_input.ipynb")

    nb_cells = NotebookCellList(driver)
    # Test 1:
    # -------

    # Tests if change in function_body changed the widget view
    time.sleep(2)
    code_input_lines = nb_cells[1].find_elements(By.CLASS_NAME, CODE_MIRROR_CLASS_NAME)
    assert "return 'change'" in code_input_lines[-1].text


class TestExerciseWidgets:
    prefix = "pytest"

    def setup_method(self, method):
        """setup any state tied to the execution of the given method in a
        class.  setup_method is invoked for every test method of a class.
        """
        # in case the test stopped unexpectedly and the file still exists from last
        # run
        for filename in glob.glob(f"tests/notebooks/{self.prefix}-*.json"):
            os.remove(filename)

    def teardown_method(self, method):
        """teardown any state that was previously setup with a setup_method
        call.
        """
        for filename in glob.glob(f"tests/notebooks/{self.prefix}-*.json"):
            os.remove(filename)

    def test_widget_answer(self, selenium_driver):
        """
        Tests the save/loading mechanism of all widgets inheriting from ExerciseWidget

        :param selenium_driver: see conftest.py
        """

        driver = selenium_driver("tests/notebooks/widget_answers.ipynb")

        nb_cells = NotebookCellList(driver)

        # Test 1:
        # -------
        nb_cell = nb_cells[1]

        nb_cell.find_elements(By.CLASS_NAME, BUTTON_CLASS_NAME)
        answer_registry_buttons = nb_cell.find_elements(
            By.CLASS_NAME, BUTTON_CLASS_NAME
        )
        text_inputs = nb_cell.find_elements(By.CLASS_NAME, TEXT_INPUT_CLASS_NAME)

        # text create file button
        WebDriverWait(driver, 5).until(
            expected_conditions.element_to_be_clickable(answer_registry_buttons[0])
        )
        assert len(answer_registry_buttons) == 1
        create_file_button = answer_registry_buttons[0]
        assert create_file_button.text == "Create file"
        assert create_file_button.is_enabled()

        assert len(text_inputs) == 1
        text_input = text_inputs[0]
        text_input.send_keys("test-answers")
        # wait till typing finished
        WebDriverWait(driver, 5).until(
            expected_conditions.text_to_be_present_in_element_attribute(
                (By.CLASS_NAME, TEXT_INPUT_CLASS_NAME),
                "value",
                "test-answers",
            )
        )
        # wait till everything is sync with python kernel
        time.sleep(0.1)
        create_file_button.click()

        output = nb_cell.find_element(By.CLASS_NAME, OUTPUT_CLASS_NAME)
        assert output.text == "File 'pytest-test-answers.json' created and loaded."

        answer_registry_buttons = nb_cell.find_elements(
            By.CLASS_NAME, BUTTON_CLASS_NAME
        )
        assert len(answer_registry_buttons) == 3

        choose_other_file_button = answer_registry_buttons[1]
        save_all_answers_button = answer_registry_buttons[2]

        # test save all answers button
        # confirm
        # wait till everything is sync with python kernel
        time.sleep(0.1)
        WebDriverWait(driver, 5).until(
            expected_conditions.element_to_be_clickable(save_all_answers_button)
        ).click()
        # wait till old output is gone
        WebDriverWait(driver, 5).until(
            expected_conditions.invisibility_of_element_located(output)
        )
        output = nb_cell.find_element(By.CLASS_NAME, OUTPUT_CLASS_NAME)
        assert output.text == "Are you sure?"
        answer_registry_buttons = nb_cell.find_elements(
            By.CLASS_NAME, BUTTON_CLASS_NAME
        )
        answer_registry_buttons = nb_cell.find_elements(
            By.CLASS_NAME, BUTTON_CLASS_NAME
        )
        assert len(answer_registry_buttons) == 5
        confirm_button = answer_registry_buttons[3]
        WebDriverWait(driver, 5).until(
            expected_conditions.element_to_be_clickable(confirm_button)
        ).click()
        # wait till old output is gone
        WebDriverWait(driver, 5).until(
            expected_conditions.invisibility_of_element_located(output)
        )
        output = nb_cell.find_element(By.CLASS_NAME, OUTPUT_CLASS_NAME)
        assert (
            output.text == "All answers were saved in file 'pytest-test-answers.json'."
        )
        # cancel
        # wait till everything is sync with python kernel
        time.sleep(0.1)
        WebDriverWait(driver, 5).until(
            expected_conditions.element_to_be_clickable(save_all_answers_button)
        ).click()
        answer_registry_buttons = nb_cell.find_elements(
            By.CLASS_NAME, BUTTON_CLASS_NAME
        )
        assert len(answer_registry_buttons) == 5
        cancel_button = answer_registry_buttons[4]
        WebDriverWait(driver, 5).until(
            expected_conditions.element_to_be_clickable(cancel_button)
        ).click()

        # text choose other file button
        WebDriverWait(driver, 5).until(
            expected_conditions.element_to_be_clickable(choose_other_file_button)
        ).click()

        # text load file button
        answer_registry_buttons = nb_cell.find_elements(
            By.CLASS_NAME, BUTTON_CLASS_NAME
        )
        assert len(answer_registry_buttons) == 1
        WebDriverWait(driver, 5).until(
            expected_conditions.element_to_be_clickable(answer_registry_buttons[0])
        ).click()
        # wait till old output is gone
        WebDriverWait(driver, 5).until(
            expected_conditions.invisibility_of_element_located(output)
        )
        output = nb_cell.find_element(By.CLASS_NAME, OUTPUT_CLASS_NAME)
        assert output.text == "All answers loaded from file 'pytest-test-answers.json'."

        # TODO test interaction of ExerciseWidgets with ExerciseRegistry

        # Test 2:
        # -------
        # Test if TextExercise shows correct output

        nb_cell = nb_cells[2]

        text_inputs = nb_cell.find_elements(By.CLASS_NAME, TEXT_INPUT_CLASS_NAME)
        assert len(text_inputs) == 1
        text_input = text_inputs[0]

        answer_buttons = nb_cell.find_elements(
            By.CLASS_NAME, reset_cue_button_class_name("save", False)
        )

        assert len(answer_buttons) == 2
        assert answer_buttons[0].text == "Save answer"
        save_button = answer_buttons[0]
        assert answer_buttons[1].text == "Load answer"
        load_button = answer_buttons[1]

        # tests save button
        input_answer = "answer text"
        text_input.send_keys(input_answer)
        # wait till everything is sync with python kernel
        time.sleep(0.1)
        # wait for uncued box
        nb_cell.find_element(By.CLASS_NAME, cue_box_class_name("save", True))
        # check if there are two buttons are uncued
        reset_cue_buttons = nb_cell.find_elements(
            By.CLASS_NAME, reset_cue_button_class_name("save", True)
        )
        assert len(reset_cue_buttons) == 2
        assert text_input.get_attribute("value") == input_answer
        #
        WebDriverWait(driver, 1).until(
            expected_conditions.element_to_be_clickable(save_button)
        )
        from .conftest import JUPYTER_VERSION

        if JUPYTER_TYPE == "lab" and JUPYTER_VERSION >= Version("4.0.0"):
            # button is obscured so we need to click with action on the cell
            ActionChains(driver).click(nb_cell).perform()
        save_button.click()
        # wait for uncued box
        cue_box = nb_cell.find_element(By.CLASS_NAME, cue_box_class_name("save", False))
        assert "--cued" not in cue_box.get_attribute("class")
        # check if there are two buttons are uncued
        reset_cue_buttons = nb_cell.find_elements(
            By.CLASS_NAME, reset_cue_button_class_name("save", False)
        )
        assert all(
            [
                "--cued" not in button.get_attribute("class")
                for button in reset_cue_buttons
            ]
        )
        assert text_input.get_attribute("value") == input_answer
        output = nb_cell.find_element(By.CLASS_NAME, OUTPUT_CLASS_NAME)
        assert (
            output.text == "Exercise has been saved in file 'pytest-test-answers.json'."
        )

        # tests load button
        text_input.send_keys(" update")
        # wait till everything is sync with python kernel
        time.sleep(0.1)
        # wait for cued box
        reset_cue_buttons = nb_cell.find_elements(
            By.CLASS_NAME, reset_cue_button_class_name("save", True)
        )
        # check if there are two buttons are cued
        reset_cue_buttons = nb_cell.find_elements(
            By.CLASS_NAME, reset_cue_button_class_name("save", True)
        )
        assert len(reset_cue_buttons) == 2
        assert text_input.get_attribute("value") == input_answer + " update"
        #
        WebDriverWait(driver, 1).until(
            expected_conditions.element_to_be_clickable(load_button)
        ).click()
        # wait for uncued box
        cue_box = nb_cell.find_element(By.CLASS_NAME, cue_box_class_name("save", False))
        assert "--cued" not in cue_box.get_attribute("class")
        # check if there are two buttons are uncued
        reset_cue_buttons = nb_cell.find_elements(
            By.CLASS_NAME, reset_cue_button_class_name("save", False)
        )
        assert all(
            [
                "--cued" not in button.get_attribute("class")
                for button in reset_cue_buttons
            ]
        )
        # test if last test has been loaded
        WebDriverWait(driver, 5).until(
            expected_conditions.invisibility_of_element_located(output)
        )
        output = nb_cell.find_element(By.CLASS_NAME, OUTPUT_CLASS_NAME)
        assert (
            output.text
            == "Exercise has been loaded from file 'pytest-test-answers.json'."
        )
        assert text_input.get_attribute("value") == input_answer

        # Test 3:
        # -------
        # Test if CodeExercise shows correct output

        nb_cell = nb_cells[3]

        answer_buttons = nb_cell.find_elements(
            By.CLASS_NAME, reset_cue_button_class_name("save", False)
        )
        assert len(answer_buttons) == 2
        assert answer_buttons[0].text == "Save code"
        save_button = answer_buttons[0]
        assert answer_buttons[1].text == "Load code"
        load_button = answer_buttons[1]

        WebDriverWait(driver, 1).until(
            expected_conditions.element_to_be_clickable(save_button)
        ).click()

        output = nb_cell.find_element(By.CLASS_NAME, OUTPUT_CLASS_NAME)
        assert (
            output.text == "Exercise has been saved in file 'pytest-test-answers.json'."
        )
        # not cued
        cue_box = nb_cell.find_element(By.CLASS_NAME, cue_box_class_name("save", False))
        assert "--cued" not in cue_box.get_attribute("class")
        reset_cue_buttons = nb_cell.find_elements(
            By.CLASS_NAME, reset_cue_button_class_name("save", False)
        )
        assert all(
            [
                "--cued" not in button.get_attribute("class")
                for button in reset_cue_buttons
            ]
        )

        slider_input_box = nb_cell.find_element(By.CLASS_NAME, "widget-readout")
        slider_input_box.send_keys(Keys.BACKSPACE)
        slider_input_box.send_keys(Keys.BACKSPACE)
        slider_input_box.send_keys(0)
        slider_input_box.send_keys(Keys.ENTER)
        time.sleep(0.2)

        reset_cue_buttons = nb_cell.find_elements(
            By.CLASS_NAME, reset_cue_button_class_name("save", True)
        )
        assert len(reset_cue_buttons) == 2
        WebDriverWait(driver, 1).until(
            expected_conditions.element_to_be_clickable(load_button)
        ).click()
        WebDriverWait(driver, 5).until(
            expected_conditions.invisibility_of_element_located(output)
        )
        output = nb_cell.find_element(By.CLASS_NAME, OUTPUT_CLASS_NAME)
        assert (
            output.text
            == "Exercise has been loaded from file 'pytest-test-answers.json'."
        )
        # not cued
        cue_box = nb_cell.find_element(By.CLASS_NAME, cue_box_class_name("save", False))
        assert "--cued" not in cue_box.get_attribute("class")
        reset_cue_buttons = nb_cell.find_elements(
            By.CLASS_NAME, reset_cue_button_class_name("save", False)
        )
        assert all(
            [
                "--cued" not in button.get_attribute("class")
                for button in reset_cue_buttons
            ]
        )

        # Issue #22
        # Please add tests using send_keys works once it works with code input


@pytest.mark.parametrize(
    "nb_filename, mpl_backend",
    [
        ("tests/notebooks/widget_cue_figure-ipympl.ipynb", "ipympl"),
        ("tests/notebooks/widget_cue_figure-inline.ipynb", "inline"),
    ],
)
@pytest.mark.matplotlib
def test_widget_figure(selenium_driver, nb_filename, mpl_backend):
    """
    We separate the widget figure tests for different backends to different files
    because a backend switch within a running notebook causes undefined behavior
    of matplotlib (e.g. the figures are not anymore displayed when they should be)

    :param selenium_driver: see conftest.py
    """
    # TODO for inline i need to get the image directly from the panel
    driver = selenium_driver(nb_filename)

    nb_cells = NotebookCellList(driver)

    if "inline" == mpl_backend:
        by_type = By.TAG_NAME
        matplotlib_element_name = "img"

    elif "ipympl" == mpl_backend:
        by_type = By.CLASS_NAME
        matplotlib_element_name = MATPLOTLIB_CANVAS_CLASS_NAME
    else:
        raise ValueError(f"matplotlib backend {mpl_backend!r} is not known.")

    WebDriverWait(nb_cells[20], 5).until(
        expected_conditions.visibility_of_all_elements_located(
            (by_type, matplotlib_element_name),
        )
    )
    matplotlib_canvases = driver.find_elements(by_type, matplotlib_element_name)

    # sometimes the canvaeses are not ordered
    matplotlib_canvases = sorted(
        matplotlib_canvases, key=lambda canvas: canvas.location["y"]
    )

    def test_cue_figure(
        web_element: WebElement, ref_png_filename: str, mpl_backend: str, rtol=5e-2
    ):
        # images can have different white border and slightly
        # different shape so we cut the border of and resize them
        if mpl_backend == "inline":
            image = imread(
                base64.decodebytes(
                    web_element.get_property("src").split(",")[1].encode()
                )
            )
        elif mpl_backend == "ipympl":
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
    if mpl_backend == "inline":
        # in inline mode no image is shown by the first figure
        nb_expected_canvases = 4
        if JUPYTER_TYPE == "notebook":
            # in the notebook an image of the python logo is shown as first canvas, so
            # we remove it
            matplotlib_canvases = matplotlib_canvases[1:]
        elif JUPYTER_TYPE == "lab":
            # sometimes another canvas is shown that we filter out
            matplotlib_canvases = [
                canvas for canvas in matplotlib_canvases if canvas.is_displayed()
            ]

        assert (
            len(matplotlib_canvases) >= nb_expected_canvases
        ), "Not all matplotlib canvases have been correctly loaded."
        assert len(matplotlib_canvases) == nb_expected_canvases, (
            "Test that plt.show() does not show any plot "
            "failed. For each test there should be only "
            "one plot."
        )
        # no test for inline
        pass
    elif mpl_backend == "ipympl":
        nb_expected_canvases = 5
        assert (
            len(matplotlib_canvases) >= nb_expected_canvases
        ), "Not all matplotlib canvases have been correctly loaded."
        assert len(matplotlib_canvases) == nb_expected_canvases, (
            "Test that plt.show() does not show any plot "
            "failed. For each test there should be only "
            "one plot."
        )
        image = imread(matplotlib_canvases[0].screenshot_as_png)
        assert crop_const_color_borders(image).shape == (0, 0, 0), "Image is not white"
        matplotlib_canvases = matplotlib_canvases[1:]

    # Test 1.2
    test_cue_figure(
        matplotlib_canvases[0],
        "tests/screenshots/widget_cue_figure/empty_axis.png",
        mpl_backend,
    )
    # Test 1.3
    test_cue_figure(
        matplotlib_canvases[1],
        "tests/screenshots/widget_cue_figure/update_figure_plot.png",
        mpl_backend,
    )
    # Test 1.4
    test_cue_figure(
        matplotlib_canvases[2],
        "tests/screenshots/widget_cue_figure/update_figure_set.png",
        mpl_backend,
    )
    # Test 1.5
    test_cue_figure(
        matplotlib_canvases[3],
        "tests/screenshots/widget_cue_figure/update_figure_plot.png",
        mpl_backend,
    )


def test_widgets_cue(selenium_driver):
    """
    Basic test checks if button with description "Text" exists

    :param selenium_driver: see conftest.py
    """
    driver = selenium_driver("tests/notebooks/widgets_cue.ipynb")

    nb_cells = NotebookCellList(driver)
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

    nb_cells = NotebookCellList(driver)

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
        check_all_widgets_button = buttons[0]
        assert check_all_widgets_button.get_property("title") == "Check all widgets"
        set_all_references_button = buttons[1]
        assert set_all_references_button.get_property("title") == "Set all references"

        WebDriverWait(driver, 5).until(
            expected_conditions.element_to_be_clickable(check_all_widgets_button)
        )
        from .conftest import JUPYTER_VERSION

        if JUPYTER_TYPE == "lab" and JUPYTER_VERSION >= Version("4.0.0"):
            # button is obscured so we need to click with action on the cell
            ActionChains(driver).click(nb_cell).perform()
        check_all_widgets_button.click()
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
        ), (
            f"Expected: {expected_text_on_check_all_widgets} to be found in "
            f"{[output.text for output in outputs]}"
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
        ), (
            f"Expected: {expected_text_on_set_all_references} to be found in "
            f"{[output.text for output in outputs]}"
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
        ), (
            f"Expected: {expected_text_on_set_all_references_and_check} to be found in "
            f"{[output.text for output in outputs]}"
        )

    # Test 1.1 use_fingerprint=False, failing=False, buggy=False
    test_button_clicks(
        nb_cells[2],
        "Widget 1: ✓ (success)",
        "Successfully set all references",
        "Widget 1: ✓ (success)",
    )

    # Test 1.2 use_fingerprint=True, failing=False, buggy=False
    test_button_clicks(
        nb_cells[3],
        "Widget 1: ✓ (success)",
        "Successfully set all references",
        "Widget 1: ✓ (success)",
    )

    # Test 1.3 use_fingerprint=False, failing=False, buggy=False
    test_button_clicks(
        nb_cells[4],
        "Widget 1: 𐄂 (failed)",
        "Successfully set all references",
        "Widget 1: ✓ (success)",
    )

    # Test 1.4 use_fingerprint=False, failing=False, buggy=False
    test_button_clicks(
        nb_cells[5],
        "Widget 1: 𐄂 (failed)",
        "Successfully set all references",
        "Widget 1: ✓ (success)",
    )

    # Test 1.5 use_fingerprint=False, failing=False, buggy=True
    test_button_clicks(
        nb_cells[6],
        "Widget 1: ‼ (error)",
        "NameError: name 'bug' is not defined",
        "Widget 1: ‼ (error)",
    )


def test_widgets_code(selenium_driver):
    """
    Tests the widget of the module code

    :param selenium_driver: see conftest.py
    """
    driver = selenium_driver("tests/notebooks/widget_code_exercise.ipynb")

    nb_cells = NotebookCellList(driver)
    # Test 1:
    # -------
    WebDriverWait(driver, 5).until(
        expected_conditions.text_to_be_present_in_element_attribute(
            (By.CLASS_NAME, BUTTON_CLASS_NAME),
            "title",
            "Check Code",
        )
    )

    def test_code_exercise(
        nb_cell,
        expected_texts_on_update: List[str],
        expected_texts_on_check: List[str],
        include_code=True,
        include_checks=True,
        include_params=True,
        tunable_params=False,
        update_mode="manual",
    ):
        assert (
            not (tunable_params) or include_params
        ), "tunable_params requires include_params to be true"
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

        update_boxes = nb_cell.find_elements(
            By.CLASS_NAME, cue_box_class_name("update", False)
        )
        assert (
            len(update_boxes) == include_params + include_code
        ), f"Text from update boxes {[box.text for box in update_boxes]}"
        if include_code:
            update_code_input = update_boxes[0]
            assert "def function_to_check" in update_code_input.text
            assert scwidget_cue_box_class_name(
                "update", True
            ) in update_code_input.get_attribute("class")
        if include_params:
            parameter_panel = update_boxes[1] if include_code else update_boxes[0]
            # in these tests it should not be contain anything
            if tunable_params:
                assert scwidget_cue_box_class_name(
                    "update", include_code  # is cued only if code input present
                ) in parameter_panel.get_attribute("class")
            else:
                assert parameter_panel.size["height"] == 0

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
                assert sum([output.text.count(text) for output in outputs]) == 1, (
                    f"Did not find text {text!r} in outputs "
                    f"{[output.text for output in outputs]}"
                )

        ##################################################
        # asserts for behavior on click of update button #
        ##################################################

        if include_code or update_mode == "manual":
            update_buttons = nb_cell.find_elements(
                By.CLASS_NAME, reset_cue_button_class_name("update", False)
            )
            assert len(update_buttons) == 1
            update_button = update_buttons[0]
            assert update_button.text == "Run Code" if include_code else "Update"
            assert update_button.is_enabled()
            assert scwidget_reset_cue_button_class_name(
                "update", True
            ) in update_button.get_attribute("class")

            update_button.click()
            time.sleep(0.2)
            if include_code:
                assert not (
                    scwidget_cue_box_class_name("update", True)
                    in update_code_input.get_attribute("class")
                )
            assert not (
                scwidget_reset_cue_button_class_name("update", True)
                in update_button.get_attribute("class")
            )
            assert update_button.is_enabled()
            if include_params and tunable_params:
                assert not (
                    scwidget_cue_box_class_name("update", True)
                    in parameter_panel.get_attribute("class")
                )

        outputs = nb_cell.find_elements(By.CLASS_NAME, OUTPUT_CLASS_NAME)
        for text in expected_texts_on_update:
            assert sum([output.text.count(text) for output in outputs]) == 1, (
                f"Did not find text {text!r} in outputs "
                f"{[output.text for output in outputs]}"
            )

        if tunable_params:
            outputs = nb_cell.find_elements(By.CLASS_NAME, OUTPUT_CLASS_NAME)
            # In the code we print a text that adds another output
            before_parameter_change_text = "".join([output.text for output in outputs])

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

            if update_mode == "manual":
                assert scwidget_reset_cue_button_class_name(
                    "update", (update_mode == "manual")
                ) in update_button.get_attribute("class")

                # Check if output has changed only after click when manual
                outputs = nb_cell.find_elements(By.CLASS_NAME, OUTPUT_CLASS_NAME)
                # In the code we print a text that adds another output
                after_parameter_change_text = "".join(
                    [output.text for output in outputs]
                )
                assert before_parameter_change_text == after_parameter_change_text
                update_button.click()

            outputs = nb_cell.find_elements(By.CLASS_NAME, OUTPUT_CLASS_NAME)
            after_parameter_change_text = "".join([output.text for output in outputs])
            assert before_parameter_change_text != after_parameter_change_text

        #####################################
        # asserts on reaction on text input #
        #####################################
        if include_code:
            # expected_conditions.text_to_be_present_in_element does not work
            # for code input
            code_input_lines = nb_cell.find_elements(
                By.CLASS_NAME, CODE_MIRROR_CLASS_NAME
            )
            assert any(["return" in line.text for line in code_input_lines])
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

    # Test 1.1
    test_code_exercise(
        nb_cells[1],
        ["SomeText", "Output"],
        ["Check was successful"],
        include_code=True,
        include_checks=True,
        include_params=True,
        tunable_params=False,
        update_mode="manual",
    )

    # Test 1.2
    test_code_exercise(
        nb_cells[2],
        ["SomeText", "Output"],
        ["Check failed"],
        include_code=True,
        include_checks=True,
        include_params=True,
        tunable_params=False,
        update_mode="manual",
    )

    # Test 1.3
    test_code_exercise(
        nb_cells[3],
        ["SomeText", "NameError: name 'bug' is not defined"],
        ["NameError: name 'bug' is not defined"],
        include_code=True,
        include_checks=True,
        include_params=True,
        tunable_params=False,
        update_mode="manual",
    )
    # Test 1.4
    test_code_exercise(
        nb_cells[4],
        ["SomeText", "Output"],
        ["Check was successful"],
        include_code=True,
        include_checks=True,
        include_params=True,
        tunable_params=True,
        update_mode="manual",
    )

    # Test 1.5
    test_code_exercise(
        nb_cells[5],
        ["SomeText", "Output"],
        ["Check was successful"],
        include_code=True,
        include_checks=True,
        include_params=True,
        tunable_params=True,
        update_mode="continuous",
    )

    # Test 1.6
    test_code_exercise(
        nb_cells[6],
        ["SomeText", "Output"],
        ["Check was successful"],
        include_code=True,
        include_checks=True,
        include_params=True,
        tunable_params=True,
        update_mode="release",
    )

    # Test 2:
    # -------

    # Test 2.1
    # Test if update button is shown even if params are None
    test_code_exercise(
        nb_cells[7],
        ["SomeText", "Output:"],
        [],
        include_code=True,
        include_checks=False,
        include_params=False,
        tunable_params=False,
        update_mode="release",
    )

    # Test 2.2 TODO
    # Test 2.3 TODO

    # Test 2.4.1
    test_code_exercise(
        nb_cells[8],
        ["Output:", "{'x': 3}"],
        [],
        include_code=False,
        include_checks=False,
        include_params=True,
        tunable_params=True,
        update_mode="release",
    )

    # Test 2.4.2
    test_code_exercise(
        nb_cells[9],
        ["Output:", "{'x': 3}"],
        [],
        include_code=False,
        include_checks=False,
        include_params=True,
        tunable_params=True,
        update_mode="continuous",
    )

    # Test 2.4.3
    test_code_exercise(
        nb_cells[10],
        ["Output:", "{}"],
        [],
        include_code=False,
        include_checks=False,
        include_params=False,
        tunable_params=False,
        update_mode="manual",
    )

    # Test 2.4.4
    test_code_exercise(
        nb_cells[11],
        ["Output:", "{'x': 3}"],
        [],
        include_code=False,
        include_checks=False,
        include_params=True,
        tunable_params=True,
        update_mode="manual",
    )

    # TODO test only update, no check

    # Test 3:
    # -------
    # TODO test only checks, no run
