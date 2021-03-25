================
cesar-p - readme
================

CESAR-P (Combined Energy Simulation And Retrofitting - Python) calculates the energy demand for a bunch of buildings. 
The steps involved are gathering and calculating the parameters per building as BuildingModel objects, generation based on that the simulation input files (IDF), 
running the simulation with EnergyPlus and post-processing the results. All steps can be run in parallel on multiple cores.

*Inputs*

As a input, the building **footprint and height, year of construction, building type** (residential, office, ....)
and **hourly weather data** as EnergyPlus weather file (epw) are needed. 
If shading shall be considered **footprints and height of potential neighbours** must be provided.

*Outputs*

Default output is a summary with **annual energy demand** values (heating, cooling, domestic hot water) per building. **Hourly result series** can be queried on demand.
Further CESAR-P is capable of calculating **operational cost and emissions** based on the energy demand results. 
There is also the possibility to apply **retrofit measures** to the building construction and compare between different simulation runs. Output include besides the results 
a detailed Log with the **retrofit measures** along with pricing and embodied emission infromation.

Project Info
============

CESAR-P is developed at the **Urban energy systems Laboratory** at Empa (Swiss Federal Laboratories for Materials Science and Technology).

The predecessor tool of CESAR-P is CESAR, for more details see section References.

- Main contact & developer: Léonie Fierz - leonie.fierz(at)empa.ch

- Contributors

  - Ricardo Parreira da Silva (Passive Cooling: window shading and night ventilation)
  - Aaron Bojarski (package graphdb_access)
  - James Allan (Graph Database data for Archetypical constructions)
  - Sven Eggimann (shapefile parser for reading site vertices)

- Programming Language and Version: Python 3.8 

- License: CESAR-P is released under AGPLv3 open source license

- Dependencies

  - EnergyPlus (Version 8.5 to 9.3 supported)
  - Excel or OpenOffice (part of the Input Files are in xlsx format)
  - For Python dependencies see pyproject.toml and poetry.lock

- Documentation

  - Raw documentation markdown files under docs/source (see docs/source/development-commands.rst on how to build HTML documentation)


Project Status
===============
Released, development ongoing

For changelog see docs/source/history-releasenotes.rst

Bug-Tracking & Open Issues
---------------------------

Please send any Bugs reports or feature requests to leonie.fierz@empa.ch
Include follwoing information for a bug report.

- log files
- version of cesar-p and GIT SHA if it is not a released version
- your custom configuration
- any input files that could be connected to the problem


References
==========

The base methodology of CESAR-P regarding building simulation and retrofit is set up according to CESAR Matlab. For details refer to following documents:

