GraphDB - Add or update data
==============================

Local data (TTL file)
-----------------------

In case you do not have a GraphDB Server instance for managing the archetype data and you need to fix 
for example a infiltration value for a certain archetype, you can change this in the 
Turtle file (cesarp.graphdb_access.ressources construction_and_material_data.ttl) directly.

1. Copy the TTL file to your project (skip if it is a bugfix that should be pushed to cesar-p-core repository)
2. The TTL file is a text file - search e.g. for infiltration and you will find the matching spots in the file
   you have to go through some general definitions at the beginning, but ultimatley you will find the places where the infiltration rate is actually assigned to the archetype
   the line would look something like 
   <http://uesl_data/sources/archetypes/1918_SFH_Archetype> :hasInfiltrationRate "0.551666667 ACH"^^cdt:ucum;
   Just adapt that value and save the file.
3. Point to your project-specific TTL file in your project YAML config (skip if you bugfix cesar-p-core): 
   
   .. code-block::
   
      GRAPHDB_ACCESS:
      LOCAL: 
        ACTIVE: True 
        PATH: "THE_NEW_LOCATION/construction_and_material_data.ttl"


GraphDB Server
--------------

# TODO 

Describe process how to add a new constructional archetype