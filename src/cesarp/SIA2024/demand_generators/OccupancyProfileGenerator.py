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
from typing import Callable, Iterable, Protocol, Optional, Sequence, Dict
from enum import Enum

from cesarp.common.profiles import profile_generation
from cesarp.common.profiles import profile_variability
from cesarp.SIA2024.demand_generators.ValuePerKeyCache import ValuePerKeyCache
from cesarp.common.profiles import DAYS_PER_YEAR
from cesarp.SIA2024.demand_generators.BuildingTypeProtocol import BuildingTypeProtocol


class BaseDataForOccupancyProtocol(Protocol):
    def get_occ_day_profile_hourly_nominal(self, room_type) -> Iterable[float]:
        ...

    def get_horizontal_breaks_occupancy(self, room_type) -> Iterable[int]:
        ...

    def is_occupancy_nominal_during_night(self, room_type) -> bool:
        ...

    def get_lighting_density_std(self, room_type) -> pint.Quantity:
        ...

    def get_nr_of_rest_days_per_week(self, room_type) -> pint.Quantity:
        ...

    def get_occupancy_profile_restday_value(self, room_type) -> pint.Quantity:
        ...


class OccupancyProfileGenerator:
    """
    Generate occupancy profile for given building type.
    The object is specific for one building. If variability is activated, the profile is cached, so repeated calls to
    get_occupancy_for_bldg() returns always the same profile.

    Variability can be controlled at following points:

    - nighttime pattern (see initialization) - as this is controlled from outside, the "nominal" occupancy profile can have variability for nighttime pattern
    - profile variation monthly (see initialization) - as for nighttime pattern, profile variation  monthly can have variability even for "nominal" occupancy profile
    - vertical variation for each hourly profile value (see activate_profile_variability())
    - horizontal variation, meaning a shuffling of values in a time block for each day of the profile (see activate_profile_variability())
    """

    def __init__(
        self,
        bldg_type: BuildingTypeProtocol,
        base_data: BaseDataForOccupancyProtocol,
        nighttime_pattern_year_profile_bldg_hourly: Sequence[bool],
        get_year_profile_variation_monthly_for_room_method: Callable[[str], Iterable[float]],
        profile_start_date: str,
    ):
        """
        :param bldg_type: building type for which to generate the profile, e.g. object of SIA2024BuildingType
        :param base_data: base data for generating the profiles, e.g. based on SIA2024DataAccessor
        :param nighttime_pattern_year_profile_bldg_hourly: year profile with hourly entries set to True if it is
                                                            considered night/sleeptime, False otherwise. Method can return nominal pattern or wiht variability
        :param get_year_profile_variation_monthly_for_room_method: method reference to get year profile with variation value per month, method can return nominal or variable values.
        """
        self.bldg_type = bldg_type
        self.base_data = base_data
        self.nighttime_pattern_year_profile_bldg_hourly = nighttime_pattern_year_profile_bldg_hourly
        self.get_year_profile_variation_monthly_for_room_method = get_year_profile_variation_monthly_for_room_method
        self.get_occupancy_profile_for_room_method = self.__generate_occupancy_profile_nominal_for_room
        self.__occupancy_profiles_variable_cache: Optional[ValuePerKeyCache] = None
        self.__occupancy_profiles_nominal_cache: Dict[Enum, Iterable[float]] = dict()
        self._profile_start_date = profile_start_date

    def activate_profile_variability(self, vertical_variability: float, do_horizontal_variability: bool):
        """
        Activates vertical and horizontal variability (shuffling within time-blocks) on hourly profile values.
        The time-blocks for horizontal shuffling are defined per room-type in the base_data.

        :param vertical_variability: sigma for vertical variability, set to 0 to deactivate
        :param do_horizontal_variability: whether horizontal variability should be applied or not.
        :return: nothing, profiles per room are generated and cached
        """
        assert vertical_variability <= 1 and vertical_variability >= 0

        def wrap_gen_occ_prof_variable(room_type):
            return self.__generate_occupancy_profile_variable_for_room(room_type, vertical_variability, do_horizontal_variability)

        self.__occupancy_profiles_variable_cache = ValuePerKeyCache(self.bldg_type.get_room_types(), wrap_gen_occ_prof_variable)
        self.get_occupancy_profile_for_room_method = self.__occupancy_profiles_variable_cache.lookup_value

    def get_occupancy_profile_for_bldg(self, area_per_person_for_bldg: float, get_area_pp_for_room: Callable[[Enum], float]):
        """

        :param area_per_person_for_bldg: area_per_person for the building aggregated over room types, in m2/person
        :param get_area_pp_for_room: reference to method returning the area per person for a certain room type
        :return: year  profile with hourly values defining fraction of full occupancy value range [0...1]
        """
        if area_per_person_for_bldg == 0:
            return [0] * DAYS_PER_YEAR

        def get_occ_prof_proportional_for(room_type, room_area_fraction):
            occupancy_profile = self.get_occupancy_profile_for_room_method(room_type)
            area_per_person_for_room = get_area_pp_for_room(room_type)
            if area_per_person_for_room == 0:
                area_pp_factor = 0
            else:
                area_pp_factor = (1 / area_per_person_for_room.m) / (1 / area_per_person_for_bldg.m)
            return [room_area_fraction * profile_value * area_pp_factor for profile_value in occupancy_profile]

        occ_profs_proportions_per_room_type = [get_occ_prof_proportional_for(*room_item) for room_item in self.bldg_type.get_room_types_area_fraction().items()]
        return [sum(i) for i in zip(*occ_profs_proportions_per_room_type)]

    def __generate_occupancy_profile_nominal_for_room(self, room_type):
        if room_type in self.__occupancy_profiles_nominal_cache.keys():
            return self.__occupancy_profiles_nominal_cache[room_type]
        occupancy_profile_nominal = self.__generate_base_occupancy_profile(room_type)
        occupancy_profile_nominal = self.__handle_restdays(occupancy_profile_nominal, room_type)
        self.__occupancy_profiles_nominal_cache[room_type] = occupancy_profile_nominal
        return occupancy_profile_nominal

    def __generate_occupancy_profile_variable_for_room(self, room_type, vertical_variability: float, do_horizontal_variability: bool):
        """
        Generates occupancy profile with vertical and horizontal variability as configured by the parameters for the given room type of the building

        :param room_type: room type in building for which to generate the profile
        :param vertical_variability: vertical variability, for no vertical variability set to 0
        :param do_horizontal_variability: True if horizontal variability/shuffling should be applied, false otherwise
        :return: occupancy profile for one year, hourly values for given room
        """

        # might or might not have monthly variation according to passed method
        occupancy_prof_hourly = self.__generate_base_occupancy_profile(room_type)

        if vertical_variability > 0:
            # randomize  to avoid having the same profile for each day of a month
            occupancy_prof_hourly = profile_variability.randomize_vertical(occupancy_prof_hourly, vertical_variability)

        # target for "weekend correction" are non residential buildings - on a weekend a fixed value is used
        occupancy_prof_hourly = self.__handle_restdays(occupancy_prof_hourly, room_type)

        if do_horizontal_variability:
            horizontal_breaks = self.base_data.get_horizontal_breaks_occupancy(room_type)  # empty means no horizontal variability / shuffling
            occupancy_prof_hourly = profile_variability.horizontal_variability(occupancy_prof_hourly, horizontal_breaks)

        if self.base_data.is_occupancy_nominal_during_night(room_type):
            occupancy_prof_hourly = profile_generation.combine_day_and_nighttime_profiles(
                occupancy_prof_hourly, occupancy_prof_hourly, self.nighttime_pattern_year_profile_bldg_hourly
            )

        return occupancy_prof_hourly

    def __handle_restdays(self, occupancy_base_profile, room_type):
        # target for "weekend correction" are non residential buildings - on a weekend a fixed value is used
        nr_of_rest_days = self.base_data.get_nr_of_rest_days_per_week(room_type).m
        if nr_of_rest_days > 0:
            occupancy_base_profile = profile_generation.correct_weekends(
                occupancy_base_profile, nr_of_rest_days, self.base_data.get_occupancy_profile_restday_value(room_type).m, start_date=self._profile_start_date
            )
        return occupancy_base_profile

    def __generate_base_occupancy_profile(self, room_type):
        occupancy_profile = profile_generation.expand_year_profile_monthly_to_hourly(
            self.get_year_profile_variation_monthly_for_room_method(room_type),
            self.base_data.get_occ_day_profile_hourly_nominal(room_type),
        )
        return occupancy_profile
