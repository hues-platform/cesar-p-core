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
import pint
import cesarp.common
from cesarp.common.DatasetMetadata import DatasetMetadata


class SIA2024Parameters:
    """
    Data object holding one parameter set derived from SIA2024.
    The xxx_schedule members can be of any different Schedule types, e.g. cesarp.common.ScheduleFixedValue, cesarp.common.ScheduleFile, cesarp.common.ScheduleValues.
    Objects of type SIA2024Parameters are not intended to be used outside of the SIA2024 package.
    """

    def __init__(
        self,
        name,
        occupancy_fraction_schedule,
        activity_schedule,
        floor_area_per_person,
        electric_appliances_fraction_schedule,
        electric_appliances_power_demand,
        lighting_fraction_schedule,
        lighting_power_demand,
        dhw_fraction_schedule,
        dhw_power_demand,
        heating_setpoint_schedule,
        cooling_setpoint_schedule,
        ventilation_fraction_schedule,
        ventilation_outdoor_air_flow,
        infiltration_rate: pint.Quantity,
        infiltration_fraction_schedule: cesarp.common.ScheduleFile,
        data_descr: DatasetMetadata,
    ):
        self.name = name
        self.occupancy_fraction_schedule = occupancy_fraction_schedule
        self.activity_schedule = activity_schedule
        self.floor_area_per_person = floor_area_per_person
        self.electric_appliances_fraction_schedule = electric_appliances_fraction_schedule
        self.electric_appliances_power_demand = electric_appliances_power_demand
        self.lighting_fraction_schedule = lighting_fraction_schedule
        self.lighting_power_demand = lighting_power_demand
        self.dhw_fraction_schedule = dhw_fraction_schedule
        self.dhw_power_demand = dhw_power_demand
        self.heating_setpoint_schedule = heating_setpoint_schedule
        self.cooling_setpoint_schedule = cooling_setpoint_schedule
        self.ventilation_fraction_schedule = ventilation_fraction_schedule
        self.ventilation_outdoor_air_flow = ventilation_outdoor_air_flow
        self.infiltration_rate = infiltration_rate
        self.infiltration_fraction_schedule = infiltration_fraction_schedule
        self.data_descr = data_descr
        # Version 1: parameter was introduced with CESAR-P version 1.2.0-alpha.0
        # Version 2: before releasing version 1.2.0; added name parameter
        self.CLASS_VERSION = 2

    @classmethod
    def emptyObj(cls):
        return cls(None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None)
