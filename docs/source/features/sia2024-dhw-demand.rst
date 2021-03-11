.. _sia2024_dhw_demand:

===================================
SIA2024 - Domestic Hotwater Demand 
===================================

There are two options implemented to calculate domestic hotwater demand.
In the configuration you can choose to calculate the DHW demand based on l/d/person values from SIA2024/2016 (refered to as Variant B): 

.. code-block:: console

    SIA2024:
        DHW_BASED_ON_LITER_PER_DAY:
            ACTIVE: True
            NOMINAL_TEMPERATURE: 60°C
            COLD_WATER_TEMPERATURE: 10°C

if you set DHW_BASED_ON_LITER_PER_DAY - ACTIVE to False, then the specific heat demand values  stated in the excel sheet are used, as in the implementation in CESAR Matlab (refered to as Variant A).

For defining the dhw usage profile there is only one variant.

EnergyPlus needs a specific power per m2 value for domestic hotwater demand alongside with a hourly profile. 

.. _sia2024_dhw_profile:

Usage profile
--------------

- Base is the occupancy profile per room type
- If "dhw is off during night" is set to 1 in the excel input sheet for the room, then all night-hours are set to zero. The decision which hours should be night is taken from nighttime profile generated with cesarp.SIA2024.demand_generators.NighttimePatternGenerator
- Variability: no variability is introduced for the DHW profile itself, but the used occupancy and nighttime profile can have some variability
- The per room profiles are aggregated for the building, depending on the area share and the share in DHW demand value of that room type


VARIANT A: DHW demand value based on SIA2024/2006 specific power "Spezifischer Wärmebedarf für Warmwasser" (as implemented in CESAR Matlab)
-------------------------------------------------------------------------------------------------------------------------------------------

The specific heating power value "Spezifischer Wärmebedarf für Warmwasser" in W/m2 as stated in the SIA2024/2006 can be used directly.
That value is available in SIA2024/2006, but not in SIA2024/2016 anymore.
In case variability is on for the DHW demand value, additional custom definitions for min/max are used to generate a random value based on a triangular distribution.
Those min/max values were copied from the CESAR Matlab implementation.

Resulting yearly demand - too low according to SIA2024/2016
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Consulting the "old" Norm SIA2024/2006, the description mentions that the value "Spezifischer Wärmebedarf für Warmwasser" in W/m2 applies to "Nutzungsstunden pro Tag".
As the profile for DHW uses the occupancy profile but sets demand to zero during nighttime, there is a mismatch between the hours with demand in the DHW profile and those "Nutzungsstunden pro Tag" from the norm.
This leads to a too small yearly DHW demand, as following calculation shows:

For a single family home (SFH):

- "Spez. Leistungsbedarf für Wassererwärmung" = 2.5 W/m2 for SHF in the SIA_data_for_MATLAB.xlsx 

- The hourly profile is set off during nighttime

- yearly_dhw_demand = sum(val*2.5W/m2 for val in dhw_profile) = 4.38 kWh/m2

SIA2024/2016 states for the yearly demand "Jährlicher Wärmebedarf für Warmwasser" for a SFH 13.5 kWh/m2 - this is ~3 times bigger than what we get; for details about the value see SIA Norm PDF, chapter 1.3.8.7.

As the specific power demand value is meant to go with a profile also active during night, I calculated the yearly demand when DHW is not set off during nighttime:  

- yearly_dhw_demand = sum(val*2.5W/m2 for val in occupancy_profile) = 10.2 kWh/m2

As the value when using the occupancy profile only roughly matches yearly demand from SIA2024/2016, this implementation is not changed and left as it is.
Anyway, a new approach based on the l/d/person values (Variant B) is implemented, details see below.
  
VARIANT B: DHW demand value based on SIA2024/2016 hot water demand "Warmwasserbedarf pro Person" in liter/day/person 
---------------------------------------------------------------------------------------------------------------------

This implementation takes the hot water demand value per person as a base, then calculates the energy demand per day per person and converts to a energy per area value by using the area per person. Then, using the domestic hot water profile, the specific power per m2 value is calculated.

Implementation according to SIA2024/2016 calculation of "Jährlicher Wärmebedarf für Warmwasser" (see SIA Norm PDF, chapter 1.3.8.7):

- Daily energy demand for domestic hot water: **Qw,day = [Vw * pw * cp (thetaw-thetacw)] / Ap,NGF** 

  - Vw: domestic hotwater demand in l/d/person,  stated in SIA2024/2016, read from spreadsheet

  - pw: relative density of water, 1 kg/l

  - cp: specific heat capacity of water, 0.00116 kWh/(kg*°C)

  - thetaw: requested hotwater temperature, read from configuration, according to SIA2024/2016 60°C

  - thetacw: mean temperature of cold water inlet, read from configuration, according to SIA2024/2016 10°C

  - Ap,NGF: room area per person, stated in SIA2024/2016, read from spreadsheet

- **specific_dhw_power_demand = Qw,day * 365 / sum_h(dhwProfile(h)/monthlyVariation(month(h)))**

  - **dhwProfile** is the usage profile as described above, see :ref:`sia2024_dhw_profile`

  - Note that Qw,day value calculated is for full occupancy, so the occupancy profile has to be devided by the **monthlyVariation**, which states partial occupancy depending on the month. 

