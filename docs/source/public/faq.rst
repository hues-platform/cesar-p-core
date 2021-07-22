========
FAQ
========

CESAR-P crashes after update
----------------------------

- CESAR-P should be backward compatible from version 1.0.0 onwards. Nevertheless, if CESAR-P fails unexpectedly after a update, try following:

  - If you try to relaod, check if things work when you run everything from scratch
  - If the error messages include *DatasetMetadata*: delete generated SIA parameters - it might be that you switched between code versions or updated the code and
    format of SIA Parameter file did change


CESAR-P crashes/hangs without an error
---------------------------------------

- Have a look in the worker logs in TIMESTAMP-cesar-p-logs 
- Use **cesarp.debug_methods.run_single_bldg(...)** to run only a single building without using multiprocessing pool

Can I use a \*.shp file as input for the Site Vertices?
-------------------------------------------------------

Set configuration variable **MANAGER- SITE_VERTICES_FILE** to point to your \*.shp file. Make sure other files going
along with the shape file are in the same folder. Then, CESAR-P will select the right input parser (namely cesar
.geometry.shp_input_parser.py) to load the footprint vertices for your site.

Implementation reference: cesar.geometry.shp_input_parser

NOTE: you need to (manually) install geopandas. Follow the instructions in the above mentioned Python file to do so
on Windows (make sure you install it to the virtual environment created by poetry if you installed CESAR-P with
poetry). On Linux, you can use "poetry install -e geo" to install geopandas

How can I run CESAR-P using x Cores / running in parallel?
----------------------------------------------------------
The SimulationManager class supports running the preparation of the IDF's as well as running the EnergyPlus
simulation on many cores. For the preparation it does not make sense to parallelize more than ~10buildings per core
as loading the site vertices into memory takes quite long (depending on the size of the buildings included).
To set the number of cores to be used:

.. code-block::

   MANAGER:
     NR_OF_PARALLEL_WORKERS: -1  # -1 means half of the available processors will be used


How do I best fix/debug tests?
-----------------------------------------------

After any change, make sure all the tests run through again:

- if you do not expect any test fails, commit your changes to the repository, otherwise execute first locally the tests which you think might fail. 
- if CI pipeline failed you should get a notice per mail
- if static tests failed, run flake8 and mypy locally and clean up the errors (use black to quickly clean up formatting errors). 
  if you can't fix a static error, you can add a "# type: ignore" comment to tell mypy to ignore that line or "# noqa: E731" to tell flake8 to ignore error 731 (or whatever it is in your case) on a certain line
- if a unit test failed, the easiest is to re-run this test locally. often it is handy to comment the line deleting test-outputs after the test-function finished to be able to compare side-by-side test result and expected results.
  look out for a line with "shutil.rmtree", most often placed in a tetfixture mehtod
- in your IDE, e.g. VisualCode, you can also debug the test which might be handy to figure out what is going wrong


.. _migrate_from_matlab:

What is the version scheme of CESAR-P?
-----------------------------------------------

:ref:`version_numbers`

