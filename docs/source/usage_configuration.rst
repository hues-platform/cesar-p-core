.. _usage_ref:

======================
Usage & Configuration
======================

For usage instructions please see README, section Usage. This includes also an overview of output files and folders.


YML configuration files
------------------------

For each package with configuration parameters, there is a default configuration file in the source package. When
calling CESAR-P you pass a custom configuration file, also refered to as main config. In that file you can specify
all parameters you want to set specific for your project (but you do not need to include all parameters). There are a
bunch of parameters under MANAGER you have to specify as they point to the project specific input files. See examples
and section below on input files for details

General structure of the YML configuration is:

.. code-block::

  PACKAGE_NAME:
    PARAMETER_Y: "x"
    SUBPACKAGE_NAME:
      PARAMETER_X: "y"

So each parameter is under the package using that parameter. The top most package "cesarp" is not reflected in the
configuration, so the top level package names in the configuration are MANAGER, CONSTRUCTION, GEOMETRY etc.
Be careful with the indention, use two spaces for each level. Make also sure when adding parameters to your main
config for a package different than MANAGER to state the package unindented and not under MANAGER. Make also sure you
have no typos, as CESAR-P does not check if your configuration parameters are valid. If misspelt, they are ignored
and the default value is used.

CESAR-P reads this YML structure into a dictionary (multi-level). To the top-level classes in ceserp.manager, namely
SimulationManager and ProjectManager and in cesarp.retrofit. When using other classes directly, you can optionally pass your custom configuration as a dictionary
(usually as parameter custom_config of __init__), then just use the same hierarchy as there is in the configuration
file.
