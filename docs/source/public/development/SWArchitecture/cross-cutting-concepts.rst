Cross cutting concepts
========================

.. _sub-packages:

*Sub-Packages*
---------------
Modularize each aspect or function into its own package.
Each CESAR-P sub-package has its own configuration and input data packed with it. Thus, a sub-package can be used on its own. Sub-Packages should be loosly coupled. Several smaller sub-packages are prefered over bigger ones with low cohesion allowing the user to have a better configurability and extensability.
Input data goes in to folder **ressources**
Default configuration file name is defined in __init__.py
Dependencies to other packages should be kept minimal.

.. _configuration:

*Configuration*
---------------
There is a configuration file per package holding all parameters for the package. All API classes should provide the possibility to pass a custom configuration (as dictonary). Parameters also set in this custom configuration overwrite those of the package default configuration.
The reasons behind this logic:

- In the custom configuration the user has only those parameters he wants to change.
- There are a lot of parameters used and some are probably never going to change. But still it is easy to lookup which assumptions were made and which constants are used in a package, as you can refer to the configuration file.
- If a new parameter is introduced in a package, it won't break the custom configuration of the users
- With the custom configuration containing parameters for all packages, there is a single point for user configuration

Implementation:

- the configuration file uses yml
- the structure is hierarchical:

  .. code-block::

    package_name:
      sub_package_name:
        parameter_x: "y"

- in the package default configuration and in the custom configuration the whole package structure needs to be stated (below main "cesarp" package)
- there are common functions to load package config, merge custom config and so on in cesar.common.config_loader

.. _dependency-injection:

*Dependency Injection*
-----------------------

Dependencies to function or classes of other sub-packages shall be injected rather than hard linked.

.. _programming-paradigm:

*Programming paradigm*
-----------------------
Everything not relying on a state or common ressources such as the configuration shall be programmed in a functional approach. 
The advantages of this approach are:

- more transparency what data a function needs and which parameters changing the behaviour are available
- easier reusability, as also single functions can be reused without the need of reconstruction a whole object tree
- as the functions do not access any shared data not passed as arguments, it's less prone to run into multi-threading problems such as dead locks

Nevertheless, during development there arised the need of some statefulness, among others:

- to be able to load data only once (without delegating this to the main sequence)
- to be able to have a shared configuration and passing custom configuration from top down to almost each method called
- provide an easy and consitent API for the packages
- using well known object oriented patterns, e.g. Factories and Strategy Pattern to make Cesar-P extensible

.. _type-checking-and-contracts:

*Type checking and contracts*
------------------------------
- Obscure pre-conditions should be checked explizit with assert statements, providing a helpful message to the developer if the condition is not met.
- Type checking: Python is a dynamicly typed language and it's advantage should be kept. There is the pythonic way of checking types with MyPy and type annotations, which shall be used. To enforce checks where the code relies on "duck typing", Protocols should be used to enforce conformity. Advantages:

  - Ease of use for developers extending the code as the API is clearer
  - Compared to writing documentation including the types of function and method parameters is that type hints will not get outdated as easy as comments
  - Checking types with MyPy gives way more easy to read error messages than when there is Runtime TypeError occuring

Disadvantages:

- Types have to be defined
- Some runtime overhead if type have to be imported (but type checking is not performed during runtime, so the overhead should not be too big)

Further reading:

- [RealPython Type Checking Article] (https://realpython.com/python-type-checking/)
- [PEP 484 Type Hints] (https://www.python.org/dev/peps/pep-0484/)
- [PEP 544 Protocols] (https://www.python.org/dev/peps/pep-0544/)


Generally Type Hints should be added, at least to the interface methods of a class.

In the geometry package I used python-contracts to check the pre-conditions and enforce type safety. It worked but was not handy enought to use, 
so I stopped using it in the other packages. For the geometry package it is still useful to know that the dataframes passed have the right 
content, as so far this was not possible with type hints, but there might be some updates on that now. Anyway, if there is a bigger
refactoring in the geometry package you could re-think whether to keep those contracts in or not.


.. _units:

*Units*
-------
The python library pint is used for Unit handling. Generally all values read should be accopanied with their unit.
With pint, each value is encapsulated in a Quantity object, having a unit (attribut u) and a magnitude (attribute m).
Following reasons made the use of a unit system worse it:

- automatic conversion, e.g. from m3/h/m2 to m3/s/m2
- checking if value is in the expected unit
- the advantage of the programatic approach over stating the units as comments is that it cannot be outdated and units are easily printable and also available during debugging
- error if a mathematical operation is performed between incompatible units, e.g. adding m2 to m3
- units are automatically updated when mathematical operations are performed, e.g. (5 m3)/(2 m2) = 2.5m

pint has a so called unit registry which handels all the unit stuff. It is important to always use the same instance of this registry, 
thus in the main script such an instance is created and passed to whatever object instances need access to the unit registry.
Passing the unit registry rather than having a "Singelton" or global instance is more flexible in case cesar or part of it should be made ready for multithreading.
For use with the python multiprocessing library, I had to use the "application unit registry" approach, creating a unit registry when the worker is started and 
registring it with set_application_registry and access with get_application_registry in the per-worker methods in :py:mod:`cesarp.manager.processing_steps`.

There are some CESAR-P specific units defined in cesarp.common package, myPintDefs.txt.

