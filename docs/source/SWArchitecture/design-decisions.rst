Design decisions
================

Datastorage
------------
There are following data that need to be handled

- building input data (site specific)
- building characteristics (predefined, general)
- SIA and other energy strategy information (predefined, general)
- simulation metadata (inputs used, data of simulation, project scope)
- energy plus raw simulation results (hourly data quite big)
- accumulated simulation results (could acutually also be re-calculated form raw simulation results)
- weather input files (site specific, some predefined data available)

The different predefined input data might be extended by several users, thus it should be easy to exchange and extend those datasets. Furthermore some metadata should be provided alongside to be able to trace back the datasources used for a certain simulation.

A relational database seems not flexible enough to extend with own data, in addition SQL and database handling might not be known for all users making the process of adding and sharing data complicated. Furthermore, a temporary extension or testing of new datasets before sharing would need some rather sophisticated user access handling per dataset. Furthermore such a database could not easily be shared with researchers outside of EMPA.
As there is the Lab porject to build a GraphDB for data management including building data and construction archetypes, constructional Archetypes used for CESAR-P shall be set up within that DB. 
CESAR-P shall still be able to run stand alone without DB access, thus the option must be given to read that data locally from a file, which can be accomplished with querying from a TTL file over SPARQL.

The current Matlab version is based on different Excel and CSV input files. As most of the data is tabular, CSV matches the needs better than YAML, JSON or XML. CSV lacks the possibility of adding metadata. To address this, the https://csvy.org/ (2019-10-18) initiative proposes to add metadata to CSV by adding a YAML header. This solution seems to be the most practical for our purpose. Data exchange can be done by just copying new files to appropriate directories.

As input data should be understood and also extendable by the users, YAML is prefered over JSON and XML as it is the most human readable format of those three. As the data formated as YAML is not big, the slower parsing compared to JSON can be neglected. XML would have even better control over the data definition, but as also the functionalities will be extended probably needing more input data, the flexibility without having a fixed schema is appreciated.

If a simulation history per user is a required feature, the metadata for a simulation could either be stored in a YAML file or in a SQLite DB. The decision for this datastorage shall be taken when there is a more detailed specification of this feature.

Decision: CSV with YAML frontmatter (Metadata header), when appropriate pure YAML for input data; GraphDB (with option to read from local TTL file) for constructional archetype.

EPPY
----
The Python EPPY library offers a good set of functionality to create IDF files, run E+ simulations and also process the E+ outputs. Quite a lot of this functionality will be used by CESAR. EPPY is licensed under MIT License allowing for redestribution.

The API is well documented on https://eppy.readthedocs.io/en/latest/index.html (2019-10-18)
eppy is a PyPi package, see https://pypi.org/project/eppy/ (2019-10-18)

Its development seems to be still ongoing, as the latest release was on 2019-10-14.

Decision: use EPPY

Shapelib/Shaply
---------------
Those library address handling of geometric transformations and calculations. The libraries seem to be quite OK documented. 
Manipulations for converting the footprint shapes of the buildings to the IDF floor/wall objects are not all coverd, thus this transformation will be implemented within CESAR-P.
Anyhow, some functions could be useful, for sure calculating the area of a polygon which we need to get the groundfloor area of a building.

Decision: use Shapely where useful
