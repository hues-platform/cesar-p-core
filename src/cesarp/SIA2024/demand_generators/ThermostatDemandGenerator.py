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
import numpy
from pint import Quantity
from typing import Callable, List, Tuple, Protocol

from cesarp.common.profiles import profile_generation
from cesarp.common.profiles import HOURS_PER_YEAR
from cesarp.SIA2024.demand_generators.ValuePerKeyCache import ValuePerKeyCache
from cesarp.SIA2024.demand_generators.BuildingTypeProtocol import BuildingTypeProtocol


class BaseDataForThermostatDemandProtocol(Protocol):
    def get_unoccupied_setback_heating(self, room_type) -> Quantity:
        ...

    def get_night_setback_heating(self, room_type) -> Quantity:
        ...

    def get_unoccupied_setback_cooling(self, room_type) -> Quantity:
        ...

    def get_night_setback_cooling(self, room_type) -> Quantity:
        ...

    def get_heating_setpoint(self, room_type) -> Quantity:
        ...


class ThermostatDemandGenerator:
    """
    Generates thermostat setpoints and profile for cooling and heating.

    Points of variability:

    - heating/cooling setpoint (one setpoint value per room for whole year)
    - profile is based on occupancy profile and nighttime pattern, which both can have some variability.

    No additional variability is added to the thermostat profile itself.
    """

    def __init__(self, bldg_type: BuildingTypeProtocol, base_data: BaseDataForThermostatDemandProtocol, setpoint_variability):
        """
        :param bldg_type: building type object for which to generate profile, e.g. object of SIA2024BuildingType
        :param base_data: base data, e.g. SIA2024DataAccessor
        :param setpoint_variability:
        """
        self.base_data = base_data
        self.bldg_type = bldg_type

        if setpoint_variability is not None:

            def wrap_get_setpoints(room_type):
                return self.__generate_setpoint_heating_cooling_variable(room_type, setpoint_variability)

            self.__thermostat_setpoint_var_cache = ValuePerKeyCache(self.bldg_type.get_room_types(), wrap_get_setpoints)
            self.__get_thermostat_setpoints_method = self.__thermostat_setpoint_var_cache.lookup_value
        else:
            self.__get_thermostat_setpoints_method = self.__lookup_setpoint_heating_cooling_nominal

    def get_thermostat_profiles_for_bldg(
        self,
        get_year_profile_occupancy_hourly_per_room_method: Callable[[str], List[float]],
        nighttime_pattern_yearly_profile: List[bool],
    ) -> Tuple[List[float], List[float]]:
        """
        If setback for night and unoccupied hours

        :param get_year_profile_occupancy_hourly_per_room_method: reference to method returning occupancy year profile defining hourly fraction [0...1] of full occupancy
        :param nighttime_pattern_yearly_profile: year profile with hourly value, True if it is nighttime, False otherwise
        :return: tuple with two year profiles each with hourly values, first defining setpoint for heating,
                 second defining setpoint for cooling [°C]
        """

        # Setback temperatures during unoccupied hours and night are defined per room, so the the heating setpoint
        # is not synthesized among rooms before creating the profile
        setpoints = dict()
        for room_type in self.bldg_type.get_room_types():
            (setpoint_heating, setpoint_cooling) = self.__get_thermostat_setpoints_method(room_type)
            setpoints[room_type] = {"sp_heating": setpoint_heating, "sp_cooling": setpoint_cooling}

        def wrap_heating_prof_for_room(room_type):
            occupancy_profile = get_year_profile_occupancy_hourly_per_room_method(room_type)
            return self.__get_thermostat_profile(
                setpoints[room_type]["sp_heating"],
                occupancy_profile,
                self.base_data.get_unoccupied_setback_heating(room_type),
                nighttime_pattern_yearly_profile,
                self.base_data.get_night_setback_heating(room_type),
            )

        synth_heating_prof = self.bldg_type.synthesize_profiles_yearly_by_room_area_for_bldg(wrap_heating_prof_for_room)
        synth_heating_prof = [x * setpoints[room_type]["sp_heating"].u for x in synth_heating_prof]

        def wrap_cooling_prof_for_room(room_type):
            occupancy_profile = get_year_profile_occupancy_hourly_per_room_method(room_type)
            return self.__get_thermostat_profile(
                setpoints[room_type]["sp_cooling"],
                occupancy_profile,
                self.base_data.get_unoccupied_setback_cooling(room_type),
                nighttime_pattern_yearly_profile,
                self.base_data.get_night_setback_cooling(room_type),
            )

        synth_cooling_prof = self.bldg_type.synthesize_profiles_yearly_by_room_area_for_bldg(wrap_cooling_prof_for_room)
        synth_cooling_prof = [x * setpoints[room_type]["sp_cooling"].u for x in synth_cooling_prof]

        return (synth_heating_prof, synth_cooling_prof)

    def __get_thermostat_profile(
        self,
        thermostat_setpoint: Quantity,
        occupancy_profile: List[float],
        setback_unoccupied: Quantity,
        nighttime_pattern_yearly_profile: List[bool],
        setback_night: Quantity,
    ):
        """
        Create a thermostat profile, for heating or cooling. In case of cooling, specify negative setback temperatures.
        If unoccupied and nihgttime setback are both set, these are applied consequtively, meaning if room is unoccupied
        at a certain hour and it is nighttime, both setbacks are subtracted from the nominal value.

        :param thermostat_setpoint: temperature setpoint in degree C
        :param occupancy_profile: year profile with hourly occupancy values [0..1]
        :param setback_unoccupied: temperature reduction during unoccupied hours; 0 or None for no setback
        :param nighttime_pattern_yearly_profile: year profile with hourly boolean values, True if it is night
        :param setback_night: temperature reduction during nighttime; 0 or None for no setback
        :return: year profile with hourly thermostat setpoint values [°C]
        """

        if occupancy_profile and setback_unoccupied:
            year_profile_setpoint_hourly = [(thermostat_setpoint.m - setback_unoccupied.m) if occ_val == 0 else thermostat_setpoint.m for occ_val in occupancy_profile]
        else:
            year_profile_setpoint_hourly = [thermostat_setpoint.m] * HOURS_PER_YEAR

        if setback_night and nighttime_pattern_yearly_profile:
            profile_setback_night = [x - setback_night.m for x in year_profile_setpoint_hourly]
            year_profile_setpoint_hourly = profile_generation.combine_day_and_nighttime_profiles(
                year_profile_setpoint_hourly, profile_setback_night, nighttime_pattern_yearly_profile
            )

        return year_profile_setpoint_hourly

    def __lookup_setpoint_heating_cooling_nominal(self, room_type):
        setpoint_heating_nominal = self.base_data.get_heating_setpoint(room_type)
        setpoint_cooling_nominal = self.base_data.get_cooling_setpoint(room_type)
        return (setpoint_heating_nominal, setpoint_cooling_nominal)

    def __generate_setpoint_heating_cooling_variable(self, room_type, variability):
        (heating_sp_nom, cooling_sp_nom) = self.__lookup_setpoint_heating_cooling_nominal(room_type)
        # generate random setpoint for heating and cooling and make sure cooling setpoint is above heating setpoint
        loops_cnt = 0
        while True:

            heating_setp_rand = round(numpy.random.normal(heating_sp_nom.m, variability.m, 1)[0], 1) * heating_sp_nom.u
            cooling_setp_rand = round(numpy.random.normal(cooling_sp_nom.m, variability.m, 1)[0], 1) * cooling_sp_nom.u
            if cooling_setp_rand > heating_setp_rand:
                break
            if loops_cnt > 100:
                raise Exception(
                    f"could not get variable heating and cooling setpoints so that cooling_setpoint > heating_setpoint with nominal heating setpoint at"
                    f"{heating_sp_nom}, cooling setpoint at {cooling_setp_rand} and variability of {variability} "
                )
            else:
                loops_cnt += 1

        return (heating_setp_rand, cooling_setp_rand)
