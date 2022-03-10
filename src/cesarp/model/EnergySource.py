# coding=utf-8
#
# Copyright (c) 2022, Empa, Leonie Fierz, Aaron Bojarski, Ricardo Parreira da Silva, Sven Eggimann.
#
# This file is part of CESAR-P - Combined Energy Simulation And Retrofit written in Python
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# Contact: https://www.empa.ch/web/s313
#
from enum import Enum


class EnergySource(Enum):
    NO = "No Energy Carrier"
    HEATING_OIL = "Heating Oil"
    COAL = "Coal"
    GAS = "Gas"
    ELECTRICITY = "Electricity"
    WOOD = "Wood"
    HEAT_PUMP = "Heat Pump"
    SOLAR_THERMAL = "Solar Thermal"
    DISTRICT_HEATING = "District Heating"
    HEATING_OTHER = "Other (Heating)"
    DHW_OTHER = "Other (DHW)"

    @classmethod
    def _missing_(cls, value):
        # decode energy source number as they were used in the Cesar Matlab
        # (as a source for the mapping the input file FuelCostFactors.xlsx was used)
        try:
            e_carrier_nr = int(value)
            if e_carrier_nr == 1:
                return EnergySource.NO
            if e_carrier_nr == 2:
                return EnergySource.HEATING_OIL
            if e_carrier_nr == 3:
                return EnergySource.COAL
            if e_carrier_nr == 4:
                return EnergySource.GAS
            if e_carrier_nr == 5:
                return EnergySource.ELECTRICITY
            if e_carrier_nr == 6:
                return EnergySource.WOOD
            if e_carrier_nr == 7:
                return EnergySource.HEAT_PUMP
            if e_carrier_nr == 8:
                return EnergySource.SOLAR_THERMAL
            if e_carrier_nr == 9:
                return EnergySource.DISTRICT_HEATING
            if e_carrier_nr == 10:
                return EnergySource.HEATING_OTHER
            if e_carrier_nr == 11:
                return EnergySource.DWH_OTHER
        except ValueError:  # raised if value is not an integer
            pass

        value = value.strip()  # remove withespaces
        try:
            # if reaching this bit, we can try to decode it assuming it's the Enum name, such as "WOOD"
            val_as_name = value.upper()
            return EnergySource[val_as_name]
        except KeyError:  # raised if not found
            pass

        # if reaching here try to decode assuming it's the Enum value, such as "Solar Thermal"
        val_as_value = value.lower()
        for entry in EnergySource:
            if entry.value.lower() == val_as_value:
                return entry

        raise ValueError(f"{value} is not a valid EnergySource")