- Danhong Wang, Jonas Landolt, Georgios Mavromatidis, Kristina Orehounig, Jan Carmeliet,
  CESAR: A bottom-up building stock modelling tool for Switzerland to address sustainable energy transformation strategies,
  Energy and Buildings, Volume 169, 2018, Pages 9-26, ISSN 0378-7788, https://doi.org/10.1016/j.enbuild.2018.03.020.
  (http://www.sciencedirect.com/science/article/pii/S0378778817337696)


Installation
============

EnergyPlus
----------

CESAR-P simulates the building energy demand with EnergyPlus. Currently supported versions are 8.5, 8.7, 8.8, 8.9, 9.0.1, 9.2, 9.3 (others can be added on demand).

CESAR-P currently uses EnergyPlus 9.3 as default. Default installation location is C:/EnergyPlusV9-3-0. 
Download and install EnergyPlus from https://energyplus.net/downloads.
You can configure the EnergyPlus version and executable path by setting following environment variables:

Set follwoing environment variables:

  ENERGYPLUS_VER

  ENERGYPLUS_EXE

e.g. for EPlus 9.3.0 that would be

  ENERGYPLUS_VER = 9.3.0

  ENERGYPLUS_EXE = "C:/EnergyPlusV9-3-0/energyplus.exe"



Python
------
CESAR-P requires Python 3.8. Download and Install from https://www.python.org/downloads/. 

If you already have a Python installation, do not tick 'Add Python X.Y to Path' during installation procedure.

Alternative: use Anaconda to setup different python versions, but keep in mind that if you will be using development IDE's conda is not always the most easy to handle.


A - Install (& Update) CESAR-P as python package
------------------------------------------------

- Open a shell, create & activate a virtual environment (based on the Python 3.8). E.g do:

  - Check if required python version is system default with 

    .. code-block::

      python -version

  - If NOT preceed python with the path to your python installation in the following commands

  - Create a new virtual environment (you can adapt the location of the venv as you wish - your home directory or any other location on the fileserver is not a sensible choice and might run out of space when installing all dependencies.

    .. code-block::

      python -m venv %TEMP%/venv-cesar-p

  - Then activate your venv with

    .. code-block::

      "/t%TEMP%/venv-cesar-p/Scripts/activate


- pip install the package

  - pip install cesar_p-X.X.X-py3-none-any.whl

- **Update** the package: redo the pip install command you used for installing the package


B - Editable mode / Development
-------------------------------

- Install poetry on your system: https://python-poetry.org/docs/#windows-powershell-install-instructions

- clone this cesar-p-core repository

  .. code-block::

    git clone https://github.com/hues-platform/cesar-p-core.git

- Open a shell and navigate to the root of the checked-out repository

- Check if required python version is system default with

  .. code-block::

    python -version

- If NOT, tell poetry which pyhton.exe to use with (point to installation directory and in case you use Anaconda to a environment using correct Python version):

  .. code-block::
    
    poetry env use PATH_TO_YOUR_CORRECT_VERISON_OF_PYTHON.EXE
    poetry env info

- Do now install the project and dependencies. The project sources are not copied to the site-packages but a link is established, 
  so editing the files will right away update your package in the virtual environment.
  
  .. code-block::

    poetry install

- Open the root folder of the checkout in your IDE and adapt python path to the virtual environment created by poetry.

- If you want to run without IDE, you can get a shell within the poetry environment with 

  .. code-block::

     poetry shell

  Or use poetry run THE_COMMAND to run commands such as pytest or running your main script.


- For commands how to run tests etc from command line see docs/source/


Usage
=====

The steps to set up a simulation run are:

1. Define configuration file 
2. Create a main script 
3. Run your main script 
4. Check outputs

1. Configuration
-----------------

To specify the options and inputs CESAR-P should use you create your configuration file, e.g. my_cesar_config.yml. 
The configuration is in YAML format, so keep an eye on the **indention**.
Generally, for each CESAR-P package, e.g. cesar.eplus_apdater or cesar.manager there is a default config file within the package.
You can set all the properties you find in those default configs in your project config to overwrite the default parameters.

Documentation on the configuration parameters can be found here:

- listing under docs/ConfigurationDescription.xlsx
- visual representation of options under docs/source/features/diagrams or in compiled documentation

There is a **simple validation** of the configuration done when the *SimulationManager* reads the config file, checking that the parameters defined exist, but not validating their values.


In the configuration you can use **pathes relative to the config-file location, or full pathes** as shown below. For more details on
the format of the input files please refer to **Input Files Format section in the documentation**.

Following an example configuration with the configuration you should check per project.
The entries having an *ACTIVE* option only need to be configured if set to *True*.
So in minimum, you have to set following entries to point to your project files:

- SITE_VERTICES_FILE: defines footprints and height for all the buildings of the site, including buildings only used as shading objects
- BLDG_FID_FILE: defines the list of building fids to be simulated
- BLDG_AGE_FILE: defines year of construction
- BLDG_TYPE_PER_BLDG_FILE: defines building type, e.g. SFH, MFH, OFFICE, ....
- SINGLE_SITE or SITE_PER_CH_COMMUNITY: specifies which EnergyPlus weather file(s) to use


.. code-block::

  MANAGER:
      NR_OF_PARALLEL_WORKERS: -1  # -1 means half of the available processors will be used
      SITE_VERTICES_FILE:
          PATH: "./SiteVertices.csv"
          SEPARATOR: ","
      BLDG_FID_FILE:
          PATH: "./Simple_BuildingInformation.csv"
          SEPARATOR: ","
      BLDG_AGE_FILE:
          PATH: "./Simple_BuildingInformation.csv"
          SEPARATOR: ","
      BLDG_TYPE_PER_BLDG_FILE:
          PATH: "./Simple_BuildingInformation.csv"
          SEPARATOR: ","
      DO_CALC_OP_EMISSIONS_AND_COSTS: False
      SINGLE_SITE:
          ACTIVE: True
          WEATHER_FILE: "./Zurich_2015.epw"

To connect to a remote GraphDB instance as source for construction, materials and constructional retrofit data instead of using the local GraphDB export (cesarp/graphdb_access/ressources/construction_and_material.ttl), adapt configuration to activate the remote access, and set your GraphDB user and password as environment variables. For the default SPARQL-Endpoint see cesarp/graphdb_access/graph_default_config.yml SPARQL_ENDPOINT

In your main configuration add:

.. code-block::

  GRAPHDB_ACCESS:
    LOCAL:
      ACTIVE: False      
    REMOTE:
      ACTIVE: True

Set following environment variables (! make sure to set those environment variables under the user section, as the password should be kept private!):

.. code-block::

  GRAPHDB_USER
  GRAPHDB_PASSWORD


**Migration from Cesar Matlab**
You can use the same SiteVertices.csv file as you did use for CESAR Matlab.
The "BuildingInformation.csv" can be reused as well. The only adaption you have to do is mapping the building type.
For more details check out  docs/source/faq.rst

2. Main Script
---------------

The main API classes are SimulationManager when having a single variant to simulate or ProjectManager if you have different simulation runs for the same site.

a. Create a cesarp.manager.SimulationManager instance and pass the path to the configuration file, an empty output folder and a instace of pint unit registry (see cesarp.common.init_unit_registry())
b. Call run_all_steps() on your SimulationManager instance
c. collect custom results, e.g. with hourly resolution

3. Run
-------
Make sure you have CESAR-P and EnergyPlus set up as described in the Installation.
Then, in the Python environment set up as described in the installation section, run your script.

4. Outputs
-----------
All outputs are saved in the output folder specified in your main script. Following content should be available after a successful run:

- **bldg_containers**: serialized *BuildingContainer* instances per building, containing all model parameters and simulation results. Those containers can be re-loaded into a SimulationManager instance for later analysis or re-execution.
- **idfs**: IDF input files for EnergyPlus along with profiles referenced
- **eplus_output**: raw output of EnergyPlus per building (that can be quite big!)
- **bldg_infos_model_generation.csvy**: building specific input parameters used during model generation as well as intermediate calculations
- **site_result_summary.csvy**: annual energy demand and optionally cost and emsission results. more details under docs/source/result-summary.rst


Debugging outputs:

- outputfolder/**eplus_error_summary.err**: all energy plus error files are merged together for easier error checking
- outputfolder/**eplus_simulation_timelog.csv**: timelog for EnergyPlus simulation per building.
- **TIMESTAMP-cesarp-logs**: log file per worker thread, helpful for debugging if model creation failes for all or some of the buildings
- **cesar-p-debug.log**: set up file-logging for cesar-p logger in your main script

It is good practice to check if EnergyPlus simulation run without failures and warnings either in the site_result_summary.csv and if necessary in eplus_error_summary.err.

If you want to read csvy files in a Python script, check out cesarp.common.csv_reader

Run CESAR-P with Docker
========================

- Install Docker, see https://docs.docker.com/docker-for-windows/install/
- Start Docker, once the Docker Ship appears in your Status-Bar, right click and choose "Switch to Linux containers..."
- Open command prompt in folder where you want the Cesar-P sources
- Checkout a copy of cesar-p:
  .. code-block::

    git clone https://github.com/hues-platform/cesar-p-core.git

- cd to the base project folder (containing the Dockerfile)
- follow instructions at the bottom of the Dockerfile


Development commands
===========================

See docs/source/development_commands.rst

Credits
=======

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
