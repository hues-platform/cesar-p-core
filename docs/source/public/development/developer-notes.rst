Notes for developers
=====================

Configuration
-------------

- When you add a **config entry for a path**, if the key contains file, path, dir... or the value has a "registered"
  file extension (for full list of what is interpreted as a path see cesar.common.config_loader
  _PATH_IDENTIFIERS_IN_VALUE and _PATH_IDENTIFIERS_IN_KEY), the path is realtive, it is interpreted as relative to the location of the config file and converted to absolute path.


How do I add support for a new EnergyPlus Version?
---------------------------------------------------

You need to create a special IDD for CESAR-P for your E+ Version and you have to allow the new E+ Version in the functions in eplus_adapter. If there are changes in the IDF for the new version, 
you need to do a version handling and handle the difference when writing the IDF depending on the used E+ version. Here a step-by-step guide:

1. copy the IDD form the new IDD from C:/EnergyPlusVX-X-X/Energy+.IDD to src/cesarp/eplus_adapter/ressources and rename accroding to the naming schema of the other modified IDDs
2. compare a modified IDD under src/cesarp/eplus_adapter/ressources with the original from e.g. C:/EnergyPlusV9-5-0/Energy+.IDD
3. take over those additions (extending vertices from 120 to 250 (addition at two places in the IDD) and allow 100 Fenestration Surface elements
   there is also a script generating those additional lines in case the format changed https://github.com/hues-platform/cesar-p-usage-examples/blob/master/development_scripts/extend_idd.py
   Note: if you need to just quickly add the E+ version for a test and you do not have buildings with taht many vertices, you can also add the IDD without modifications
4. add the new IDD in src/cesarp/default_config.yml
5. add new E+ version respectively IDD in src\cesarp\eplus_adapter\eplus_sim_runner.py::get_idd_path
6. try running a simulation with the new version, include all options (set window shading, night ventilation active in the config)
7. if it does not run through, and eppy library is complaining about missing/wrong fileds, check the E+ documentation to see if there are changes in the definitions. if so, adapt the IDF writing 
   code, introduce version handling as it is done e.g. in cesarp.eplus_adapter.idf_writer_window_shading.add_shading_on_windows. add in the tests/test_integration a test to check the IDF writing process
   for both, the new and old version
8. if you want to change the main version for CESAR-P:

   a. set the new version in src/cesarp/default_config.yml (and change your environment variables ENERGYPLUS_VER and ENERGYPLUS_EXE)
   b. update tests/test_integration and tests/test_eplus_adapter - there are some tests for backward compatibility with EnergyPlus 8.5, 
      but all other tests can be upgraded to the latest version 
      (unless you had to introduce some version handling in the IDF writing in point 7., then make sure you cover both those variants)
      results normally change a little (<1% or so) between versions, but please check them thoroughly (with a Diff Tool e.g. from TortoiseGit or the integrated one in VS Code)
      Best is to search for "CUSTOM_IDD\_" to find all locations. Update the expected results files as well.
      As with eppy only only one IDD can be set per instance, on the CI system it will fail if you mix differetn IDD in the same set of tests... why it works
      locally but not on the CI to run two tests in sequence with dirrereent IDD set I do not fully understand.
   c. do download the EnergyPlus Linux \*.sh for the new version (go the E+ github to download it), replace the \*.sh in the project root. 
      Update ENERGYPLUS_DOWNLOAD_FILENAME and ENERGYPLUS_VER in gitlab-ci.yml.

9. if you do not set the added E+ version as default, make sure you run the example cases and check that results do not change significantly

