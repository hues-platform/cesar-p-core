.. _input_files_format:

===================
Input Files Format
===================


Some general information about how input files are handled/configured are given here.
The format of the main input files for the vertices of all buildings on the site and
the per-building information are explained here.

If details on other input files are needed, such as the input files for the energy strategy or SIA2024, please let me
know and I will add a description. You can also just check the files included in CESAR-P to see what is expected.

General
-------
All files used are passed as parameters in the YML configuration.
Normally, a file configuration block looks like:

.. code-block::

    BLDG_INSTALLATION_FILE:
        PATH: "YOUR_FILE.csvy"
        SEPARATOR: ";"
        LABELS:
            gis_fid: "ORIG_FID"
            dhw_energy_carrier: "ECarrierDHW"
            heating_energy_carrier: "ECarrierHeating"

- **PATH**: see below for relative/absolute path
- **SEPARATOR**: for csv(y) files you can specify here the separator used ";" is prefered over "," as it gives less
  troubles with YAML headers containing "," in the text
- **LABELS**: specify which colums must be contained in that file - you can name the columns as you like and map the
  name in the list. The key is the internal name used in CESAR-P, the value is the column heading that should be used
  in your file. So in that example, the file is expected to have the columns: ORIG_FID; ECarrierDHW, ECarrierHeating

For CESAR-P, the order of the columns in the input file is not important. You can also have more columns than
needed in a certain input file, unexpected columns will be ignored.

If y CSV/Y or Excel file is required you see in the value set by default for the PATH. For the SiteVertices you can
pass a csv or shp, see details below.

Absolute vs Relative Pathes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
You can specify the file pathes relative to the location of the configuration file or as absolute pathes.
I recommend using relative pathes whenever possible, so your project is portable to another PC or the Workstation.
If you create your configuration as a dictionary within your python script, you must make sure the configuration entries are absolute pathes. 
You can see how relative pathes are converted to absolute ones e.g. in cesarp.common.config_loader.abs_path(path, basepath)

"./theFile.csv" is a relative path, explicit stating that the file is in the current folder.
"theFile.csv" is relative and results in the same as above.
"../theFile.csv" is also relative, the "../" navigates one level up in the folder structure.
"C:/Data/MyProject/theFile.csv" is an absolute path.


I further recommend to use the "/" also on Windows, if you use "\\" you need to escape it, thus use "\\\\".

CSVY-Format
~~~~~~~~~~~~
That's a csv with a YAML header. Like that, you can add some metadata right in the data file. Below an example, but
you can put any KEY: value pairs or only set the ones you want. See also http://csvy.org

.. code-block::

  ---
  # this is a csvy file with a header block formatted as YAML followed by csv data, see csvy.org
  DESCRIPTION: Definition of energy carriers for my great project
  SOURCE: where you got that great data from
  REFERENCES: a link to a online source, file server, or reference to a paper
  DATE-CREATED: 2020-06-15
  AUTHOR: Leonie Fierz
  CHANGE-LOG:
  - 2020-06-17, Leonie Fierz, changing energy carrier for fid2 to heatpump
  ---
  ORIG_FID, ECarrierDHW, ECarrierHeating
  1, SOLAR_THERMAL, OIL
  2, HEATPUMP, HEATPUMP


Site Vertices
-------------

.. code-block::

    SITE_VERTICES_FILE:
        PATH: "./SiteVertices.csv" # you can specify a *.shp file here, but be aware that you need to have geopandas installed when reading from shape file
        SEPARATOR: ","
        LABELS: # only effective for csv files
            gis_fid:  "TARGET_FID"
            height:   "HEIGHT"
            x:        "POINT_X"
            y:        "POINT_Y"

The SITE_VERTICES_FILE describes the footprint vertices of all buildings on a site. This includes the buildings that should be
simulated as main buildings and probably buildings that are only used as neighbouring shading objects.
Footprint vertices are expected in counter-clockwise order. First Vertex entry is used for calculating distance to
neighbouring buildings.

Cesar-P supports following input formats:

**Shapefile:** If you set the path to a file with \*.shp ending, Cesar-P uses the Shapefile-Parser.
You need to install geopandas before you can use this feature. Instructions on windows see in src/cesar/geometry/shp_input_parser.py
For \*.shp file the SEPARATOR and LABELS section is not used.

**CSV Files:** the format is the same as it was in Cesar Matlab.
For each building the last entry must be a duplication of the first vertex.

Example CSV site vertices file content, defining two buildings

.. code-block::

    TARGET_FID, POINT_X, POINT_Y, HEIGHT
    1,          0,        0,      12.5
    1,          0,        10,     12.5
    1,          25,       10,     12.5
    1,          25,       0,      12.5
    1,          0,        0,      12.5
    2,          35,       0,      12.5
    2,          35,       10,     12.5
    2,          60,       10,     12.5
    2,          60,       0,      12.5
    2,          35,       0,      12.5

File is parsed from cesar.manager.BldgModelFactory

Weather
-------
Weather files have to be in the epw, EnergyPlus Weather Files format. See EnergyPlus reference for more details, e.g.
for version 8.5 see https://bigladdersoftware.com/epx/docs/8-5/auxiliary-programs/energyplus-weather-file-epw-data-dictionary.html#energyplus-weather-file-epw-data-dictionary

Building information
--------------------
In Cesar-Matlab you could specify one file with information per building. In Cesar-P, you can reuse this file after you did map the building type to the new Cesar-P constants (see below description for BLDG_TYPE_PER_BLDG_FILE).
To give more flexibility if you have different input sources and not all information in the same file, with Cesar-P
you need to specify the input file per aspect. If you have everything in the same file its a bit clumsy because you
need to specify and in case of a change replace all the pathes.

