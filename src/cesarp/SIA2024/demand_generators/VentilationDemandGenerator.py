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
import numpy
from typing import Callable, List, Protocol

from cesarp.common.profiles import profile_generation
from cesarp.SIA2024.demand_generators.ValuePerKeyCache import ValuePerKeyCache
from cesarp.SIA2024.demand_generators.BuildingTypeProtocol import BuildingTypeProtocol


class BaseDataForVentilationProtocol(Protocol):
    def get_ventilation_rate_night_per_person(self, room_type) -> pint.Quantity:
        ...

    def get_ventilation_rate_day_per_person(self, room_type) -> pint.Quantity:
        ...

    def get_ventilation_rate_per_area(self, room_type) -> pint.Quantity:
        ...


class VentilationDemandGenerator:
    """
    Generates ventilation rate and ventilation yearly profile. Ventilation means outdoor air flow.
    The object is specific for one building. If variability is activated, the profile is cached, so repeated calls to
    get_occupancy_for_bldg() returns always the same profile.

    Variability can be controlled at following points:

    - ventilation rate value (see __init__)
    - area_per_person (see __init__) - has an effect for all room types which have a ventilation rate per person defined
    - nighttime pattern (see get_yearly_ventilation_profile) - used if ventilation is reduced during night
    - occupancy profile (see get_yearly_ventilation_profile) - used as a base for ventilation profile
    """

    def __init__(
        self,
        bldg_type: BuildingTypeProtocol,
        base_data: BaseDataForVentilationProtocol,
        vent_rate_variability: bool,
        get_area_pp_for_room_method: Callable[[str], float],
    ):
        """
        :param bldg_type: Building type to generate the profile for, e.g. object of SIA2024BuildingType
        :param base_data: nominal values data store, e.g. SIA2024DataAccessor
        :param vent_rate_variability: True if variability should be added to the ventilation rate
        :param get_area_pp_for_room_method: method to get the area_per_person for a room
        """
        self.get_area_pp_for_room_method = get_area_pp_for_room_method
        self.base_data = base_data
        self.bldg_type = bldg_type

        self.vent_rate_variable_per_room_lookup_table = None
        if vent_rate_variability:
            self.__vent_rate_variable_per_room_lookup_table = ValuePerKeyCache(self.bldg_type.get_room_types(), self.__get_vent_rate_variable_for_room)
            self.__get_vent_rate_for_room_method = self.__vent_rate_variable_per_room_lookup_table.lookup_value
        else:
            self.__get_vent_rate_for_room_method = self.__calc_vent_rate_nom_for_room

    def get_ventilation_rate_for_bldg(self):
        """
        :return: return ventilation rate value for the building aggregated over the different room types
        """
        return self.bldg_type.synthesize_value_by_room_area(self.__get_vent_rate_for_room_method)

    def get_yearly_ventilation_profile_for_bldg(
        self,
        get_year_profile_occupancy_hourly_per_room_method: Callable[[str], List[float]],
        nighttime_pattern_year_profile_bldg_hourly: List[bool],
    ):
        """
        :param get_year_profile_occupancy_hourly_per_room_method: reference to method returning a year profile with hourly values [0...1]
        :param nighttime_pattern_year_profile_bldg_hourly: year profile with hourly entries, True during night, False during the day
        :return: year profile with hourly values for ventilation [0...1]
        """

        def wrap_get_vent_prof_for_room(room_type):
            return self.__get_yearly_ventilation_profile_for_room(room_type, get_year_profile_occupancy_hourly_per_room_method, nighttime_pattern_year_profile_bldg_hourly)

        return self.bldg_type.synthesize_profiles_yearly_by_room_area_for_bldg(wrap_get_vent_prof_for_room, additional_factor_per_room_method=self.__get_vent_rate_for_room_method)

    def __get_yearly_ventilation_profile_for_room(
        self,
        room_type,
        get_year_profile_occupancy_hourly_per_room_method: Callable[[str], List[float]],
        nighttime_pattern_year_profile_bldg_hourly: List[bool],
    ):

        # ventilation profile follows occupancy
        vent_profile_yearly = get_year_profile_occupancy_hourly_per_room_method(room_type)

        # correct ventilation during night if nighttime ventilation value is given
        vent_rate_pp_night_room = self.base_data.get_ventilation_rate_night_per_person(room_type)
        vent_rate_pp_day_room = self.base_data.get_ventilation_rate_day_per_person(room_type)
        if vent_rate_pp_night_room != 0 and vent_rate_pp_day_room != 0:
            nighttime_correction_prof_yearly = (vent_profile_yearly * vent_rate_pp_night_room / vent_rate_pp_day_room).m
            vent_profile_yearly = profile_generation.combine_day_and_nighttime_profiles(
                vent_profile_yearly, nighttime_correction_prof_yearly, nighttime_pattern_year_profile_bldg_hourly
            )
        return vent_profile_yearly

    def __calc_vent_rate_nom_for_room(self, room_type):
        """
        Uses nominal ventilation rate, but in case ventilation rate per person is available the results depends
        on the area_per_person_method injected during construction, which could return a area_per_person value with variability.
        """
        vent_nom_pp = self.base_data.get_ventilation_rate_day_per_person(room_type)
        if vent_nom_pp != 0:
            vent_rate = vent_nom_pp / self.get_area_pp_for_room_method(room_type)
        else:
            vent_rate = self.base_data.get_ventilation_rate_per_area(room_type)
        return vent_rate

    def __get_vent_rate_variable_for_room(self, room_type):

        vent_nom_pp = self.base_data.get_ventilation_rate_day_per_person(room_type)
        if vent_nom_pp != 0:
            vent_pp_variable = numpy.random.normal(vent_nom_pp.m, vent_nom_pp.m / 10, 1)[0] * vent_nom_pp.u
            vent_rate = vent_pp_variable / self.get_area_pp_for_room_method(room_type)
        else:
            vent_nom_per_area = self.base_data.get_ventilation_rate_per_area(room_type)
            vent_rate = numpy.random.normal(vent_nom_per_area.m, vent_nom_per_area.m / 10, 1)[0] * vent_nom_per_area.u

        return vent_rate