- To get then to the value for the whole building, the values calculated for each room type are aggregated according to their area share

- As you see below, with the new approach taken the yearly energy demand is not changed depending on the profile. This allows for variation in the profile without affecting overall energy demand for DHW as it is the case with the old method.


**Comparision of yearly energy demand based on the different calculation approches**

Single family home: 

- Variant B (based on "Warmwasserbedarf pro Person" in l/d/p, DHW following occupancy or off during night): **13.5 kWh/m2**

- Variant A (based on "Spez. Leistungsbedarf für Wassererwärmung", DHW off during night): **4.3 kWh/m2**

- "Jährlicher Wärmebedarf für Warmwasser" yearly demand stated in SIA2024/2016 datasheet for roomtype EFH, which makes up 100% of the single family home building type (see SIA2024/2016): **13.5 kWh/m2**

Multi family home:

- Variant B (based on "Warmwasserbedarf pro Person" in l/d/p, DHW following occupancy or off during night): **17.8 kWh/m2**

- Variant A (based on "Spez. Leistungsbedarf für Wassererwärmung", DHW off during night): **5.6 kW/m2**

- "Jährlicher Wärmebedarf für Warmwasser" yearly demand stated in SIA2024/2016 datasheet for roomtype MFH, which makes up 90% of the multi family home building type (see SIA2024/2016): 19.8 kWh/m2
  => so the expected value per square meter for MFH is 90% of the MFH room type demand, as the other 10% is staircase without any DHW usage, which is **17.82 kWh/m2**

**Checking EnergyPlus results**

- The output of EnergyPlus simulation for resulting annual DHW energy demand for MFH is 17.78 kWh/m2

Variability for hotwater demand value
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
To add variability in the resulting yearly hotwater energy demand, the daily hotwater demand value in liter per person is variated.

As SIA2024/2016 does not state any range for that value, other approaches had to be taken to estimate the distribution.

**Distribution of dhw demand for residential room types**

Measurement data was used to identify the distribution for residential room types (SFH and MFH). 
The measurement data originates from BFE P&D Projekt "2000-Watt Gesellschaft leben" (SI/501502-01) over Hochschule Luzern. 
The measurement includes data for 2 years for ~35 households, which are part of a experimental neighbourhood.

There are approx 10'000 daily measurements. The data I used was preprocessed. The values per household were aggregated to weekly demands to 
filter out housholds with a sudden change of DHW usage during the year (due to change of renter).
Those weekly demands were mapped again to get mean values per day per person for each household and year.
The mean over the two values for the year 2019 and 2020 are used for the further analysis.
Lower demand during holidays is not compensated, thus the factor holiday is included in the mean values. 
I'm not sure wether SIA2024/2016 takes holidays for residential room types into account in the monthly variation ("Jahresprofil") or not. 
If yes, using values where holiday absences are corrected would be better (from the BFE 2000W project such data should be available).
Given that we can anyway only roughly match the distribution due to the low number of samples I assume the influence of holiday absences on the resulting distribution used would be small, so I didn't puruse that point.

The figure shows the measurements as a histogram, with a gamma distribution fitted with Matlab.

.. figure:: ./diagrams/SIA2024/DHW/dhw_demand_BFEProj_histogram_mean_per_houshold.png

For the CESAR Matlab implementation for DHW demand variation a triangular distribution was used. So this was done here as well. We could have used the gamma distribution as well, but with the triangular distribution the parameters a,b,c are easier traceable and comprehensible.
Following diagram shows the gamma distribution fitted along with a triangular distribution, where min/max was set to the minimum resp. second but last biggest mean value from all households (23 l/d/person resp 118 l/d/person). The maximum value is such an outlyer that it would flatten the distribution too much towards big values.
The peak value used for the triangular distribution corresponds to the nominal demand value from SIA2024/2016, thus for MFH 35 l/d/person and for EFH 40 l/d/person.
In CESAR-P implementation when using a triangular distribution, the limits for the distribution function are shiftet, so that the target min/max are withing 0.05 resp 0.95 Percentile (see function cesarp.common.profile_variability::triang_dist_limits). 
This results in a final triangular distribution with a=10, b=35, c=144.

.. figure:: ./diagrams/SIA2024/DHW/dhw_demand_BFEProj_data_distribution_fits.png


Resulting distribution of specific hotwater demand:

.. figure:: ./diagrams/SIA2024/DHW/CESARP_Variable_specific_DHW_Demand_VariantB.png

As a comparision, the distribution of specific hotwater demand as generated with Variant A:

.. figure:: ./diagrams/SIA2024/DHW/CESARP_Variable_specific_DHW_Demand_VariantA.png

Note: see Scripts/dhw_dist.py for code to draw the dhw specific power demand values as used for the diagrams above.


**Distribution for non-residential room types**

For non-residential room types a simple approach was used.
As a distribution again the triangular distribution was used. The range is set as +/-20% of the nominal value stated in SIA2024/2016 is used (see also additional columns in SIA Spread Sheet).
The +/-20% limits are set as 0.05 resp 0.95 Percentiles for the triangular distribution method.