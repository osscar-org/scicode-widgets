import os
import subprocess
import time
from urllib.parse import urljoin

import pytest
from packaging.version import Version
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

# Can be "notebook" for jupyter notebook or "lab" for jupyter lab
JUPYTER_TYPE = os.environ["JUPYTER_TYPE"] if "JUPYTER_TYPE" in os.environ else "lab"
# Because for the tests frontend elements are retrieved by class names which change
# between versions, these veriable are change depending on the version. The version is
# automatically determined on initialization of tests
JUPYTER_VERSION = None


def get_jupyter_version() -> Version:
    """
    Function so we can update the jupyter version during initialization
    and use it in other files
    """
    global JUPYTER_VERSION
    if JUPYTER_VERSION is None:
        raise ValueError("JUPYTER_VERSION was not correctly on initialization")
    return JUPYTER_VERSION


@pytest.fixture(scope="session")
def notebook_service():
    global JUPYTER_VERSION

    if JUPYTER_TYPE not in ["lab", "notebook"]:
        raise ValueError(
            f"Tests do not support jupyter type {JUPYTER_TYPE!r}. Please use"
            " 'notebook' or 'lab'."
        )

    # some hard coded port and token
    port = 8815
    token = "fe47337ccb5b331e3d26a36b92112664af06462e511f66bb"
    jupyter_version = subprocess.check_output(
        ["jupyter", f"{JUPYTER_TYPE}", "--version"]
    )
    # convert to string
    JUPYTER_VERSION = Version(jupyter_version.decode().replace("\n", ""))

    jupyter_process = subprocess.Popen(
        [
            "jupyter",
            f"{JUPYTER_TYPE}",
            f"--NotebookApp.token={token}",
            "--no-browser",
            f"--port={port}",
        ],
        stdout=subprocess.PIPE,
        shell=False,
    )
    # give some time to let the jupyter notebook start
    time.sleep(5)
    url = f"http://localhost:{port}"

    yield url, token

    # teardown juypter notebook
    os.system(f"jupyter {JUPYTER_TYPE} stop {port}")
    time.sleep(2)
    os.system(f"kill {jupyter_process.pid}")


@pytest.fixture(scope="function")
def selenium_driver(notebook_service, selenium):
    """
    Returns a function that starts a notebooks at a given path
    """

    def _selenium_driver(nb_path):
        """
        :param nb_path: jupyter notebook path
        """
        global JUPYTER_TYPE
        url, token = notebook_service

        if JUPYTER_TYPE == "lab":
            nb_path_prefix = "lab/tree"
        elif JUPYTER_TYPE == "notebook":
            nb_path_prefix = "tree"
        else:
            raise ValueError(
                f"Tests do not support jupyter type {JUPYTER_TYPE!r}. Please use"
                " 'notebook' or 'lab'."
            )

        # nb_path_prefix =
        url_with_token = urljoin(url, f"{nb_path_prefix}/{nb_path}?token={token}")
        selenium.get(f"{url_with_token}")
        selenium.implicitly_wait(10)
        window_width = 1280
        window_height = 1024
        selenium.set_window_size(window_width, window_height)

        # Click on restart kernel button
        # ------------------------------

        # jupyter lab < 4
        if JUPYTER_TYPE == "lab":
            if get_jupyter_version() < Version("4.0.0"):
                restart_kernel_button_class_name = (
                    "bp3-button.bp3-minimal.jp-ToolbarButtonComponent.minimal.jp-Button"
                )
                restart_kernel_button_title_attribute = (
                    "Restart Kernel and Run All Cells…"
                )
            else:
                restart_kernel_button_class_name = "jp-ToolbarButtonComponent"
                restart_kernel_button_title_attribute = (
                    "Restart the kernel and run all cells"
                )
        elif JUPYTER_TYPE == "notebook":
            if get_jupyter_version() < Version("7.0.0"):
                restart_kernel_button_class_name = "btn.btn-default"
                restart_kernel_button_title_attribute = (
                    "restart the kernel, then re-run the whole notebook (with dialog)"
                )
            else:
                restart_kernel_button_class_name = (
                    "jp-ToolbarButtonComponent.jp-mod-minimal.jp-Button"
                )
                restart_kernel_button_title_attribute = (
                    "Restart the kernel and run all cells"
                )

        # the code below imitates this code which cannot find the button
        # I think it is because the button is hidden by another element
        # WebDriverWait(driver, 5).until(
        #    expected_conditions.text_to_be_present_in_element_attribute(
        #        (By.CLASS_NAME, restart_kernel_button_class_name),
        #        "title",
        #        restart_kernel_button_title_attribute
        #    )
        # )
        restart_kernel_button = None
        waiting_time = 10
        start = time.time()

        while restart_kernel_button is None and time.time() - start < waiting_time:
            buttons = selenium.find_elements(
                By.CLASS_NAME, restart_kernel_button_class_name
            )
            for button in buttons:
                try:
                    title = button.get_attribute("title")
                    if (
                        button.is_displayed()
                        and title == restart_kernel_button_title_attribute
                    ):
                        restart_kernel_button = button
                except StaleElementReferenceException:
                    # element is not ready, go sleep
                    continue

            time.sleep(0.1)
        if restart_kernel_button is None:
            raise ValueError(
                f"{restart_kernel_button_title_attribute!r} button not found."
            )
        restart_kernel_button.click()

        # Click on confirm restart dialog
        # -------------------------------

        if JUPYTER_TYPE == "lab":
            if get_jupyter_version() < Version("4.0.0"):
                restart_button_class_name = (
                    "jp-Dialog-button.jp-mod-accept.jp-mod-warn.jp-mod-styled"
                )
                restart_button_text = "Restart"
            else:
                restart_button_class_name = (
                    "jp-Dialog-button.jp-mod-accept.jp-mod-warn.jp-mod-styled"
                )
                restart_button_text = "Restart"
        elif JUPYTER_TYPE == "notebook":
            if get_jupyter_version() < Version("7.0.0"):
                restart_button_class_name = "btn.btn-default.btn-sm.btn-danger"
                restart_button_text = "Restart and Run All Cells"
            else:
                restart_button_class_name = "jp-Dialog-buttonLabel"
                restart_button_text = "Restart"

        # the code below imitates this code which cannot find the button
        # I think it is because the button is hidden by another element
        # WebDriverWait(driver, 5).until(
        #    expected_conditions.text_to_be_present_in_element(
        #        (By.CLASS_NAME, restart_button_class_name),
        #        restart_button_text
        #    )
        # )

        restart_button = None
        waiting_time = 10
        start = time.time()
        while restart_button is None and time.time() - start < waiting_time:
            buttons = selenium.find_elements(By.CLASS_NAME, restart_button_class_name)
            for button in buttons:
                if button.text == restart_button_text:
                    restart_button = button
            time.sleep(0.1)

        if restart_button is None:
            raise ValueError(f"{restart_button_text!r} button not found.")
        restart_button.click()

        WebDriverWait(selenium, 10).until(
            expected_conditions.text_to_be_present_in_element_attribute(
                (By.CLASS_NAME, "jp-Notebook-ExecutionIndicator"), "data-status", "idle"
            )
        )

        return selenium

    return _selenium_driver


@pytest.fixture
def firefox_options(firefox_options):
    """
    Options that are passed to firefox when running `pytest --driver Firefox`
    """
    options = os.environ.get("SELENIUM_FIREFOX_DRIVER_ARGS", "")
    if options != "":
        for option in options.split(" "):
            firefox_options.add_argument(option)
    return firefox_options
