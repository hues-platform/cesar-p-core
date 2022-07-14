================
cesar-p - readme
================

CESAR-P (Combined Energy Simulation And Retrofitting - Python) calculates the energy demand for a district or other site with
a bottom-up approach by using the building simulation tool EnergyPlus. The steps involved are gathering and calculating 
the parameters per building on your site, generation of the simulation input files (IDF), 
running the simulation with EnergyPlus and post-processing the results. All steps can be run in parallel.

You can also create your customized pipeline to combine simulation of archetypical buildings with a clustering and upscaling
for a large amount of buildings, e.g. whole Switzerland. You would use CESAR-P for the simulation part, but the clustering 
and upscaling are not included in CESAR-P so far.

*Inputs*

As a input, the building **footprint and height, year of construction, building type** (residential, office, ....)
and **hourly weather data** as EnergyPlus weather file (epw) are needed. 
If shading shall be considered **footprints and height of potential neighbours** must be provided.

*Outputs*

Default output is a summary with **annual energy demand** values (heating, cooling, domestic hot water) per building. **Hourly result series** can be queried on demand.
Further CESAR-P is capable of calculating **operational cost and emissions** based on the energy demand results. 
There is also the possibility to apply **retrofit measures** to the building construction and compare between different simulation runs. Output include besides the results 
a detailed Log with the **retrofit measures** along with pricing and embodied emission infromation.

The target audience of the software are energy planners, energy utilities, cities and researchers to identify the time-resolved 
energy consumption of buildings at large scale to successfully in-tegrate renewable energy technologies in buildings and to 
develop energy masterplans for neighborhoods and cities.

Full documentation: https://cesar-p-core.readthedocs.io/en/latest/


Project Info
============

CESAR-P is developed at the **Urban energy systems Laboratory** at Empa (Swiss Federal Laboratories for Materials Science and Technology).

The whole project is named **CESAR-P**. The repository for the code library is **cesar-p-core**, 
the python base code package name **cesarp** (avoiding the - to be sure not to run into problems in includes etc) 
and the wheel/PyPi package name you use during installation **cesar-p**.

The predecessor tool of CESAR-P is CESAR, for more details see section References.

- Main contact: Kristina Orehounig

- Contributors

  - Léonie Fierz (main developer until July 2021)
  - Ricardo Parreira da Silva (Passive Cooling: window shading and night ventilation)
  - Aaron Bojarski (package graphdb_access)
  - James Allan (Graph Database data for Archetypical constructions)
  - Sven Eggimann (shapefile parser for reading site vertices)

- Programming Language and Version: 

  - Python 3.8

- Supported platforms:
  
  - Windows (development platform)
  - Linux (Ubuntu system used for testing/CI)
  - Mac (not tested)


- License: CESAR-P is released under AGPLv3 open source license. Contact UES Lab to discuss about other licensing terms.

- Dependencies

  - EnergyPlus (Version 8.5 to 9.5 supported)
  - Excel or OpenOffice (part of the Input Files are in xlsx format)
  - For Python dependencies see pyproject.toml and poetry.lock

- Documentation

  - https://cesar-p-core.readthedocs.io/en/latest/
  - Raw documentation markdown files under docs/source/public


Project Status
===============
Released, development ongoing

Changelog: https://cesar-p-core.readthedocs.io/en/latest/history-releasenotes.html

Bug-Tracking & Open Issues
---------------------------

Please file an issue on https://github.com/hues-platform/cesar-p-core/issues

Include follwoing information for a bug report:

* log files
* version of cesar-p-core
* your custom configuration
* any input files that could be connected to the problem
* instead of providing your configuration and input files separately, you can use the cesarp.manager.ProjectSaver to create a ZIP file of your simulation run

References
==========

The base methodology of CESAR-P regarding building simulation and retrofit is set up according to CESAR Matlab. For details refer to following documents:

* Danhong Wang, Jonas Landolt, Georgios Mavromatidis, Kristina Orehounig, Jan Carmeliet,
  CESAR: A bottom-up building stock modelling tool for Switzerland to address sustainable energy transformation strategies,
  Energy and Buildings, Volume 169, 2018, Pages 9-26, ISSN 0378-7788, https://doi.org/10.1016/j.enbuild.2018.03.020.
  (http://www.sciencedirect.com/science/article/pii/S0378778817337696)


* To cite the CESAR-P OpenSource version:

  Leonie Fierz, Urban Energy Systems Lab, Empa. (2021, April 13). hues-platform/cesar-p-core: 1.3.0 (Version 1.3.0).  Zenodo. http://doi.org/10.5281/zenodo.4682881
  
  Leonie Fierz, Urban Energy Systems Lab, Empa. (2021, July 30). hues-platform/cesar-p-core: CESAR-P-V2.0.1 (CESAR-P-V2.0.1). Zenodo. https://doi.org/10.5281/zenodo.5148531


Installation & Usage
========================

- Installation guide: https://cesar-p-core.readthedocs.io/en/latest/installation.html
- Usage instructions: https://cesar-p-core.readthedocs.io/en/latest/usage/index.html
- Usage examples: https://github.com/hues-platform/cesar-p-usage-examples


Contributing
============

You are welcome to open issues reporting bugs or creating pull requests with bugfixes or new features!

We develop and test this library on our internal GitLab and synchronize new versions to GitHub.

Before submitting your contribution as a pull request please make sure tests run through and code 
complies with formatting and typing rules checked with the tools described under 
https://cesar-p-core.readthedocs.io/en/latest/development/development-commands.html

Credits
=======

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
