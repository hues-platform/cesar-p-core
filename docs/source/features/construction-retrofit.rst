
.. _construction_retrofit:

======================
Construction Retrofit
======================

- If you use construction retrofit, use GraphDB access as source for your constructions and materials (is the default)
- CO2 and PEN embodied emission must be assigned for all materials used, otherwise CESAR-P will run into an exception.

Use either cesarp.retrofit.all_bldgs.SimpleRetrofitManager or cesarp.retrofti.energy_perspective_2050.EnergyPerspective2050RetrofitManager 
instead of the cesarp.manager.SimulationManager to control the simulation and retrofit workflow. 

The two retrofit manager classes mentioned are examples and you can implement your own retrofit manager 
according to those if other retrofit strategies are needed.

Please find software design diagrams for retrofit package under 
:ref:`detailed-design-diagrams`

Embodied Emissions and Costs
============================
Retrofit costs are not included in the GraphDB data as those costs are quite variable over time.

For CESAR-P retrofit costs for construction retrofit were transfered from the Cesar Matlab implementation.

The emission and cost factors determined are /m2. The areas of the different building elements is calculated by
CESAR-P based on the geometry that was constructed. Code: cesar.geometry.area_calculator

Note that emissions and costs are stored in the RetrofitLog instance hold by your xxxRetrofitManager class. 
The user is currently responsible to aggregate those cost and emissions logged per retrofit measure 
in the way he needs (e.g. per building element, per building, ...)

Wall, Roof, Ground
------------------


Embodied CO2 emissions and non-renewable PEN:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
See cesar.retrofit.RetrofitEmbodiedEmissions

The emissions are assigned on the material level and defined in the database. Parameters needed for each used material are:
- embodied co2 emission in kg CO2eq / kg  
- embodied non-renewable PEN in MJ Oileq / kg
- density

Further, the thickness of each layer is defined in the database as well. With all this information the emissions per m2 of a certain constructions can be defined.

There are some material having no emission factors, namely the Gases (used between window glasses) and AirGaps
(modeled as OpaqueMaterial without mass, used in roof constructions).

Values used are according to **KBOB 2014** (were transfered construction retrofit Excel DB of CESAR Matlab).

Costs
~~~~~~~
Costs are implemented according to **GEAK 2014** data, thus on the level of layers and not on material level as the embodied
emissions. As those cost factors change quite fast, data is not included in the database but stored in cesar.retrofit.ressources insulation_retrofit_costs_geak_2014.yml.
If custom cost values shall be used point to a file with your own cost factors in your config ["RETROFIT"]["INSULATION_COST_LOOKUP"]

Layer function of insulation layers is used assigned by an algorithm described in the following flow chart and implemented in cesarp.graphdb_access:

.. figure:: ./diagrams/LayerFunction-mapping.jpg

Windows
-------
The emission factors used as default are according to KBOB 2014 and the cost factors accroding to GEAK 2014. 

The embodied emissions for windows are combined between emissions for the frame and emissions for the glass.

The embodied emissions for the frame, as CESAR-P currently supports only one default standard frame, are stored in
configuration for cesar.construction (["CONSTRUCTION"]["FIXED_WINDOW_FRAME_CONSTRUCTION_PARAMETERS
"]["embodied_co2_emission_per_m2"] and ["embodied_non_renewable_primary_energy_per_m2"]).

For the window construction embodied emissions are stored in the GraphDB on the level of the glass construction (not
on material level as for wall, roof, ground).

System retrofit and operational data
============================================

Retrofit respectively replacement of the system for domestic hot water and space heating is only done partially. 
- System efficiency: are base on the "simulation year", so if you change this parameter for a retrofit scenario, efficiencies are updated accordingly
- Energy carrier for domestic hot water and space heating remain unchanged
- Operational parameters remain unchanged, thus better efficiency e.g. for appliances and lighting are not considered