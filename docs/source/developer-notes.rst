Notes for developers
=====================

Configuration
-------------

- When you add a **config entry for a path**, if the key contains file, path, dir... or the value has a "registered"
  file extension (for full list of what is interpreted as a path see cesar.common.config_loader
  _PATH_IDENTIFIERS_IN_VALUE and _PATH_IDENTIFIERS_IN_KEY), the path is realtive, it is interpreted as relative to the location of the config file and converted to absolute path.

Implementation notes
--------------------
- **IDF defaults** when transfering the Matlab Cesar implementation to Python, in the IDF Writing process some values are
  not set explicit anymore as they were in the Matlab version. The reason is that those values were set to the
  default values, and not really by a decision, it was probably more because the IDF was created by copying together
  IDF Chunks for the general portions. Manly this includes algorithm definitions in Zones, SurfaceConvection
  algorithm etc.
