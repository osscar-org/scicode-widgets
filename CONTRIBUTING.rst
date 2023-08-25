Contributing
============

This is an instruction of the developer tools that help you contributing.

Running tests
-------------

Tests can be with run using

.. code-block:: bash

   tox -e tests

You can source the test environment of tox after a run using

.. code-block:: bash

    source .tox/tests/bin/activate

Converting notebook test files
##############################

The we store the notebooks as converted Python file using `jupytext` for the conversion
for better versioning

.. code-block:: bash

  jupytext tests/notebooks/*.py --to ipynb

Be aware that when runnng the tests with tox all `*.ipynb` are overwriten by their
corresponding `*.py` file. For example, the file `test_widget_cue_box.ipynb` is
overwritten by the conversion of `test_widget_cue_box.py` when running the test.


Running with UI
###############

We use selenium to test the widgets on user actions (like a button click). To run it in
in the CI where no display is available. We run the browsers in headless model to not
load the UI. For debugging a test however, it is often benificial to see what is
happening in the window. To run the tests with the browser UI please use

.. code-block:: bash

    pytest --driver Firefox

Port issues
###########

For the notebook server we fixed the port to 8815, if this port is not available you .
It can happen that notebook process is not properly killed and remains as zombie
process. You can check if a notebook with this port is already running using

.. code-block:: bash
    
   jupyter notebook list | grep 8815

or if some process is using it 

.. code-block:: bash

    netstat -l | grep 8815

Formatting code
---------------

Your code can be formatted using

.. code-block:: bash

   tox -e format

The formatting should fix most issues with linting, but sometimes you need to manually
fix some issues. To run the linter use

.. code-block:: bash

   tox -e lint


Building documentation
----------------------

To build the docs please use

.. code-block:: bash

   tox -e docs

To open the doc with for example firefox you can run

.. code-block:: bash

   firefox docs/build/html/index.html
