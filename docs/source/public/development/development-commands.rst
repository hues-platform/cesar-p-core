Development commands
=====================

Before running tests from console, make sure your local or installed cesar-p module is available in the PYTHON_PATH.
This should be the case if you did follow the :ref:`development/development-installation/Development Installation`.

Make sure you do have the python environment where you have your cesar-p-core development installation active 
(most probably this is the environment that poetry did create for you) before working with any of the 
commands outlined below.

Unittesting
-------------------

The tests depending on EnergyPlus assume that you have EnergyPlus 9.5.0 installed and configured in the environment 
variables ENERGYPLUS_EXE and ENERGYPLUS_VER.

I recommend to use your IDE support for running tests during development. 
For the coverage there is no IDE support I know of, but maybe there is something out there as well.

To run your test:

.. code-block:: console

    pytest tests

Checking code coverage

.. code-block:: console

    pytest tests --cov
    coverage html

The second command creates a nice report to folder htmlcov, which you can explore in any browser.

**For debugging**: the test cases (e.g. tests/test_eplus_adapter/test_eplus_adapter.py) that compare e.g. a IDF file created against an expected one have a 
pytest.fixture method creating a result folder. In the normal run each test should clean up the files created, so after the *yield* that result folder is deleted. 
If such a test fails it is best to manually compare the generated file with the expected and update the expected if needed. For this, 
just **comment out the shutil.rmtree line in the pytest.fixture function after the yield**.


Code formatting
-------------------

Format your source files automatically with black (after doing this, most static checker errors thrown by flake8 should disappear)
To format all files in src folder, run:

.. code-block:: console

  black src

A few configuration settings for black are set in pyproject.toml


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


Doku generation
-------------------

To generate the HTML docu:

.. code-block:: console

    cd docs/source/public
    sphinx-build . ../../html

The generation of the rst files for the the Code/API documentation is included in the command above (see conf.py for details).
The reason is that the API autodocumentation must be generated form conf.py to work on readthedocs. Also the pathes in conf.py 
have been adapted to work on PyPi, thus you must now navigate to the docs root folder to execute shpinx-build...

To generate PDF docu:

Sphinx offers two ways to create a PDF documentation. The first is rst2pdf. I tried it out, but the result was not convincing and
especially for the API documentation there were a lot of overflow errors. The second is generating LaTex sources and create a PDF,
this is how I did set it up.

Install LaTex on your system (e.g. Live Tex on Windows). Make sure pdflatex command is available.
Also do install "make" (on Windows e.g. by using chocolatey, see https://community.chocolatey.org/packages/make)

The two steps to generate the PDF then are

.. code-block:: console

    cd docs/source
    sphinx-build -b latex . ./_latex    
    cd _latex
    make

The PDF is then in the folder *_latex*

UML diagrams
-------------------

The UML Diagrams were created with UMLet, which you can download from https://www.umlet.com/