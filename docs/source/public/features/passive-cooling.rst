Passive cooling 
==================

Two aspects for modelling passive cooling are available have been modeled by Ricardo da Silva and integrated into CESAR-P together with Léonie Fierz.

Per default window shading is active but night ventilation is not used. To check see cesarp.operation operation_default_config.yml.

Passive cooling by window shading
------------------------------------

Note: currently there is one set of parameters for all building types, but in reality behavior of users in residentail buildings compared to commercial, office or shool buildings differ.

Window shading is commonly used to reduce solar heat gains and prevent buildings from overheating, 
by partially or fully covering glazed areas from incoming direct, diffuse, and ground reflected solar radiation. 
Its effectiveness depends on several factors, such as building orientation, geometry, windows optical properties and relative positioning, 
occupant behaviour and control strategy. The detailed optical and thermal modelling properties 
of the shading devices can be found in :py:class:`cesarp.Construction.ConstructionBasics.ConstructionBasics`. 
Occupants generally actuate shading devices in response to several factors, 
such as solar radiation, perceived glare, thermal discomfort, and responsiveness (time latency between occupant sensing and actuating). 
As detailed modelling of occupant behaviour (inherently stochastic, and multivariable) is not possible in this scope,
the variables used to determine the behaviour of the user are the incident solar radiation on each of the individual windows, 
which are therefore controlled independently, and the average indoor temperature. A rule-based control logic was implemented to emulate the user behaviour, 
with a differential controller that actuates the shading device based on global radiation on the plane of the window. A constant value of 90 W/m2 and a minimum indoor
temperature of 24°C were used as the thresholds for the actuation criteria, assuming that the building inner lightning ensures proper visual comfort. 
More advanced automated shading systems were not considered as they are out of scope and currently not commonly available in Swiss buildings. 
The type of shading device, characterization properties, and activating criteria are: 

- Type of shading: Venetian blinds (exterior)
- Transmissivity to radiation (solar spectrum):	Tau in range [0.20-0.31]
- Reflectance to radiation (solar spectrum):	Roh in range [0.50-0.70]
- Global solar irradiance on window plane >90 W/m2	-> window shading is activated
- if Tr > 24 °C	-> window shading is activated


Passive cooling by night ventilation
------------------------------------

Note: currently the model is designed for residential buildings. For other building types parameters would need to be evaluated.

Autor of this section: Ricardo Parreira da Silva

*Parameters in configuration (see cesarp.operation operation_default_config.yml for defaults):*

- flow_rate                      # night ventilation nominal air flow rate - in air-changes-per-hour (ACH)
- min_indoor_temperature         # minimum indoor temperature for the space to require cooling (C) - above this value the window can be opened
- maximum_in_out_deltaT          # maximum indoor-outdoor temperature differential in (C) to ensure that the occupant only opens the window when the ambient can provide cooling, i.e., when the outdoor temperature is lower than the inside temperature by a given number of degrees
- max_wind_speed                 # maximum wind speed threshold (m/s) - above this value the occupant closes the window
- start_hour                     # night ventilation starting hour (00:00 format)
- end_hour                       # night ventilation ending hour (00:00 format)

*Inputs:*

Maximum indoor air temperature set-point [°C]

- this value is used to contemplate the possibility of using air conditioning
- above this value of indoor temperature the window is closed so that the AC is not turned on with the window opened
- simulation with cooling air-conditioning
  if we want to simulate passive cooling, and activate the AC cooling if passive not enough,
  then this value should be put to the cooling set-point schedule (cooling_setpoint_schedule)
- simulation without cooling air-conditioning
  if we want to simulate only passive cooling without AC, then this value should be put to 99
  and window will always open when cooling is required (and available) from night ventilation.

*Outputs/Effect on model:*

- ventilation flow rate to provide cooling to the room

*Features:*

- Models an exterior air flow rate to the inside room during the night to provide cooling
  in the summer season, when interior and exterior conditions allow it.
- The actual flow rate  is defined as a nominal air changer per hour (ACH) based on values
  recommended in scientific literature for night ventilation (Frank, 2005)
- Window opening by occupants controlled by minimum temperature to require cooling, and indoor-outdoor
  differential, supported by the main drivers identified for actuation decision in Roetzl et al, 2010
  " (...) as key drivers for occupants using night ventilation, field studies
  identified indoor temperature, outdoor temperature, as well as window state before departure"
  Source: Roetzl et al. "A review of occupant control on natural ventilation"
- The occupant actuation modelling is based in a differential on-off controller; sufficient for long-term energy
  modelling purposes.
- The maximum indoor temperature - from which above that, active cooling can be turned on, is established by
  comfort conditions received from the cooling set point schedule (input)
- Cooling by night ventilation schedule is established to be active from start_hour to end_hour
- Possibility to close window above a maximum wind speed threshold is also addressed

  - to model occupant behavior of closing of window during high wind conditions

    - maximum wind speed value set to 40 m/s - EnergyPlus 8.5 default value

*Notes:*

- Observed small impact on heating energy demand (roughly below 5%)

  - which can be potentially justified by non-ideal behavior of typical on-off controllers close to
    dead-band during transition from cooling to heating requirement conditions, together with the delay
    caused by dynamic factors. (non-perfect controller)

- No observed impact on electricity demand. (expected)
- No observed impact on DHW consumption. (expected)

*Full details:*

- The full details of the model, with a extensive description will be fully documented in a publication to be
  released

*Possibilities/ideas for improvement:*

- Introduction of previous state-of-the-window as criteria for actuation (2nd order criteria)
- Introduction of multiplying factor for computing non-nominal renovation flow rate in function of available wind speed
- Introduction of electrical consumption of window actuator (expected small)

  - for the case of domotization of windows - in modern buildings

*References:*

Cowie,L., Carmeliet, J., Orehounig, K., "Predicted Impact of Climate Change on Cooling Requirements in Residential", ETH Zurich Semester project, 2017
Roetzl, et al. "A review of occupant control on natural ventilation" Renewable and Sustainable Energy Reviews, 2010
Frank et al., "Climate change impacts on building heating and cooling energy demand in Switzerland. Energy and Buildings", 2005


*Implementation*

- data model: cesarp.model.BuildingOperation.NightVent
- factory for data model creation: cesarp.operation.PassiveCoolingOperationFactory
- IDF writing: cesarp.eplus_adapter.idf_writer_night_vent.py - for copying the associated profile see CesarIDFWriter