import os
import subprocess
import time
from urllib.parse import urljoin

import pytest
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait


@pytest.fixture(scope="session")
def notebook_service():
    # some hard coded port and token
    port = 8815
    token = "fe47337ccb5b331e3d26a36b92112664af06462e511f66bb"
    jupyter_process = subprocess.Popen(
        [
            "jupyter",
            "notebook",
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
    os.system(f"jupyter notebook stop {port}")
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
        url, token = notebook_service
        url_with_token = urljoin(url, f"tree/{nb_path}?token={token}")
        selenium.get(f"{url_with_token}")
        selenium.implicitly_wait(10)
        window_width = 800
        window_height = 600
        selenium.set_window_size(window_width, window_height)

        # the code below imitates this code which cannot find the button
        # I think it is because the button is hidden by another element
        # WebDriverWait(driver, 5).until(
        #    expected_conditions.text_to_be_present_in_element_attribute(
        #        (By.CLASS_NAME, "jp-ToolbarButtonComponent.jp-mod-minimal.jp-Button"),
        #        "title",
        #        "Restart the kernel and run all cells"
        #    )
        # )
        restart_kernel_button = None
        waiting_time = 10
        start = time.time()
        while restart_kernel_button is None and time.time() - start < waiting_time:
            # does not work for older notebook versions
            buttons = selenium.find_elements(
                By.CLASS_NAME, "jp-ToolbarButtonComponent.jp-mod-minimal.jp-Button"
            )
            for button in buttons:
                try:
                    title = button.get_attribute("title")
                    if title == "Restart the kernel and run all cells":
                        restart_kernel_button = button
                except StaleElementReferenceException:
                    # element is not ready, go sleep
                    continue
            time.sleep(0.1)
        if restart_kernel_button is None:
            raise ValueError('"Restart the kernel and run all cells" button not found.')
        restart_kernel_button.click()

        # the code below imitates this code which cannot find the button
        # I think it is because the button is hidden by another element
        # WebDriverWait(driver, 5).until(
        #    expected_conditions.text_to_be_present_in_element(
        #        (By.CLASS_NAME, "jp-Dialog-buttonLabel"),
        #        "Restart"
        #    )
        # )
        restart_button = None
        waiting_time = 10
        start = time.time()
        while restart_button is None and time.time() - start < waiting_time:
            buttons = selenium.find_elements(By.CLASS_NAME, "jp-Dialog-buttonLabel")
            for button in buttons:
                if button.text == "Restart":
                    restart_button = button
            time.sleep(0.1)
        if restart_button is None:
            raise ValueError('"Restart" button not found.')
        restart_button.click()

        # wait until everything has been run
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
