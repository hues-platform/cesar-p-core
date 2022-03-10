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
import pint
from typing import Callable, List, Protocol
import logging

from cesarp.common.profiles import profile_generation, profile_variability
from cesarp.SIA2024.demand_generators.ValuePerKeyCache import ValuePerKeyCache
from cesarp.SIA2024.demand_generators.BuildingTypeProtocol import BuildingTypeProtocol
from cesarp.SIA2024 import COL_STD, COL_MIN, COL_MAX


class BaseDataForLightingProtocol(Protocol):
    def get_lighting_setpoint(self, room_type) -> pint.Quantity:
        ...

    def get_lighting_density_std(self, room_type) -> pint.Quantity:
        ...

    def get_light_off_fraction_profile_value(self) -> pint.Quantity:
        ...

    def is_lighting_following_occupancy(self, room_type) -> bool:
        ...

    def is_light_off_during_night(self, room_type) -> bool:
        ...


class LightingDemandGenerator:
    """
    Generate lighting density and setpoint values and lighting fraction profile.

    The object is specific for one building. If variability is activated, the profile is cached, so repeated calls to
    get_xxxx_for_bldg() returns always the same profile/value.

    Variabilty points:

    - lighting density value (see activate_lighting_density_variability)
    - lighting setpoint value (see activate_lighting_setpoint_variability)
    - profile due to variability in profiles used as a base:
      - monthly variation
      - occcupancy profile
      - nighttime pattern
    """

    def __init__(self, bldg_type: BuildingTypeProtocol, base_data: BaseDataForLightingProtocol):
        """
        :param bldg_type: building type for which to create the profile and demand values, e.g. object of SIA2024BuildingType
        :param base_data: base data to derive profile and demand values, e.g. SIA2024InteralConditionsData
        :param lighting_setpoint_variability: True if variability should be added to lighting setpoint
        :param lighting_density_variability: True if variability should be added to lighting density demand value
        """
        self.base_data = base_data
        self.bldg_type = bldg_type
        self.__get_lighting_setpoint_for_room_method = self.base_data.get_lighting_setpoint
        self.__get_lighting_density_for_room_method = self.base_data.get_lighting_density_std

    def activate_lighting_density_variability(self):
        self.light_dens_var_per_room_cache = ValuePerKeyCache(self.bldg_type.get_room_types(), self.__get_lighting_density_var_for_room)
        self.__get_lighting_density_for_room_method = self.light_dens_var_per_room_cache.lookup_value

    def activate_lighting_setpoint_variability(self, variability_prc: float):
        """
        :param variability_prc: defines the percentage of the standard value to use for randomization,
                                e.g. if nominal setpoint is 50lux and variability_prc is 0.1 resulting variabilit range is 45...55 lux
        """
        assert variability_prc <= 1, "variability_prc must be percentage in range 0...1"

        def wrap_get_lighting_setpoint_var(room_type):
            return self.__get_lighting_setpoint_var_for_room(room_type, variability_prc)

        self.light_sp_var_per_room_cache = ValuePerKeyCache(self.bldg_type.get_room_types(), wrap_get_lighting_setpoint_var)
        self.__get_lighting_setpoint_for_room_method = self.light_sp_var_per_room_cache.lookup_value

    def get_lighting_density_profile_for_bldg(
        self,
        get_year_profile_occupancy_hourly_per_room_method: Callable[[str], List[float]],
        nighttime_pattern_year_profile_bldg_hourly: List[bool],
        get_year_profile_monthly_variation_hourly_per_room_method: Callable[[str], List[float]],
    ):
        """
        :param get_year_profile_occupancy_hourly_per_room_method: reference to method returning occupancy year profile defining hourly fraction [0...1] of full occupancy
        :param nighttime_pattern_year_profile_bldg_hourly: year profile with hourly value, True if it is nighttime, falso otherwise
        :param get_year_profile_monthly_variation_hourly_per_room_method: monthly variation values of full occupancy, only used for room types where lighting does not follow occupancy
        :return: year profile defining hourly fraction of full lighting demand [0...1]
        """

        def wrap_get_lighting_density_prof_for_room(room_type):
            return self.__get_lighting_density_profile_for_room(
                room_type,
                get_year_profile_occupancy_hourly_per_room_method,
                nighttime_pattern_year_profile_bldg_hourly,
                get_year_profile_monthly_variation_hourly_per_room_method,
            )

        return self.bldg_type.synthesize_profiles_yearly_by_room_area_for_bldg(
            wrap_get_lighting_density_prof_for_room,
            additional_factor_per_room_method=self.__get_lighting_density_for_room_method,
        )

    def get_lighting_density_for_bldg(self):
        """
        :return: lighting density demand value synthesized over the different room types of the building type in W/m2
        """
        return self.bldg_type.synthesize_value_by_room_area(self.__get_lighting_density_for_room_method)

    def get_lighting_setpoint_for_bldg(self):
        """
        :return: lighting setpoint synthesized over the different room types of the building type in lux
        """
        return self.bldg_type.synthesize_value_by_room_area(self.__get_lighting_setpoint_for_room_method)

    def __get_lighting_density_profile_for_room(
        self,
        room_type,
        get_year_profile_occupancy_hourly_per_room_method: Callable[[str], List[float]],
        nighttime_pattern_year_profile_bldg_hourly: List[bool],
        get_year_profile_variation_monthly_per_room_method: Callable[[str], List[float]],
    ):
        light_off_value = self.base_data.get_light_off_fraction_profile_value().m

        if self.base_data.is_lighting_following_occupancy(room_type):
            lighting_yearly_profile = get_year_profile_occupancy_hourly_per_room_method(room_type)
        else:
            month_variation_profile_hourly = profile_generation.expand_year_profile_monthly_to_hourly(get_year_profile_variation_monthly_per_room_method(room_type), [1] * 24)
            occupancy_profile = get_year_profile_occupancy_hourly_per_room_method(room_type)
            lighting_yearly_profile = [month_variation if occ > 0 else light_off_value for occ, month_variation in zip(occupancy_profile, month_variation_profile_hourly)]

        if self.base_data.is_light_off_during_night(room_type) and nighttime_pattern_year_profile_bldg_hourly:
            lighting_yearly_profile = profile_generation.define_fix_nighttime_value(lighting_yearly_profile, light_off_value, nighttime_pattern_year_profile_bldg_hourly)

        return lighting_yearly_profile

    def __get_lighting_setpoint_var_for_room(self, room_type, variability_prc: float):
        setp_nom = self.base_data.get_lighting_setpoint(room_type)
        setp_variable = numpy.random.normal(setp_nom.m, setp_nom.m * variability_prc, 1)[0] * setp_nom.u  # remove unit for random, add again
        return setp_variable

    def __get_lighting_density_var_for_room(self, room_type):
        lighting_dens_triple = self.base_data.get_lighting_density_triple(room_type)
        unit = lighting_dens_triple[COL_STD].u
        (min, max, peak) = profile_variability.triang_dist_limits(lighting_dens_triple[COL_MIN].m, lighting_dens_triple[COL_MAX].m, lighting_dens_triple[COL_STD].m, perc=0.05)
        logging.getLogger(__name__).debug(f"lighting density limits used for triang dist: {min}, {max}, {peak}, with originals from SIA beeing \n{lighting_dens_triple}")
        return profile_variability.get_random_value_triangular_dist(min, max, peak) * unit
