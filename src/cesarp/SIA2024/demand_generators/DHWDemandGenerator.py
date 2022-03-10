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
from typing import Callable, List, Dict, Protocol
import pint
import logging

from cesarp.common.profiles import profile_generation, profile_variability
from cesarp.SIA2024.demand_generators.ValuePerKeyCache import ValuePerKeyCache
from cesarp.SIA2024.demand_generators.BuildingTypeProtocol import BuildingTypeProtocol
from cesarp.SIA2024 import COL_STD, COL_MIN, COL_MAX


class BaseDataForDHWProtocol(Protocol):
    def get_dhw_demand_std(self, room_type) -> pint.Quantity:
        ...

    def get_dhw_demand_triple(self, room_type) -> Dict[str, pint.Quantity]:
        ...

    def get_dhw_night_value(self) -> pint.Quantity:
        ...

    def is_dhw_off_during_night(self, room_type) -> bool:
        ...


class DHWDemandGenerator:
    """
    Generate electricity demand for domestic hotwater and fraction profile for dhw usage.

    The object is specific for one building. If variability is activated, the profile is cached, so repeated calls to
    get_occupancy_for_bldg() returns always the same profile.
    Variabilty points:

    - dhw power demand value (see __init__)
    - occcupancy profile (see get_dhw_profile_for_bldg())
    - nighttime pattern (see get_dhw_profile_for_bldg())
    """

    def __init__(
        self,
        bldg_type: BuildingTypeProtocol,
        base_data_accessor: BaseDataForDHWProtocol,
        dhw_variability: bool,
        get_year_profile_occupancy_hourly_per_room_method: Callable[[str], List[float]],
        nighttime_pattern_yearly_profile: List[bool],
    ):
        """
        :param bldg_type: type of building for which to generate profile, e.g. object of SIA2024BuildingType
        :param base_data_accessor: base data, e.g. SIA2024DataAccessor
        :param dhw_variability: True if variability should be added to dhw power/m2 value
        :param get_year_profile_occupancy_hourly_per_room_method: reference to method returning occupancy year profile defining hourly fraction [0...1] of full occupancy
        :param nighttime_pattern_yearly_profile: nighttime profile, to determine hours in which dhw should be turned off in case room is specified as such in excel input sheet
        """
        self.base_data = base_data_accessor
        self.bldg_type = bldg_type
        self._get_year_profile_occupancy_hourly_per_room_method = get_year_profile_occupancy_hourly_per_room_method
        self._nighttime_pattern_yearly_profile = nighttime_pattern_yearly_profile

        self.__dhw_var_per_room_cache = None
        if dhw_variability:
            self.__dhw_var_per_room_cache = ValuePerKeyCache(self.bldg_type.get_room_types(), self.__get_dhw_demand_variable_for_room)
            self.__get_dhw_power_per_area_for_room_method = self.__dhw_var_per_room_cache.lookup_value
        else:
            self.__get_dhw_power_per_area_for_room_method = self.base_data.get_dhw_demand_std

    def get_dhw_profile_for_bldg(self) -> List[float]:
        """
        Occupancy profile is used as a base. Depending on the building resp. room types contained, the profile is modified depending on nighttime pattern.

        :param get_year_profile_occupancy_hourly_per_room_method: reference to method returning occupancy year profile defining hourly fraction [0...1] of full occupancy
        :param nighttime_pattern_yearly_profile: year profile with hourly value, True if it is nighttime, falso otherwise
        :return: year profile defining hourly fraction of full load dhw demand [0...1]
        """

        return self.bldg_type.synthesize_profiles_yearly_by_room_area_for_bldg(
            self.__get_dhw_profile_for_room,
            additional_factor_per_room_method=self.__get_dhw_power_per_area_for_room_method,
        )

    def get_dhw_power_per_area_for_bldg(self) -> float:
        """
        :return: electricity demand for dhw in W/m2 on full load aggregated for the building
        """
        return self.bldg_type.synthesize_value_by_room_area(self.__get_dhw_power_per_area_for_room_method)

    def __get_dhw_profile_for_room(self, room_type):

        dhw_profile_yearly = self._get_year_profile_occupancy_hourly_per_room_method(room_type)
        if self.base_data.is_dhw_off_during_night(room_type):
            dhw_profile_yearly = profile_generation.define_fix_nighttime_value(dhw_profile_yearly, self.base_data.get_dhw_night_value().m, self._nighttime_pattern_yearly_profile)
        return dhw_profile_yearly

    def __get_dhw_demand_variable_for_room(self, room_type):
        dhw_demand_triple = self.base_data.get_dhw_demand_triple(room_type)
        unit = dhw_demand_triple[COL_MIN].u
        (min_lim, max_lim, peak) = profile_variability.triang_dist_limits(dhw_demand_triple[COL_MIN].m, dhw_demand_triple[COL_MAX].m, dhw_demand_triple[COL_STD].m, perc=0.05)
        logging.getLogger(__name__).debug(f"dhw power per are limits used for triang dist: {min_lim}, {max_lim}, {peak}, with originals from SIA beeing \n{dhw_demand_triple}")
        dhw_dem_val = profile_variability.get_random_value_triangular_dist(min_lim, max_lim, peak)
        dhw_dem_val = max(0, dhw_dem_val)  # make sure we do not get negative dhw demand values
        return dhw_dem_val * unit
