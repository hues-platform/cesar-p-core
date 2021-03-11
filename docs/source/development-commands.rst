Development commands
=====================

Unittesting
-------------------
Before running tests from console, make sure your local or installed cesar module is available in the PATH.
You can acomplish this by using poetry. Be aware that you have to repeat this step when you changed files in your IDE.
I recommend to use your IDE support for running tests during development and just use the command line if you want to check the coverage.
Anyway, to add cesar as a lib to your current environment do

.. code-block:: console

    poetry install

Then, to run your test against this installed version:

.. code-block:: console

    pytest tests

Checking code coverage

.. code-block:: console

    pytest tests --cov
    coverage html

The second command creates a nice report to folder htmlcov, which you can explore in any browser.

Static code checker / Linting
--------------------------------------

.. code-block::

    flake8

Configuration resides in .flake8

Typing check
-------------
The type hints are not checked during runtime, however you can do a consistency check with mypy

.. code-block::

    mypy src

Code formatting
-------------------

Format your source files automatically with black (after doing this, most static checker errors thrown by flake8 should disappear)
To format all files in src folder, run:

.. code-block:: console

  black src

A few configuration settings for black are set in pyproject.toml

Doku generation
-------------------

To generate api doc structure, only run on major changes

.. code-block:: console

    sphinx-apidoc -efM -o docs/source/api src/cesarp

To generate the docu:

.. code-block:: console

    sphinx-build docs/source docs/html

UML diagrams
-------------------

The UML Diagrams were created with UMLet, which you can download from https://www.umlet.com/