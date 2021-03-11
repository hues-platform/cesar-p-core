Result Summary
==============

For units please see the headers in the result file.

All values in the result summary are integrated over the whole simulation period, thus one year.


Base results from EnergyPlus simulation output
----------------------------------------------

All the following values are stated as overall values for the whole building and as specific values per m2 floor area. To convert the EnergyPlus annual output values for the whole building to specific per floor area values to floor area is retrieved from EnergyPlus outputs \*.eio file.


DHW Annual
    Energy demand for domestic hot water. Corresponds to EnergyPlus output **DistrictHeating:Building**.
Heating Annual
    Energy demand for space heating. Corresponds to EnergyPlus output **DistrictHeating:HVAC**.
Cooling Annual
    Energy demand for space cooling. Corresponds to EnergyPlus output **DistrictCooling:Facility**.
Electricity Annual
    Electricity demand for appliances, lighting etc. Corresponds to EnergyPlus output **Electricity:Facility**.

By CESAR-P post-processed Cost & Emission results
--------------------------------------------------

**Input values used to calculate cost & emission results**

- Energy demands: DHW Annual, Heating annual and Electricity Annual - see base results explained above.
- Energy carrier: DHW Energy Carrier respectively Heating Energy Carrier specified in the input data (e.g. in your BuildingInformation.csv), for electricity the energy carrier is fixed to electricity
- Simulation year: the reference year used to calculate cost & emissions (configuration SITE - SIMULATION_YEAR, defaults to 2015)
- Lookup tables: different lookup tables for system efficiency, heating value, PEN, CO2 and cost factors. Factors depend on the selected Energy Strategy and simulation year (configuration ENERGY_STRATEGY - ENERGY_STRATEGY_SELECTION, defaults to "Business as usual"). For details package see cesarp.energy_strategy.

PEN Heating, PEN DHW, PEN Elec
    Non-renewable Primary Energy used for operation of heating, domestic hotwater and for consumed electricity; specific values per square meter floor area;
    
Total PEN
    Sum of PEN Heating, DHW and Elec;

CO2 Heating, CO2 DHW, CO2 Elec
    CO2 emissions for the operation of heating, domestic hot water and for consumed electricity; specific values per squre meter floor area;
    
Total CO2
    Sum of CO2 Heating, DHW and Elec

Heating - Fuel Costs, DHW - Fuels Costs:
    Costs for the fuel (energy carrier) for operation of heating respectively domestic hot water.

Electricity - Costs:
    Costs of consumed electricity (if the energy carrier for DHW or Heating is electricity, electricity usage is not included here but included under *Heating/DHW - Fuel Costs*)

Year used for lookup of cost factors:
    Simulation year which was used to lookup several factors, see the description of Inputs above

