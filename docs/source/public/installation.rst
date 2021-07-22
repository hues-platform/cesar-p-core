Installation
============

CESAR-P has currently no executable, so here is the installation guide to install the cesar-p-core library.
See :ref:`usage/set-up-simulation:Set up simulation` on instructions how to use the library.

Steps to install cesar-p-core library:

1. EnergyPlus
2. Python
3. Install cesar-p-core library python package

For instructions how to install if you want to adapt the code or develop new features, check the development section (:ref:`development/development-installation:Development Installation`).
Installing the package as editable with -e is not tested and supported.

1. EnergyPlus
--------------

CESAR-P simulates the building energy demand with EnergyPlus. Currently supported versions are 8.5, 8.7, 8.8, 8.9, 9.0.1, 9.2, 9.3, 9.5 (others can be added on demand).

Default EnergyPlus version is 9.5

Default installation location is C:/EnergyPlusV9-5-0/energyplus.exe. 

Download and install EnergyPlus from https://energyplus.net/downloads.

Set follwoing environment variables if you do not want to use the default EnergyPlus version or your installation location is different:

  ENERGYPLUS_VER

  ENERGYPLUS_EXE

e.g. for EPlus 9.5.0 that would be

  ENERGYPLUS_VER = 9.5.0

  ENERGYPLUS_EXE = C:/EnergyPlusV9-5-0/energyplus.exe


2. Python
----------
CESAR-P requires Python 3.8. Download and Install from https://www.python.org/downloads/.

If you already have a Python installation, do not tick 'Add Python X.Y to Path' during installation procedure.

Note: using Anaconda is not recommended, as it might be more complicated to handle with your IDE

3. Create Python virtual environment
--------------------------------------

- Open a shell, create & activate a virtual environment (based on the Python 3.8). E.g do:

  - Check if required python version is system default with 

    .. code-block::

      python -version

  - If NOT preceed python with the path to your python installation in the following commands

  - Create a new virtual environment (you can adapt the location of the venv as you wish - your home directory or any other location on the fileserver is not a sensible choice and might run out of space when installing all dependencies.

    .. code-block::

      python -m venv %USERPROFILE%/venv-cesar-p

  - Then activate your venv with

    .. code-block::

      %USERPROFILE%/venv-cesar-p/Scripts/activate


4. cesar-p-core library
----------------------------

Note: in case you use **Anaconda**, install shapely respectively geos with conda before installing CESAR-P 
(conda install -c conda-forge shapely). When running CESAR-P you might get an error that geos_c.dll was not found, 
which is hopefully prevented with installing shapley with conda. If you nevertheless get that error, 
try searching for that DLL in your conda environment where you did install shapley and copy-paste the 
geos.dll and geos_c.dll to the locatation mentioned in the error you get.

There are different options to install from

1. (Default) Install the latest released open-source version from PyPi package repository:

  .. code-block::
    
     pip install cesar-p

2.  Install a older released open-source version from PyPi package repository:

   .. code-block::
    
      pip install cesar-p==1.3.0

3. Install from GitHub Repository directly, e.g. if you need a special tag or the latest development version that was not released

    .. code-block::
    
       pip install git+https://github.com/hues-platform/cesar-p-core@1.3.0


5. optional: geopandas (for shp input file)
-----------------------------------------------------

If you will use shp input files for your site vertices, then you must install geopandas.
Unfortunately it can not be automated on Windows Systems. On linux, you can just install
geopandas and it will install the dependencies to GDAL and fiona for you.

1. Download GDAL and fiona wheels from https://www.lfd.uci.edu/~gohlke/pythonlibs
   Make sure to pick the x32 or x64 version according to your hardware and the matching python version (cpXX)

2. pip install GDAL and fiona (*pip install downloaded-package-name.whl*).

   .. code-block::
   
      pip install downloaded-gdal-package.whl
      pip install downloaded-fiona-package.whl


3. install now geopandas

   .. code-block::
   
      pip install geopandas

  if you want to check which version is the default, check this in the source repository in pyproject.toml.

4. If you get errors when running cesar-p using the shape file parser, 
    you probably need to manually copy geos_c.dll, geos.dll to MY_VIRTUAL_ENV/Library/bin from a geopandas installation with conda.
    This is the same step as you most probably already did for the shapely installation in case you work with Anaconda environments.

See also https://github.com/Toblerity/Fiona#windows for installation instructions for fiona package.


Update the cesar-p-core library
------------------------------------

- Just redo the pip install command you used for installing the package

