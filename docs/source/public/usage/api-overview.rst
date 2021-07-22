API Overview
=================

The main API classes for cesar-p-core lib are listed in the table below.
The example scripts mentioned are located in the separate cesar-p-usage-examples repository (see :ref:`readme:cesar-p - readme` for the link).

=============================================================================================== ================================================= ==========================================================
class/module                                                                                    description                                        example
=============================================================================================== ================================================= ==========================================================
:py:class:`cesarp.manager.SimulationManager`                                                    Used for the simulation of a site                 simple_example/
                                                                                                                                                  simple_run.py
                                                                                                                                                  advanced_example/
                                                                                                                                                  basic_cesar_usage.py

:py:class:`cesarp.manager.ProjectManager`                                                       used to manage different runs/variants for the    advanced_example/
                                                                                                same site                                         multi_scenario/
                                                                                                                                                  multi_scenarios.py

:py:class:`cesarp.manager.BuildingContainer`                                                    this is the main data management class - one       advanced_example/
                                                                                                container is created per building,                 basic_cesar_usage.py::load_from_disk
                                                                                                each with the bldg model and results

:py:class:`cesarp.manager.BuildingModel`                                                        the CESAR-P representation for a building
                                                                                                containing all parameters needed to create the 
                                                                                                idf file

:py:class:`cesarp.retrofit.all_bldgs.SimpleRetrofitManager`                                     if you want to run a retrofit scenario with        advanced_example/
                                                                                                a simple retrofit strategy, namely retrofitting    retrofit_simple_example.py
                                                                                                all or part of the building elements for all 
                                                                                                buildings

:py:class:`cesarp.retrofit.energy_perspective_2050.EnergyPerspective2050RetrofitManager.py`     retrofit of the building site to match the         advanced_example/
                                                                                                energy 2050 strategy                               retrofit_energy_strategy2050_example.py

:py:class:`cesarp.retrofit.all_bldgs.RetrofitLog`                                               used to keep track of retrofit measures along
                                                                                                with thier cost and emissions, returned by
                                                                                                the retrofit manager's above                                                                                               
=============================================================================================== ================================================= ==========================================================



