========================
History & Release Notes
========================

.. _version_numbers:

Version Numbers
---------------
MAJOR.MINOR.PATCH.a0

- MAJOR: big new functionality, workflow change, changes in the API (e.g. in config entries which must be set for a project or changes in SimulationManager/ProjectManager/RetrofitManager which are not backward-compatible)
- MINOR: new features / change or bugfix with major influence on generated models and/or simulation results, minor API change e.g. in a not-often used retrofit manager class or in BldgModelFactory.
- PATCH: bugfix or small usability change, for example a fix in SimulationManager for some file handling error
- aX/alphaX: Suffix that markes the version as alpha version, being developed (respectively on master branch) - you won't find those version listed in the Tags/release, as they are constantly changed and do not mark a specific state. (That scheme is introduced  from 1.1.0 onwards) 
             DO NOT USE a version with an alpha-suffix if you need a traceable version of cesar-p-core!

For all released Version there is a Tag/Release in GitLab.

2.3.1
-----
- minor updates for JOSS paper

2.3.0
-----

- added paper folder which contains published papers and added JOSS paper
- cleanup of documentation
- updating all dependencies


Bugfixes

- set default arguments to None and initialize correctly afterwards. Otherwise could result in unexpected behavior
- fixed pandas future warning


2.2.0
-----

- duplicated materials were removed from the GraphDB dataset. Names were changed to simplify. All attributes stayed the same. 
- GraphDB content gets now exported to the zip file if running with remote endpoint (#129)

Bugfixes

- rdflib version 5 did not run anymore. Updated to 6. 
- zip creatin failed (#131)


2.1.0
-----

- added feature to map a weather file per building (#122)
- removed idf_constructions_db_access package (#106)
- moved shading materials to GraphDB dataset (#77)

Bugfixes

- fixed error of ArchetypicalBuildingConstruction in GraphDBArchetypicalConstructionFactory (#126)

2.0.1
-----

- fix missing dependency to requests (dependency of rdflib)
- update CESAR-P version in cesarp/SIA2024/ressources/generated_profiles (profiles values do not change, just that version pointer was outdated)

2.0.0
-----

- You may not be able to load building containers created with CESAR-p < 2.0.0 and may require to downgrade cesar-p-core version or jsonpickle to be able to deserialize or even deserialize manually.
  This is due to an update to jsonpickle 2.0, which breaks reading serialized BuildingContainer json files saved with older cesar-p-core versions resp with jsonpickle < 2.0.0 
  The version of the BuildingContainer is updated from 3 to 4 and a CesarpException is raised if a old container is loaded informing about the possible options mentioned above. 
- Changed API of SimpleRetrofitManager - the *add_retrofit_case* method now returns the sum of costs and emissions instead of the full retrofit log, parameter name fixed from szenario_name to scenario_name
- Fix name of module for EPlusEioResultAnalyzer (was previously EPlusEioResultReader)
- updating all dependencies (especially pandas library from 0.25 to 1.3, changing from xlrd to openpyxl) - CESAR-P is now compatible with Python 3.8.9 and 3.9.0 
  (CI is still running on 3.8 as there is no official Python package for Ubuntu:20.04 LTS release yet, but as the gitlab-ci.yml just installs latest Python, it will update when it is available)
- updating to EnergyPlus 9.5 (from 9.3) - no changes in IDF files nor significant changes in simulation results (<0.1%)
- updating CI pipeline to create empa internal docu and PDF for documentation
- optional feature to collect solar potential for your buildings (#107)
- updating and re-arranging documentation
- groundfloor area is added to bldg_infos_used output file (#82)

Bugfixes

- limit windows to 95% of wall width, raise exception if window is higher than wall (#112)
- allow for adding all result frequencies in OUTPUT_METER and OUTPUT_VAR in config for cesarp.eplus_adapter package; it was not possible to add them to 
  the main config because validation did not find them in the default config (now added to default config and code handles if they have no entries)


1.3.0
-----

First open source version of CESAR-P
