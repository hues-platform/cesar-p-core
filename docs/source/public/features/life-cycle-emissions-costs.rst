Life cycle emissions and costs
===================================

There are several aspects regarding emissions and costs

**operational emissions and costs**

- implemented in package cesarp.emissons_cost
- as a input energy source/carrier for domestic hotwater and space heating are needed (as csv input file, see configuration of cesarp.manager)
- all cost and emission factors are collected in the cesarp.energy_strategy package

**embodied emissions data**

- in the construction database (GraphDB) and the CESAR-P data model embodied emissions can attached either to a Construction as a whole (wall, roof, ...) or to a material.
- the source of those values is the KBOB database
- those attributes are not populated for all the construction elements and materials, so if you want to build up on them be aware that they might be None in the data model classes.

**retrofit costs and emissions**

- for each retrofit measure "carried out" by a retrofit manager class, the costs and emissions are calculated and written to the retrofit log. implementation of embodied cost and emission calculations are defined in package cesarp.retrofit.embodied
- in custom retrofit manager classes you can use this log to aggregate the retrofit emissions and costs as you want. the default retrofit managers return the sum and write the detailed log to disk.
- cost factors are read from cesarp.retrofit.embodied.ressources and are based on GEAK data
- emissions are read from the construction database, see above
- more details see :ref:`development/SWArchitecture/detailed-design-diagrams:Retrofit`

**life cycle emission and costs for new buildings**

- emission and costs data attached to the construction elements in the data model need to be evaluated on a per-project bases (the reason is that we currently do not have data for all constructional archetypes in the same manner, e.g. either on material level for materails used in retrofitted constructions or on construction level...)
- to get the per-construction-element areas of a building, you can use the methods in cesarp.geometry.area_calculator. pass in the BuildingShapeDetailed stored in the BuildingModel for each of your buildings.