Per Building Information is parsed in cesar.manager.BldgModelFactory.

This is the portion of the cesar.manager package configuration covering the parts that were previously in the one building information file.

.. code-block::

    BLDG_FID_FILE:
        PATH: "ProjectSpecificFile.csv"
        SEPARATOR: ","
        LABELS:
            gis_fid: "ORIG_FID"
    BLDG_AGE_FILE:
        PATH: "ProjectSpecificFile.csv"
        SEPARATOR: ","
        LABELS:
            gis_fid: "ORIG_FID"
            year_of_construction: "BuildingAge"
    BLDG_INSTALLATION_FILE:
        PATH: "ProjectSpecificFile.csv"
        SEPARATOR: ","
        LABELS:
            gis_fid: "ORIG_FID"
            dhw_energy_carrier: "ECarrierDHW"
            heating_energy_carrier: "ECarrierHeating"
    GLAZING_RATIO_PER_BLDG_FILE:
      ACTIVE: False
      PATH: "ProjectSpecificFile.csv"
      SEPARATOR: ","
      LABELS:
        gis_fid: "ORIG_FID"
        glazing_ratio: "GlazingRatio"
    BLDG_TYPE_PER_BLDG_FILE:
        PATH: "ProjectSpecificFile.csv"
        SEPARATOR: ","
        LABELS:
            gis_fid: "ORIG_FID"
            sia_bldg_type: "SIA2024BuildingType"
    SITE_PER_CH_COMMUNITY:
        ACTIVE: False # if False, SINGLE_SITE must be active
        BLDG_TO_COMMUNITY_FILE:
            PATH: "TBD_BLDG_TO_COMMUNITY_FILE.csv"
            SEPARATOR: ","
            LABELS:
                bldg_fid: "bldg_fid"
                community: "community"

**BLDG_FID_FILE**: defines the fid's which should be simulated. using a separate file, you can define here only a portion of your site to be simulated.

**BLDG_AGE_FILE**: defines the year of construction or building age for each building. year should be a 4-digit, e.g. 2020

**BLDG_INSTALLATION_FILE**: defines the energy carrier for heating and dhw. DHW_OTHER and HEATING_OTHER are a mix of different energy carriers with shares according to the energy strategy used. The value can be one of

- name or value of Enum cesar.energy_strategy.EnergySource.EnergySource

  - NO / No Energy Carrier
  - HEATING_OIL / Heating Oil
  - COAL / Coal
  - GAS / Gas
  - ELECTRICITY / Electricity
  - WOOD / Wood
  - HEAT_PUMP / Heat Pump
  - SOLAR_THERMAL / Solar Thermal
  - DISTRICT_HEATING / District Heating
  - HEATING_OTHER / Other (Heating)
  - DWH_OTHER / Other (DHW)

- legacy matlab numeric id: mapping between numeric ID and EnergySource is defined in cesar.energy_strategy.EnergySource.EnergySource.
  It is

  - 1:  EnergySource.NO
  - 2:  EnergySource.HEATING_OIL
  - 3:  EnergySource.COAL
  - 4:  EnergySource.GAS
  - 5:  EnergySource.ELECTRICITY
  - 6:  EnergySource.WOOD
  - 7:  EnergySource.HEAT_PUMP
  - 8:  EnergySource.SOLAR_THERMAL
  - 9:  EnergySource.DISTRICT_HEATING
  - 10: EnergySource.HEATING_OTHER
  - 11: EnergySource.DWH_OTHER

  I do not recommend to use the legacy numeric id if you prepare new input files.

**GLAZING_RATIO_PER_BLDG_FILE**: defines the glazing ratio percentage for the building. if the entry "ACTIVE" is set to False, glazing ratio from constructional archetype is used.
The percentage can be defined as a value between 0...1 or 0...100, but it must be consistent within the file.

**BLDG_TYPE_PER_BLDG_FILE**: The building type is used to generate the correct SIA 2024 parameters and profiles.
The value can be one of the constants (key stated in CAPITAL, e.g. MFH) defined in src/cesar/SIA2024/ressources/building_types.yml. This is

- MFH (Wohnen MFH / Residential Multi Family Home)
- SFH (Wohnen EFH / Residential Single Family Home)
- OFFICE (Verwaltung / Office)
- SCHOOL (Schule (ohne Turnhalle) / School (without gym))
- SHOP (Verkauf / Shop)
- RESTAURANT (Restaurant (mit Küche) / Restaurant (with kitchen))
- HOSPITAL ( Spital / Hospital)

ATTENTION: If you are using an input file used previously with **Cesar Matlab**, you need to map the numeric Building Type to
the constants. In the example files I got the mapping was **1 -> SFH, 2-> MFH**. Onyl those two building types were used, and I didn't see a mapping in the code from the numeric id to the building type,
thus you have to match it yourself if you have entries other then 1 and 2.

Example file (including column LastRetrofit and GroundFloorArea is not refered to in the config and are currently not necessary to be specified).
According configuration is above.

.. code-block::

  ORIG_FID, SIA2024BuildingType, BuildingAge, LastRetrofit, GroundFloorArea, ECarrierHeating, ECarrierDHW, GlazingRatio
  1,        MFH,                 1900,        1900,         250,             2,               2,           13
  2,        MFH,                 1930,        1930,         250,             2,               2,           16


**SITE_PER_CH_COMMUNITY**: 
If you have different locations for your buildings, you can activate that option and map
the the file where the community is defined for each of the buildings. Currently the community only influences the
weather file chosen. Make sure the set the path to where you have your weather files stored if you do not want to use
in the config for the package cesar.weather.swiss_communities. There you can also lookup the list of community id's.