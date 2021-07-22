Building Geometry
=======================

Input and configuration overview
--------------------------------

.. figure:: ./diagrams/Inputs_Config_Geometry.png

Implementation Notes
--------------------

- All geometry elements of a building are assumed to be rectangles
- Roof is modeled as a flat roof
- Defined glazing ratio is applied to each wall. If a wall is too small or resulting window is too small (see
  configuration in cesarp.geometry), the window is not modelled. The so missing window area is not compensated for,
  thus the overall glazing ratio might be lower than you defined. You will be warned when resulting glazing ratio 
  differs more than 2% (for details see config entries for "GLAZING_RATIO_CHECK" in cesarp.geometry package)
- Footprint vertices are assumed to form a closed polygon and must be in counter-clockwise order

Windows
-------
- **Window sill** absorptance property was set to 0.5 but sill depth was 0 with Matlab CESAR, so Window sill is now left
  to default (all 0)

- **Window divider** were set in Matlab CESAR, but as we only have a quite rough glazing ratio estimation and not
  all buildings have windows with dividers, modeling dividers is not reasonable. Those properties will not be set with
  CESAR-P.

- **Window width / Frame width** in Matlab CESAR version, minimal window width was defined with 0.04m and frame width
  also with 0.04m. To make sure that the frame does not overlap itself, minimal window width was set to 0.08m in
  CESAR-P.

- **View Factor to ground** for windows there was a fixed view factor to ground of 0.5 set in CESAR Matlab. As
  autocalculate makes no difference in simulation results for the nine example buildings, CESAR-P sets view factor to
  ground to autocalculate.