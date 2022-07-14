Development Installation
========================

Follow those installation instructions to be able to develop new features or bug fixes for cesar-p-core libarary.
The project is set up using poetry for dependency management and packaging. 
Note that installing the package as editable with -e option of pip is not supported.


- Install EnergyPlus and Pyhton according to the general installation guide :ref:`installation:Installation`

- Install poetry on your system according to https://python-poetry.org/docs/#windows-powershell-install-instructionsS

- Clone the cesar-p-core repository (do git lfs install at least once on your machine, otherwise all files managed with LFS are not downloaded)

    .. code-block::

        git lfs install
        git clone https://github.com/hues-platform/cesar-p-core.git

    
    Note for UES Lab members: do checkout the cesar-p-core repository from gitlab.empa.ch

- Check an probably activate correct Python version for poetry (in case you have multiple Python installations)

  - Open a shell and navigate to the root of the checked-out repository

    .. code-block::

        cd cesar-p-core

  - Check if required python version is system default with

    .. code-block::

        python -version

  - If NOT, tell poetry which pyhton.exe to use with. Point to installation directory of Python version and in case you use Anaconda to an environment using correct Python version.
    You must be within the project/reposiotry, here cesar-p-core, in order that the poetry env use command works:

    .. code-block::
        
        poetry env use PATH_TO_YOUR_CORRECT_VERISON_OF_PYTHON.EXE
        poetry env info

- Install cesar-p-core and dependencies
  Note: Poetry will create a new virtual environment and installs all dependencies as defined in poetry.lock.
  The cesar-p-core sources are not copied to the site-packages of your virtual environment but a link is established, 
  so editing the files in your checkout will right away be reflected in the virtual environment.
  
  .. code-block::

    poetry install

- You have three ways to run commands in the virtual environment created by poetry: 

  1. Open a shell using this poetry command:
  
     .. code-block::

        poetry shell

  2. use *poetry run THE_COMMAND*, e.g. to run all tests you would do
    
     .. code-block::

        poetry run pytest tests

  3. Set up your IDE to use the virtual environment created by poetry. See details below.

- If you want to make sure the installation went correctly and changes in the sources checkout will be reflected in your venv: 
  Navigate to YOUR_VENV\lib\site-packages\ check that there should be a cesar_p-1.x.x.dist-info folder, but no folder named cesar_p
  or do a pip list and check if there is a path pointing to your repository after the cesar-p version.

- For commands how to run tests etc from command line see :ref:`development/development-commands:Development commands`

IDE Setup - Visual studio code
-------------------------------

Steps to run or edit cesar-p in Visual Studio Code IDE

- Install Python extension (empa internal: refer to python-cicd template projct, section IDE - Visual Studio Code)
- Open the root folder of the checkout in your IDE and adapt python path to the virtual environment created by poetry.
- Open a terminal within Visual Studio Code and allow commands to be executed (otherwise you will get an error when trying to activate a python virtual environment):

  .. code-block::

    Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope CurrentUser

- Press Ctrl+Shift+P, then type respectively choose "Python: Select Interpreter" and choose the python.exe from the virtual environment you created in the step before
- Note that before running a script in the terminal of VSCode, you have to open a new terminal window - unfortunately the chosen virtual environment does not get 
  activated automatically for the Terminal on startup of the IDE

