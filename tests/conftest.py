import pytest
import os
import subprocess
from urllib.parse import urljoin
import time

import selenium.webdriver.support.expected_conditions as ec
from requests.exceptions import ConnectionError
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains

@pytest.fixture(scope="session")
def notebook_service():
    # TODO need to check if port is unavailable
    port = 8815
    token = "fe47337ccb5b331e3d26a36b92112664af06462e511f66bb"
    jupyter_process = subprocess.Popen(["jupyter", "notebook", f"--NotebookApp.token={token}", "--no-browser", f"--port={port}"], stdout=subprocess.PIPE, shell=False)
    # give some time to start jupyter notebook
    time.sleep(5)
    url = f"http://localhost:{port}"

    yield url, token

    # teardown juypter notebook
    os.system(f"kill {jupyter_process.pid}")


# pytest-selenium
@pytest.fixture(scope="function")
def selenium_driver(notebook_service, selenium):
    def _selenium_driver(nb_path):
        url, token = notebook_service
        url_with_token = urljoin(
            url, f"tree/{nb_path}?token={token}"
        )
        selenium.get(f"{url_with_token}")
        # By default, let's allow selenium functions to retry for 10s
        # till a given element is loaded, see:
        # https://selenium-python.readthedocs.io/waits.html#implicit-waits
        selenium.implicitly_wait(10)
        window_width = 800
        window_height = 600
        selenium.set_window_size(window_width, window_height)

        run_element = [element for element in selenium.find_elements(By.CLASS_NAME, 'lm-MenuBar-item')
                if element.text == "Run"][0]
        WebDriverWait(selenium, 10).until(
            ec.element_to_be_clickable(run_element)
        )
        time.sleep(2)
        actions = ActionChains(selenium)
        actions.move_to_element(run_element); actions.click(); actions.pause(1); actions.move_by_offset(0, 235.0); actions.click(); actions.perform()


        # Menu does not work because of movement
        #run_element = [element for element in selenium.find_elements(By.CLASS_NAME, 'lm-MenuBar-item')
        #        if element.text == "Run"][0]

        #WebDriverWait(selenium, 100).until(
        #    ec.element_to_be_clickable(run_element)
        #).click()

        #run_all_element = [element for element in selenium.find_elements(By.CLASS_NAME, 'lm-Menu-item') if element.text == "Run All Cells"][0]
        #WebDriverWait(selenium, 100).until(
        #    ec.element_to_be_clickable(run_all_element)
        #)
        #breakpoint()
        #actions = ActionChains(selenium); actions.move_to_element(run_all_element); actions.click(on_element=run_all_element); actions.perform()

        #actions = ActionChains(selenium)
        #actions.move_to_element(run_all_element)
        ##actions.click(on_element=run_all_element)
        #actions.click()
        #actions.perform()


        #selenium.find_element(By.ID, "ipython-main-app")
        #selenium.find_element(By.ID, "notebook-container")
        #WebDriverWait(selenium, 100).until(
        #    ec.invisibility_of_element((By.ID, "appmode-busy"))
        #)

        #time.sleep(5) # TODO
        #because another element <div> obscures it
        #visibility_of_element
        #selenium.find_elements(By.CLASS_NAME, 'lm-MenuBar-item')[i]
        #.text
        #lm-Widget lm-MenuBar jp-scrollbar-tiny 
        #WebDriverWait(selenium, 100).until(
        #    ec.element_to_be_clickable((By.XPATH, '//Div[text()="Run"]'))
        #)
        #WebDriverWait(selenium, 100).until(
        #    ec.invisibility_of_element_located((By.XPATH, '//Div[text()="Run"]'))
        #).click()

        #[selenium.find_element(By.XPA, '//Div[text()="Run"]')
        #selenium.find_element(By.XPATH, '//Div[text()="Run"]').click() 
        #WebDriverWait(selenium, 100).until(
        #    ec.element_to_be_clickable((By.CLASS_NAME, '//Div[text()="Run All Cells"]'))
        #)
        #selenium.find_element(By.XPATH, '//Div[text()="Run"]').click()
        #.click()
        #selenium.find_element(By.XPATH, '//Div[text()="Run All Cells"]').click()

        #selenium.find_element(By.ID, "ipython-main-app")
        #class=""
        #data-status="busy"

        #selenium.find_element(By.ID, "notebook-container")
        #WebDriverWait(selenium, 100).until(
        #    ec.invisibility_of_element((By.ID, "appmode-busy"))
        #)


        ## Run all cells
        #selenium.find_element(By.XPATH, '//Div[text()="Run All Cells"]')
        #buttons = selenium.find_elements(By.CLASS_NAME, 'jp-ToolbarButtonComponent.jp-mod-minimal.jp-Button')
        #breakpoint()
        #WebDriverWait(selenium, 100).until(
        #    ec.element_to_be_clickable((By.XPATH, '//Div[text()="Run All Cells"]'))
        #).click()
        #[button
        #    for button in buttons
        #    if button.get_property("title") == "Restart the kernel and run all cells"][0]
        ##if len(buttons) > 1:
        ##    raise ValueError("Multiple run buttons")
        ##button = buttons[0]
        #ActionChains(selenium).move_to_element(button)
        #WebDriverWait(selenium, 100).until(
        #    ec.element_to_be_clickable(button)
        #).click()
        ##button.click()
        ##time.sleep(1)
        #button = selenium.find_element(By.CLASS_NAME, "jp-Dialog-button.jp-mod-accept.jp-mod-warn.jp-mod-styled")
        #WebDriverWait(selenium, 100).until(
        #    ec.element_to_be_clickable(button)
        #).click()


        #WebDriverWait(selenium, 10).until(
        #    ec.invisibility_of_element((By.CLASS_NAME, "jp-Notebook-ExecutionIndicator"))
        #)

        return selenium

    return _selenium_driver

#def selenium_driver(notebook_service, nb_path):
#    url, token = notebook_service
#    url_with_token = urljoin(
#        url, f"{nb_path}?token={token}"
#    )
#    selenium.get(f"{url_with_token}")
#    # By default, let's allow selenium functions to retry for 10s
#    # till a given element is loaded, see:
#    # https://selenium-python.readthedocs.io/waits.html#implicit-waits
#    selenium.implicitly_wait(10)
#    window_width = 800
#    window_height = 600
#    selenium.set_window_size(window_width, window_height)
#
#    selenium.find_element(By.ID, "ipython-main-app")
#    selenium.find_element(By.ID, "notebook-container")
#
#    return selenium


@pytest.fixture
def firefox_options(firefox_options):
    firefox_options.add_argument("--headless")
    return firefox_options
