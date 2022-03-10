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
from typing import Protocol, List
from cesarp.common.profiles import profile_variability
from cesarp.SIA2024.demand_generators.ValuePerKeyCache import ValuePerKeyCache
from cesarp.SIA2024.demand_generators.BuildingTypeProtocol import BuildingTypeProtocol


class BaseDataForVariationMonthlyProtocol(Protocol):
    def get_monthly_variation(self, room_type) -> List[float]:
        ...


class VariationMonthly:
    """
    Generate a profile with monthly variation. In case there is no variability it's just a lookup in the base data.

    The object is specific for one building. If variability is activated, the monthly profile per room type is cached,
    so repeated calls to get_monthly_variation_per_room() for the same room type returns always the same profile.

    Points of variability:

    - monthly values, see __init__ parameter vertical_variability
    """

    def __init__(
        self,
        bldg_type: BuildingTypeProtocol,
        base_data: BaseDataForVariationMonthlyProtocol,
        vertical_variability: float,
    ):
        """
        :param bldg_type: building type for which to get monthly variation, e.g. object of SIA2024BuildingType
        :param base_data: base data, e.g. SIA2024ParametersFactory
        :param vertical_variability: value > 0 (and <1) for variability of monthly values, if 0 nominal values without variability are used
        """
        self.base_data = base_data

        if vertical_variability > 0:

            def wrap_get_monthly_var_prof(room_type):
                return self.__generate_monthly_variation_variable(room_type, vertical_variability)

            self.monthly_variation_variable_per_room_cache = ValuePerKeyCache(bldg_type.get_room_types(), wrap_get_monthly_var_prof)
            self.__get_monthly_variation_per_room_method = self.monthly_variation_variable_per_room_cache.lookup_value
        else:
            self.__get_monthly_variation_per_room_method = self.base_data.get_monthly_variation

    def get_monthly_variation_per_room(self, room_type):
        return self.__get_monthly_variation_per_room_method(room_type)

    def __generate_monthly_variation_variable(self, room_type, vertical_variability):
        monthly_variation_nom = self.base_data.get_monthly_variation(room_type)
        return profile_variability.randomize_vertical(values=monthly_variation_nom, band=vertical_variability)
