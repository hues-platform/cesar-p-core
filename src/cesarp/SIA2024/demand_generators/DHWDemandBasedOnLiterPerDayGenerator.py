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
from typing import Callable, List, Protocol, Iterable, Dict
import pint
from pint import Quantity
import numpy as np
import logging
from cesarp.common.profiles import profile_generation, profile_variability, HOURS_PER_DAY
from cesarp.SIA2024.demand_generators.ValuePerKeyCache import ValuePerKeyCache
from cesarp.SIA2024.demand_generators.BuildingTypeProtocol import BuildingTypeProtocol
from cesarp.SIA2024 import COL_STD, COL_MIN, COL_MAX


class BaseDataForDHWBasedOnLitersPerDayProtocol(Protocol):
    def get_dhw_demand_liter_per_day_pp_std(self, room_type) -> pint.Quantity:
        """
        domestic hot water demand in liters/day per Person
        """
        ...

    def get_dhw_demand_liter_per_day_pp_triple(self, room_type) -> Dict[str, Quantity]:
        """
        Returns dict with entries COL_MIN, STD, MAX (defined in cesarp.common.profiles.__init__.py)
        """
        ...

    def is_dhw_off_during_night(self, room_type) -> bool:
        ...


class DHWDemandBasedOnLiterPerDayGenerator:
    """
    Generate electricity demand for domestic hotwater and fraction profile for dhw usage.

    The object is specific for one building. If variability is activated, the profile is cached, so repeated calls to
    get_occupancy_for_bldg() returns always the same profile.
    Variabilty points:

    - dhw power demand value (see __init__)
    - occcupancy profile (see get_dhw_profile_for_bldg())
    - nighttime pattern (see get_dhw_profile_for_bldg())
    - monthyl variation (see get_dhw_profile_for_bldg() and get_dhw_power_per_area_for_bldg())
    """

    def __init__(
        self,
        bldg_type: BuildingTypeProtocol,
        base_data_accessor: BaseDataForDHWBasedOnLitersPerDayProtocol,
        dhw_variability: bool,
        nominal_hotwater_temperature: pint.Quantity,
        coldwater_tmeperature: pint.Quantity,
        get_year_profile_occupancy_hourly_per_room_method: Callable[[str], List[float]],
        nighttime_pattern_yearly_profile: List[bool],
        get_year_profile_variation_monthly_for_room_method: Callable[[str], Iterable[float]],
        ureg: pint.UnitRegistry,
    ):
        """
        :param bldg_type: type of building for which to generate profile, e.g. object of SIA2024BuildingType
        :param base_data_accessor: base data, e.g. SIA2024DataAccessor
        :param dhw_variability: True if variability should be added to dhw l/day/person value
        :param nominal_hotwater_temperature: required temperature for the domestic hotwater in degree Celsius
        :param coldwater_tmeperature: inlet temperature of the water for preparing domestic hot water
        :param get_year_profile_occupancy_hourly_per_room_method: reference to method returning occupancy year profile defining hourly fraction [0...1] of full occupancy
        :param nighttime_pattern_yearly_profile: nighttime profile, to determine hours in which dhw should be turned off in case room is specified as such in excel input sheet
        :param get_year_profile_variation_monthly_for_room_method: reference to method returning monthly variation profile, defining full or partial occupancy as used in the occupancy profile; needed to scale DHW demand value correctly;
        """
        self._logger = logging.getLogger(__name__)
        self._base_data = base_data_accessor
        self._bldg_type = bldg_type
        self._ureg = ureg

        self._delta_temperature = nominal_hotwater_temperature - coldwater_tmeperature
        self._get_year_profile_occupancy_hourly_per_room_method = get_year_profile_occupancy_hourly_per_room_method
        self._nighttime_pattern_yearly_profile = nighttime_pattern_yearly_profile
        self._get_year_profile_variation_monthly_for_room_method = get_year_profile_variation_monthly_for_room_method

        self.__dhw_var_liter_per_day_per_room_cache = None
        if dhw_variability:
            self.__dhw_var_liter_per_day_per_room_cache = ValuePerKeyCache(self._bldg_type.get_room_types(), self.__get_dhw_liter_per_day_demand_variable_for_room)
            self._get_dhw_demand_liter_per_day_per_person_for_room_method = self.__dhw_var_liter_per_day_per_room_cache.lookup_value
        else:
            self._get_dhw_demand_liter_per_day_per_person_for_room_method = self._base_data.get_dhw_demand_liter_per_day_pp_std

    def get_dhw_power_per_area_for_bldg(self) -> float:
        """
        :return: electricity demand for dhw in W/m2 aggregated for the building
        """
        return self._bldg_type.synthesize_value_by_room_area(self.__get_dhw_power_per_area_for_room)

    def get_dhw_profile_for_bldg(self) -> List[float]:
        """
        Domestic Hotwater usage follows occupancy during day, during night dhw is off depending on room configuration "is dhw off during night" in additional input columns in SIA2024 excel input.
        :return: year profile defining hourly fraction of full load dhw demand [0...1]
        """
        return self._bldg_type.synthesize_profiles_yearly_by_room_area_for_bldg(
            self.__get_dhw_profile_for_room,
            additional_factor_per_room_method=self.__get_dhw_power_per_area_for_room,  # keep in mind, that method calls the method to generate a profile per room as well - make sure you don't get into recursion when reusing....
        )

    def __get_dhw_profile_for_room(self, room_type):
        dhw_profile_yearly = self._get_year_profile_occupancy_hourly_per_room_method(room_type)
        if self._base_data.is_dhw_off_during_night(room_type):
            dhw_profile_yearly = profile_generation.define_fix_nighttime_value(dhw_profile_yearly, self._base_data.get_dhw_night_value().m, self._nighttime_pattern_yearly_profile)
        return dhw_profile_yearly

    def __get_dhw_liter_per_day_demand_variable_for_room(self, room_type):
        dhw_lpd_triple = self._base_data.get_dhw_demand_liter_per_day_pp_triple(room_type)
        unit = dhw_lpd_triple[COL_MIN].u
        (min_lim, max_lim, peak) = profile_variability.triang_dist_limits(dhw_lpd_triple[COL_MIN].m, dhw_lpd_triple[COL_MAX].m, dhw_lpd_triple[COL_STD].m, perc=0.05)
        self._logger.debug(f"dhw demand in lpd limits used for triang dist: {min_lim}, {max_lim}, {peak}, with originals from SIA beeing \n{dhw_lpd_triple}")
        dhw_dem_val = profile_variability.get_random_value_triangular_dist(min_lim, max_lim, peak)
        dhw_dem_val = max(0, dhw_dem_val)  # make sure we do not get negative dhw demand values
        self._logger.debug(dhw_dem_val)
        return dhw_dem_val * unit

    def __get_dhw_power_per_area_for_room(self, room_type):
        """
        The monthly variation, which is included as 'Jahresgleichzeitigkeit' in the formula for Qw according to SIA2024/2016 1.3.8.7,
        is already included in the occupancy profile, thus for the daily hotwater usage
        do not include that factor as the daily hotwater usage will be mapped to hourly values by using the occupancy profile,
        which can have some variability which is propagated that way.
        """
        room_area_per_person = self._base_data.get_area_per_person_std(room_type)

        power_per_area = 0 * self._ureg.W / self._ureg.m ** 2
        if room_area_per_person > 0:
            volume_per_day_pp = self._get_dhw_demand_liter_per_day_per_person_for_room_method(room_type)

            RELATIVE_DENSITY_WATER = 1 * self._ureg.kg / self._ureg.liter
            SPECIFIC_HEAT_CAPACITY_WATER = 0.00116 * self._ureg.kWh / (self._ureg.kg * self._ureg.delta_degC)
            energy_per_area_per_day = (volume_per_day_pp * RELATIVE_DENSITY_WATER * SPECIFIC_HEAT_CAPACITY_WATER * self._delta_temperature) / room_area_per_person  # kWh/m2
            energy_per_area_per_day.ito_reduced_units()
            dhw_profile_for_room = self.__get_dhw_profile_for_room(room_type)
            monthly_variation = self._get_year_profile_variation_monthly_for_room_method(room_type)
            monthly_variation_hourly = profile_generation.expand_year_profile_monthly_to_hourly(monthly_variation, [1] * HOURS_PER_DAY)
            # the dhw energy demand when calculated as above from SIA2024 is for full load, thus we need to convert the profile back to full load (divide by the monthly variation profile)....
            # otherwise we get a too high yeary energy demand for the DHW
            # Note: when variability is on, there migth be cases where dhw profile is not zero when monthly variation is, actually introducing some error as we say the full load hours is 0 if monthly variation is 0...
            full_load_dhw_profile = np.divide(
                dhw_profile_for_room, monthly_variation_hourly, out=np.zeros_like(dhw_profile_for_room), where=[x != 0 for x in monthly_variation_hourly]
            )
            dhw_full_load_hours_per_year = sum(full_load_dhw_profile) * self._ureg.hour
            power_per_area = energy_per_area_per_day * (365 * self._ureg.d) / dhw_full_load_hours_per_year

        return power_per_area.to(self._ureg.W / self._ureg.m ** 2)
