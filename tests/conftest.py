import os
import subprocess
import time
from urllib.parse import urljoin

import pytest
from selenium.webdriver.common.action_chains import ActionChains
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

        # wait until menu item "Run" is available
        run_menu_item = [
            element
            for element in selenium.find_elements(By.CLASS_NAME, "lm-MenuBar-item")
            if element.text == "Run"
        ][0]
        WebDriverWait(selenium, 10).until(
            expected_conditions.element_to_be_clickable(run_menu_item)
        )

        # the actions run all cells of the notebook
        run_all_cells = ActionChains(selenium)
        # waits till notebook fully loaded because clickable is not enough
        run_all_cells.pause(5)
        # moves the cursor to the "Run" menu item
        run_all_cells.move_to_element(run_menu_item)
        run_all_cells.click()
        run_all_cells.pause(2)  # waits till submenu opens
        # moves the cursor to the "Run All Cells" submenu item
        run_all_cells.move_by_offset(0, 235.0)
        run_all_cells.click()
        run_all_cells.perform()

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
