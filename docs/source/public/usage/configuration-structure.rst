Configuration structure
===================================

For each package with configuration parameters, there is a default configuration file in the source package. When
calling CESAR-P you pass a custom configuration file, also refered to as main config. In that file you can specify
all parameters you want to set specific for your project. Those parameters you pass with your project configuration 
overwrite the default from the packages. So you only need to specify the parameters you want a special value for, 
but not all of them. It is actually better not to add parameters with default values to your project config. One 
reason is that you will clutter up your config and the second point is that if something should change in the
definition of the package and the parameters get outdated, you have to adapt your config.

General structure of the YML configuration is:

.. code-block::

  PACKAGE_NAME:
    PARAMETER_Y: "x"
    SUBPACKAGE_NAME:
      PARAMETER_X: "y"

So each parameter is under the package using that parameter. The top most package "cesarp" is not reflected in the
configuration, so the top level package names in the configuration are MANAGER, CONSTRUCTION, GEOMETRY etc.
Be careful with the indention, use two spaces for each level. Make also sure when adding parameters to your main
config for a package different than MANAGER to state the package unindented and not under MANAGER.  
There are some sub-packages having their own config file, e.g. cesarp.construction.fixed. 

There is a **simple validation** of the configuration done when the *SimulationManager* reads the config file, 
checking that the parameters defined exist, but not validating their values. This validation is done against 
the default config files, so new parameters added to the configuration are validated automatically. 

CESAR-P reads this YML structure into a dictionary (multi-level). To the top-level classes in ceserp.manager, namely
SimulationManager and ProjectManager and in cesarp.retrofit. When using other classes directly, you can optionally pass your custom configuration as a dictionary
(usually as parameter custom_config of __init__), when passing a dict, it has to be a hierarchicyl dict having the same 
levels as in the YAML config.


Numeric values / units
-----------------------
In general, numerical values are stated together with their unit in the configuration.
You can change the unit if you need, but it must be convertible to the unit used in the default configuration for that value.
The unit is parsed with *pint* unit library, so please follow that style (https://pint.readthedocs.io/en/stable/tutorial.html#string-parsing).
There are some CESAR-P specific units defined in cesarp.common package, myPintDefs.txt.

Pathes
-------

You can specify pathes either relative to the configuration file location 
(the values in the default config files relative to their location, for values overwritten in the main config relative to this config location) or as absolute pathes. 
One exception are the realative pathes for the MANAGER, some are relative to the base folder specified in that configuration block.
Any relative pathes are converted to absolute ones when reading in the configuration files.
If you specify configuration parameters having pathes directly in a dictionary always use absolute pathes.
