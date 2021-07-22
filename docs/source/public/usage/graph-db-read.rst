GraphDB - Read data
======================

To use constructional archetypes defined in the database, which enables you to use the retrofit module, GRAPH_DB has to be activated with:

.. code-block:: console

    CONSTRUCTION:
        CONSTRUCTION_DB: "GRAPH_DB"


This is the default so you don't need to add anything to your project's config.

Local File (TTL)
-----------------
The data from the GraphDB Server is exported to a local Turtle file (TTL) which can be queried, so you do not need to set up the connection to the GraphDB.
This default data source makes also sure that any input values you used are traced with the cesar-p version you are using.

Check config is as following either in your project's main yml config or in cesarp/graphdb/graph_default_config.yml (default):

.. code-block:: console

    GRAPHDB_ACCES:
        REMOTE:
            ACTIVE: False
        LOCAL:
            ACTIVE: True


Remote connection to GraphDB server
-----------------------------------

Activate remote access and set endpoint in your project config: 

.. code-block:: console

    GRAPHDB_ACCES:
        REMOTE:
            ACTIVE: True
            SPARQL_ENDPOINT: xxxx
        LOCAL:
            ACTIVE: False

Set following environment variables (! make sure to set those environment variables under the user section, as the password should be kept private!):

.. code-block::

  GRAPHDB_USER
  GRAPHDB_PASSWORD


Note that if traceability of the data used is necessary in your project, that you need to make sure that either the GraphDB Server instance
provides the backup and data traceability (so you could revert to the DB state you used in your project) or you do a data export from the 
server and store that with your project.