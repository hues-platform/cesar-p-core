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
from typing import Callable, Iterable, Protocol, Dict, Optional
import pint
import logging

from cesarp.common.profiles import profile_generation, profile_variability
from cesarp.SIA2024.demand_generators.ValuePerKeyCache import ValuePerKeyCache
from cesarp.SIA2024.demand_generators.BuildingTypeProtocol import BuildingTypeProtocol
from cesarp.SIA2024 import COL_STD, COL_MIN, COL_MAX


class BaseDataForAppliancesProtocol(Protocol):
    def get_appliance_profile_min_value_allowed(self, room_type) -> pint.Quantity:
        ...

    def get_appliance_profile_fixed_weekend_value(self, room_type) -> pint.Quantity:
        ...

    def get_appliance_level_std(self, room_type) -> pint.Quantity:
        ...

    def get_appliance_day_profile_hourly(self, room_type) -> Iterable[float]:
        ...

    def get_nr_of_rest_days_per_week(self, room_type) -> pint.Quantity:
        ...

    def get_horizontal_breaks_appliances(self, room_type) -> Iterable[int]:
        ...

    def get_appliance_level_triple(self, room_type) -> Dict[str, pint.Quantity]:
        ...


class AppliancesDemandGenerator:
    """
    Generates appliance level base value and profile.
    The object is specific for one building. If variability is activated, the profile and appliance level is cached,
    so repeated calls to get_appliance_profile_for_bldg() and get_appliance_level_for_bldg()
    return always the same profile resp. value.

    Points of variability:

    - monthly variation (__init__): variation in people occupancy on a monthly basis
    - vertical variation for each hourly profile value (see activate_profile_variability())
    - horizontal variation, meaning a shuffling of values in a time block for each day of the profile (see activate_profile_variability())
    - variability for appliance level value (see activate_appliance_level_variability())
    """

    def __init__(
        self,
        bldg_type: BuildingTypeProtocol,
        base_data_accessor: BaseDataForAppliancesProtocol,
        get_year_profile_variation_monthly_for_room_method: Callable[[str], Iterable[float]],
        profile_start_date: str,
    ):
        """
        :param bldg_type: building type for which to create the profile, e.g. object of SIA2024BuildingType
        :param base_data_accessor: base data used to generate the profile, e.g. SIA2024DataAccessor object
        :param get_year_profile_variation_monthly_for_room_method: method reference to get year profile with variation value per month, method can return nominal or variable values.
        """
        self.bldg_type = bldg_type
        self.base_data = base_data_accessor
        self.profile_max_value = 1  # due to profile type
        self.get_year_profile_variation_monthly_for_room_method = get_year_profile_variation_monthly_for_room_method
        self.__app_level_var_per_room_cache: Optional[ValuePerKeyCache] = None
        self.__app_prof_var_per_room_cache: Optional[ValuePerKeyCache] = None
        self.__get_appliance_profile_for_room_method = self.__gen_app_prof_for_room_nominal
        self.__get_appliance_level_for_room_method = self.base_data.get_appliance_level_std
        self._profile_start_date = profile_start_date

    def activate_profile_variability(self, vertical_variability: float, do_horizontal_variability: bool):
        """
        Activate profile variability.
        To activate variability for the activity level value itself, see activate_appliance_level_variability.
        Timeblocks of day within which to shuffle profile values when horizontal variability is requested are looked up in the base_data data store.
        Profiles are generated per room_type contained in current building type and cached for later use.

        :param vertical_variability: sigma for randomization of each profile value; set to 0 to deactivate vertical variability
        :param do_horizontal_variability: pass True if you want horizontal variability/shuffling within timeblocks of a day
        :return: nothing
        """

        def wrap_get_profile_for_room(room_type):
            return self.__gen_app_prof_for_room_variable(room_type, vertical_variability, do_horizontal_variability)

        self.__app_prof_var_per_room_cache = ValuePerKeyCache(self.bldg_type.get_room_types(), wrap_get_profile_for_room)
        self.__get_appliance_profile_for_room_method = self.__app_prof_var_per_room_cache.lookup_value

    def activate_appliance_level_variability(self):
        """
        Activate variability for the appliance level value.
        For profile variability see activate_profile_variability()
        Appliance level per room type contained in current buidling type is calculated and cached for later use.
        :return: nothing
        """
        self.__app_level_var_per_room_cache = ValuePerKeyCache(self.bldg_type.get_room_types(), self.__gen_app_level_variable_for_room)
        self.__get_appliance_level_for_room_method = self.__app_level_var_per_room_cache.lookup_value

    def get_appliance_level_for_bldg(self):
        """
        Variability is controlled by activate_appliance_level_variability()
        :return: appliance level for the building, W/m2
        """
        return self.bldg_type.synthesize_value_by_room_area(self.__get_appliance_level_for_room_method)

    def get_appliance_profile_for_bldg(self):
        """
        Variability of profile is controlled by activate_profile_variability()
        :return: year profile with hourly values [0...1]
        """

        return self.bldg_type.synthesize_profiles_yearly_by_room_area_for_bldg(
            self.__get_appliance_profile_for_room_method,
            additional_factor_per_room_method=self.__get_appliance_level_for_room_method,
        )

    def __gen_app_prof_for_room_nominal(self, room_type):
        """
        Attention! nominal means nominal appliance profile values, but underlying monthly variation values can be
        nominal or random dependent on linked method during object construction
        """
        appliance_profile = profile_generation.expand_year_profile_monthly_to_hourly(
            self.get_year_profile_variation_monthly_for_room_method(room_type),
            self.base_data.get_appliance_day_profile_hourly(room_type),
        )

        appliance_profile = profile_generation.correct_weekends(
            appliance_profile,
            self.base_data.get_nr_of_rest_days_per_week(room_type).m,
            weekend_value=self.base_data.get_appliance_profile_fixed_weekend_value(room_type),
            start_date=self._profile_start_date,
        )
        min_value = self.base_data.get_appliance_profile_min_value_allowed(room_type)
        appliance_profile = [max(min(self.profile_max_value, prof_val), min_value) for prof_val in appliance_profile]

        return appliance_profile

    def __gen_app_prof_for_room_variable(self, room_type, vertical_variability: float, do_horizontal_variability: bool):

        appliance_profile = profile_generation.expand_year_profile_monthly_to_hourly(
            self.get_year_profile_variation_monthly_for_room_method(room_type),
            self.base_data.get_appliance_day_profile_hourly(room_type),
        )

        if vertical_variability > 0:
            min_value = self.base_data.get_appliance_profile_min_value_allowed(room_type)
            appliance_profile = profile_variability.randomize_vertical(appliance_profile, vertical_variability, min_value, self.profile_max_value)

        # target for "weekend correction" are non residential buildings, thus fixed value without randomization is ok.
        appliance_profile = profile_generation.correct_weekends(
            appliance_profile,
            self.base_data.get_nr_of_rest_days_per_week(room_type).m,
            weekend_value=self.base_data.get_appliance_profile_fixed_weekend_value(room_type),
            start_date=self._profile_start_date,
        )

        if do_horizontal_variability:
            horizontal_breaks = self.base_data.get_horizontal_breaks_appliances(room_type)
            appliance_profile = profile_variability.horizontal_variability(appliance_profile, horizontal_breaks)

        return appliance_profile

    def __gen_app_level_variable_for_room(self, room_type):
        app_level_triple = self.base_data.get_appliance_level_triple(room_type)
        unit = app_level_triple[COL_STD].u
        (min, max, peak) = profile_variability.triang_dist_limits(app_level_triple[COL_MIN].m, app_level_triple[COL_MAX].m, app_level_triple[COL_STD].m, perc=0.05)
        logging.getLogger(__name__).debug(f"appliance level limits used for triang dist: {min}, {max}, {peak}, with originals from SIA beeing \n{app_level_triple}")
        return profile_variability.get_random_value_triangular_dist(min, max, peak) * unit
