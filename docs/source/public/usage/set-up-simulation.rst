Set up simulation
==================

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
A overview of the parameters of all packages can be found under :ref:`usage/configuration-overview:Configuration overview`. 
Details about how the configuration works can be found under :ref:`usage/configuration-structure:Configuration structure`. on the configuration parameters can be found here:
Further, a good overview of the possible configurations and parametrization of the building models you find 
under Features :ref:`features/construction-and-operation:Construction and Operation`, :ref:`features/geometry:Building Geometry`, :ref:`features/neighbourhood:Neighbourhood`.

There is a **simple validation** of the configuration done when the *SimulationManager* reads the config file, 
checking that the parameters defined exist, but not validating their values.

In the configuration you can use **pathes relative to the config-file location, or full pathes** as shown below. For more details on
the format of the input files please refer to **:ref:`input-files-format` section in the documentation**.

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
      # -1 means half of the available processors will be used
      NR_OF_PARALLEL_WORKERS: -1
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
      SPARQL_ENDPOINT: "YOUR_GRAPHDB_ENDPOINT"     

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

a. Create a cesarp.manager.SimulationManager instance and pass the path to the configuration file, an empty output folder and a instance of pint unit registry (see cesarp.common.init_unit_registry())
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

For details about the result summary check out :ref:`usage/result-summary:Result Summary`


   