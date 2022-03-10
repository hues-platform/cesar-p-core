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
from typing import Protocol, Any
import pint

from cesarp.common.profiles import HOURS_PER_YEAR
from cesarp.SIA2024.demand_generators.BuildingTypeProtocol import BuildingTypeProtocol


class BaseDataForActivityProtocol(Protocol):
    """returns activity in MET (metabolic equivalent of task)"""

    def get_activity_level_per_person(self, room_type: Any) -> pint.Quantity:
        ...


class ActivityHeatGainCalculator:
    """
    Calculates the heat gain by people's activity in W/person for a building type
    Variability points:

    * area_pp_bldg (see get_people_activity_heat_gain_for_bldg)
    * area per person synthesized for the building, which can be based on area per person per room values with variability

    """

    def __init__(
        self,
        bldg_type: BuildingTypeProtocol,
        base_data_accessor: BaseDataForActivityProtocol,
        unit_reg: pint.UnitRegistry,
    ):
        """
        :param bldg_type: building type for which to calculate heat gain from activity, e.g. SIA2024BuildingType
        :param base_data_accessor: base profile data, e.g. SIA2024DataAccessor
        """
        self.bldg_type = bldg_type
        self.base_data = base_data_accessor
        self._unit_reg = unit_reg

    def get_activity_heat_gain_profile_for_bldg(self):
        return [self.get_people_activity_heat_gain_for_bldg()] * HOURS_PER_YEAR

    def get_people_activity_heat_gain_for_bldg(self):
        """
        :param ureg: pint unit registry
        :return: heat gain from activity in Watt/Person, aggregated for the whole building
        """
        BODY_SURFACE_AREA = 1.8 * self._unit_reg.m ** 2
        MET_TO_W_M2 = 58 * self._unit_reg.W / self._unit_reg.m ** 2

        synth_activity_level = self.bldg_type.synthesize_value_by_room_area(self.base_data.get_activity_level_per_person)

        return synth_activity_level.to(self._unit_reg.met).m * MET_TO_W_M2 * BODY_SURFACE_AREA / self._unit_reg.person
