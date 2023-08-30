.. _inputs:

===================
Inputs to Cesar-P
===================


Cesar-P has several inputs that are given in differents ways. This chapter should give an overview of the different values, where to find them, update them, and see them.

.. list-table:: Overview of Inputs
   :widths: 25 25 25 25
   :header-rows: 1

   * - Input Value
     - Where in Cesar-P
     - Source
     - Link 
   * - Building Footprint
     - Given by the user in each simulation. Specified in the config file.
     - User
     - `Github example <https://github.com/hues-platform/cesar-p-usage-examples/blob/master/example_project_files/SiteVertices.csv/>`_
   * - Building Information
     - Given by the user in each simulation. Specified in the config file.
     - User
     - `Github example <https://github.com/hues-platform/cesar-p-usage-examples/blob/master/example_project_files/BuildingInformation.csv/>`_
   * - Weather
     - Given by the user in each simulation. Specified in the config file. Can also use weather file per building. 
     - User
     - `Github example <https://github.com/hues-platform/cesar-p-usage-examples/blob/master/example_project_files/Zurich_2015.epw/>`_
   * - Site
     - Ground temperatures are defined in the config
     - 
     - `Site config on Github <https://github.com/hues-platform/cesar-p-core/blob/master/src/cesarp/site/site_config.yml/>`_
   * - Constructions
     - Constructions are defined as a GraphDB. They are stored in a ttl file within the graphdb_access subpackage. It includes: materials, constructions, shading, co2
     - Original Cesar version (with construction source from BFE_2016). Some constructions and age classed have been modified to agree more with the swiss building stock.
     - `TTL file on Github <https://github.com/hues-platform/cesar-p-core/blob/master/src/cesarp/graphdb_access/ressources/construction_and_material_data.ttl/>`_
   * - Retrofit
     - Retrofit costs are given in config files in the retrofit package. Emissions values are in the graph ttl file.
     - 
     - `Retrofit config on Github <https://github.com/hues-platform/cesar-p-core/blob/master/src/cesarp/retrofit/embodied/retrofit_embodied_config.yml/>`_
   * - Constructions details
     - Window frames are defined in the config. 
     - 
     - `Construction config on Github <https://github.com/hues-platform/cesar-p-core/blob/master/src/cesarp/construction/default_config.yml/>`_
   * - Operation SIA
     - Some operation parameters are given in the config. The schedules are in the SIA subpackage and created from SIA data.
     - SIA
     - `SIA config on Github <https://github.com/hues-platform/cesar-p-core/blob/master/src/cesarp/SIA2024/sia2024_default_config.yml/>`_ `SIA schedules on Github <https://github.com/hues-platform/cesar-p-core/tree/master/src/cesarp/SIA2024/generated_params/nominal/>`_
   * - Night vernilation and shading control
     - Given in OPERATION config
     - 
     - `Operation config on Github <https://github.com/hues-platform/cesar-p-core/blob/master/src/cesarp/operation/operation_default_config.yml/>`_
   * - CONFIG file
     - The config file really has a lot of parameters that can be tuned. In the root folder of the cesar-p-core repository there exits an overview of the config. Make sure to check it out.
     - Original Cesar version, SIA, KBOB, GEAK
     - `Config overview on Github <https://github.com/hues-platform/cesar-p-core/blob/master/cesar-p-config-overview.yaml/>`_
