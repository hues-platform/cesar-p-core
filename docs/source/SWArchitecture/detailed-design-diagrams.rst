.. _detailed-design-diagrams:

========================
Detailed Design diagrams
========================

Data model: BuildingModel
---------------------------

.. figure:: ./diagrams/05_BuildingModel_Detailed.jpg


Creating data models: BldgModelFactory
-----------------------------------------

.. figure:: ./diagrams/04_BuildingModelAndCreation.jpg

Initialization of BldgModelFactory
--------------------------------------

The BldgModelFactory is the central point which coordinates creation and initialization of the building models.
There is a single instance of this factory per worker process.

.. figure:: ./diagrams/08_BldgModelFactoryInit_sequence.jpg


Main workflow in SimulationManager
--------------------------------------

This diagrams illustrates the main CESAR-P workflow on a high level. From your main program, you can call each of those workflow steps separately if you wish to have more control over the process than just running everything in one sequence.

.. figure:: ./diagrams/09_main_workflow_sequence.jpg


Retrofit
--------------------------------------

This diagram gives an insight to the retrofit package to illustrate the classes responsible to perform the retrofit operations, namely selecting the buildings to retrofit and exchanging one or more construction element with its retrofitted construction. 
You also see which properties of the building model are relevant for the retrofitting.

.. figure:: ./diagrams/07_retrofit_class_diagram.jpg

Operational costs and emissions
--------------------------------------

The diagram gives an overview of the class structure used to calculate operational costs and emissions.

.. figure:: ./diagrams/06_feature_costs_and_emissions.jpg
