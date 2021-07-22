System scope and context
========================

.. figure:: ./diagrams/03_SystemContext.jpg

================ =========== ===========
Component         In/Output   Interface
================ =========== ===========
GIS                 In          csv or shp files with building id, footprint vertices and height
Metenorm            In          hourly data as epw
SIA Guidelines      In          xlsx file
EnergyPlus          Out         IDF, csv files, E+ config
EnergyPlus          In          csv, hourly energy demand
EHub                Out         csv, hourly energy demand per building
================ =========== ===========

Integration with a UES Lab database should be considered. As the database, its exact purpose and technical implementation is not yet defined the CESAR core should in a first step be developed using its own data sources and data storage where needed and later be integrated with the UES Lab database. For example, the possibility of using CityGML files as building shape and characteristics input could be a direction to go.