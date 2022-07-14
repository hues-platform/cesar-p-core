Construction and Operation
==========================

.. figure:: ./diagrams/Inputs_Config_ConstructionOperation.png


Construction - Internal ceiling/floor
--------------------------------------

As with EnergyPlus we split the building into Zones, we need to define a pair of internal ceiling and floor, so the floor and ceiling 
are assigned to the zone they are facing (https://bigladdersoftware.com/epx/docs/9-3/input-output-reference/group-thermal-zone-description-geometry.html#buildingsurfacedetailed)
In the archetype, only the ceiling construction is specified. The mirrored construction is created on-the-fly when writing the IDF.


Custom assignment of operation parameters
------------------------------------------

Built in options for assigning operational parameters is either the same parameter set for all buildings (A) or parameters according to SIA2024-2016 based on the building type (B).

Full configuration set for option A, fixed parameters, is:

.. code-block::

    MANAGER:
        BUILDING_OPERATION_FACTORY_CLASS: "cesarp.operation.fixed.FixedBuildingOperationFactory.FixedBuildingOperationFactory"
    OPERATION:
        FIXED: # to enable FIXED operation parameters set config MANAGER - BUILDING_OPERATION_FACTORY_CLASS to "cesarp.operation.fixed.FixedBuildingOperationFactory.FixedBuildingOperationFactory"
            FLOOR_AREA_PER_PERSON: 25.64103 m**2
            SCHED_OCCUPANCY_PATH: "./occupancy.csv"
            SCHED_ACTIVITY_PATH: "./activity.csv"
            SCHED_APPLIANCES_PATH: "./appliances.csv"
            APPLIANCES_WATT_PER_ZONE_AREA: 6.4 W/m**2
            SCHED_LIGHTING_PATH: "./lighting.csv"
            LIGHTING_WATT_PER_ZONE_AREA: 10.3104 W/m**2
            SCHED_DHW_PATH: "./dhw.csv"
            DHW_WATTS_PER_ZONE_AREA: 4.216667 W/m**2
            SCHED_THERMOSTAT_HEATING: "./thermostat_heating.csv"
            SCHED_THERMOSTAT_COOLING: "./thermostat_cooling.csv"
            OUTDOOR_AIR_FLOW_PER_ZONE_FLOOR_AREA: 1.297222e-03 m**3/(s * m**2)
            SCHED_VENTILATION: "./ventilation.csv"
            SCHED_PROPS:
            NUM_OF_HOURS: 8760
            SEPARATOR: ","
            NUM_OF_HEADER_ROWS: 0
            DATA_COLUMN: 1

In the OPERATION block you only specify the parameters where you do not want to use the default profile files or values. Relative pathes ("./xxx") are considered to be relative to the location of your configuration file.


Full configuration set for option B, SIA2024 is:

.. code-block::

    MANAGER:
        BUILDING_OPERATION_FACTORY_CLASS: "cesarp.SIA2024.SIA2024Facade.SIA2024Facade"  # this is actually the default
        SIA2024_VARIABILITY: False # variability for demand values and profiles generated with SIA2024 module, False is the default
        BLDG_TYPE_PER_BLDG_FILE:
            PATH: "TBD_BLDG_TYPE_PER_BLDG_FILE.csv"  # point to project file
            SEPARATOR: ","  # , is the default
            LABELS:  # change if you do not use the default column headers
                gis_fid: "ORIG_FID" 
                sia_bldg_type: "SIA2024BuildingType"
        

To allow the user to apply a **project, custom specific assignment** of operational parameters, an own Factory class can be used.

.. code-block::

    MANAGER:
        BUILDING_OPERATION_FACTORY_CLASS: "MyBuildingOperationFactory"

Your Factory class, here MyBuildingOperationFactory, needs to meet following criteria:

- initialization method (__init__) having identical parameters as cesarp.operation.fixed.FixedBuildingOperationFactory.FixedBuildingOperationFactory
- satisfy protocol definition cesarp.manager.manager_protocols.BuildingOperationFactoryProtocol
- make sure your class is in the PYTHONPATH, e.g. in the same folder as your main script is (make sure to change to that directory when calling the script)

CESAR-P also allows that you specify different sets of operational parameters for different floors of you buidling (see cesarp.model.BuildingOperationMapping)


Custom assignment of constructional Archetype
----------------------------------------------

Per default, the constructional archetype is assigned to each building depending on its building age.

Full configuration is:

.. code-block::

    MANAGER:
        BLDG_AGE_FILE:
            PATH: "TBD_BLDG_AGE_FILE.csv"
            SEPARATOR: ","
            LABELS:
                gis_fid: "ORIG_FID"
                year_of_construction: "BuildingAge"
    GRAPHDB_ACCESS:
        ARCHETYPE_CONSTRUCTION_FACTORY_CLASS: "cesarp.graphdb_access.GraphDBArchetypicalConstructionFactory.GraphDBArchetypicalConstructionFactory"  # this is also the default

        

You can create your own Factory class to implement a project specific mapping of the Archetype. For example, you can specify an Archetype URI existing in the GraphDB for each of your buildings. 
To configure your own class, set following configuration:

.. code-block::

    GRAPHDB_ACCESS:
        ARCHETYPE_CONSTRUCTION_FACTORY_CLASS: "YourConstructionArchetypeFactory.YourConstructionArchetypeFactory"
        # activate connection to remote GraphDB instead of using the local TTL-file if you did add new Archetypes to the DB (alternative is to export a TTL and point to that)
        LOCAL:
            ACTIVE: False
        REMOTE:
            ACTIVE: True
            SPARQL_ENDPOINT: "http://GRAPH_DB_URL:PORT/repositories/YOUR_REPO_ENDPOINT"


Your Factory needs to meet following criteria:

- initialization method (__init__) having identical parameters as cesarp.graphdb_access.GraphDBArchetypicalConstructionFactory.GraphDBArchetypicalConstructionFactory
- satisfy protocol definition cesarp.construction.construction_protocols.ArchetypicalConstructionFactoryProtocol
- make sure your class is in the PYTHONPATH, e.g. in the same folder as your main script is (make sure to change to that directory when calling the script)
