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
from dataclasses import dataclass
from typing import Any


class Occupancy:
    """
    Schedule parameters can be any schedule class from cesarp.common
    """

    def __init__(self, floor_area_per_person: pint.Quantity, occupancy_fraction_schedule, activity_schedule):
        self.floor_area_per_person = floor_area_per_person
        self.occupancy_fraction_schedule = occupancy_fraction_schedule
        self.activity_schedule = activity_schedule


class InstallationOperation:
    """
    Schedule parameters can be any schedule class from cesarp.common, as it represents a fraction schedule it's expected to have TypeLimits.FRACTION()
    """

    def __init__(self, fraction_schedule: Any, power_demand_per_area: pint.Quantity):
        self.fraction_schedule = fraction_schedule
        self.power_demand_per_area = power_demand_per_area


class HVACOperation:
    """
    Defines properties for the operation and damens of the Heating Ventilation and Air Conditioning of a building

    Schedule parameters can be any schedule class from cesarp.common
    """

    def __init__(
        self,
        heating_setpoint_schedule: Any,
        cooling_setpoint_schedule: Any,
        ventilation_fraction_schedule: Any,
        outdoor_air_flow_per_zone_floor_area: pint.Quantity,
    ):
        self.heating_setpoint_schedule = heating_setpoint_schedule
        self.cooling_setpoint_schedule = cooling_setpoint_schedule
        self.ventilation_fraction_schedule = ventilation_fraction_schedule
        self.outdoor_air_flow_per_zone_floor_area = outdoor_air_flow_per_zone_floor_area

    @classmethod
    def emptyObj(cls):
        return cls(None, None, None, None)


@dataclass
class NightVent:
    is_active: bool  # wether night ventilation is applied for this building or not - if false, other parameters of that class are potentially None
    flow_rate: pint.Quantity  # night ventilation nominal air flow rate - in air-changes-per-hour (ACH)
    min_indoor_temperature: pint.Quantity  # minimum indoor temperature for the space to require cooling (C) - above this value the window can be opened
    maximum_in_out_deltaT: pint.Quantity  # maximum indoor-outdoor temperature differential in (C) to ensure that the occupant only opens the window when the ambient can provide cooling, i.e., when the outdoor temperature is lower than the inside temperature by a given number of degrees
    max_wind_speed: pint.Quantity  # maximum wind speed threshold (m/s) - above this value the occupant closes the window - 40m/s is default in EnergyPlus Version 8.5
    start_hour: str  # night ventilation starting hour (00:00 format)
    end_hour: str  # night ventilation ending hour (00:00 format)
    maximum_indoor_temp_profile: Any  # any Schedule type, ScheduleFixedValue, ScheduleValues, ScheduleFile

    @classmethod
    def create_empty_inactive(cls):
        return cls(False, None, None, None, None, None, None, None)


@dataclass
class WindowShadingControl:
    is_active: bool  # wether window shading is applied or not at all
    is_exterior: bool  # if true, it is exterior shading device, if false interior
    radiation_min_setpoint: pint.Quantity
    shading_control_type: str  # one of the options for Shading_Control_Type in IDF

    @classmethod
    def create_empty_inactive(cls):
        return cls(False, None, None, None)


class BuildingOperation:
    """
    name should be unique within each building model if different BuildingOperation instances are assigned to different floors
    """

    def __init__(
        self,
        name: str,
        occupancy: Occupancy,
        electric_appliances: InstallationOperation,
        lighting: InstallationOperation,
        dhw: InstallationOperation,
        hvac_operation: HVACOperation,
        night_vent: NightVent,
        win_shading_ctrl: WindowShadingControl,
    ):
        self.name = name
        self.occupancy = occupancy
        self.electric_appliances = electric_appliances
        self.lighting = lighting
        self.dhw = dhw
        self.hvac = hvac_operation
        self.night_vent = night_vent
        self.win_shading_ctrl = win_shading_ctrl

    @classmethod
    def emptyObj(cls):
        return cls(None, None, None, None, None, None)
