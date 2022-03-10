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

from typing import Protocol, Optional
from cesarp.common.profiles import HOURS_PER_YEAR
from cesarp.SIA2024.demand_generators.ValuePerKeyCache import ValuePerKeyCache
from cesarp.SIA2024.demand_generators.BuildingTypeProtocol import BuildingTypeProtocol


class BaseDataForAreaPPProtocol(Protocol):
    def get_infiltration_rate(self, room_type) -> pint.Quantity:
        ...

    def get_infiltration_fraction_profile_base_value(self) -> pint.Quantity:
        ...


class InfiltrationRateGenerator:
    """
    Create infiltration fraction profile and get infiltration rate.
    Infiltration fraction profile is constant expect for special rooms with mechanical ventilation and pressurization.

    Points of Variability:

    - infiltration_rate (see __init__)
    - occupancy profile but only if mechanical ventilation is used in any room of the building and occupancy profile
      has variability when the room is occupied/unoccupied (see get_infiltration_profile_for_bldg)
    """

    def __init__(self, bldg_type: BuildingTypeProtocol, base_data_accessor):
        """
        :param bldg_type: type of building for which to generate profile, e.g. object of SIA2024BuildingType
        :param base_data_accessor: base data, e.g. SIA2024DataAccessor
        :param infiltration_rate_variability: True if variabillity should be introduced for infiltration rate value
        """
        self.base_data = base_data_accessor
        self.bldg_type = bldg_type

        self.__inf_rate_variable_per_room_cache: Optional[ValuePerKeyCache] = None
        self.__get_infiltration_rate_for_room_method = self.base_data.get_infiltration_rate_stock

    def activate_infiltrat_rate_variability(self, variability_perc: float):
        """
        :param variability_perc: defines the percentage of the standard value to use for randomization, e.g. if infiltration rate standard is 0.3 m3/h/m2 and
                                 variability_prc is 0.2 the variability range is 0.24...0.36m3/h/m2
        :return: nothing
        """
        assert variability_perc <= 1, f"please provide variability_perc as percentage in range 0..1, {variability_perc} was given"

        def wrap_get_inf_rate(room_type):
            return self.__get_infiltration_rate_variable_for_room(room_type, variability_perc)

        self.__inf_rate_variable_per_room_cache = ValuePerKeyCache(self.bldg_type.get_room_types(), wrap_get_inf_rate)
        self.__get_infiltration_rate_for_room_method = self.__inf_rate_variable_per_room_cache.lookup_value

    def get_infiltration_profile_for_bldg(self):
        """
        Currently fixed value profile.
        Infiltration rate reduction could be implemented for pressurized rooms,e.g. server room or lab with mechanical ventilation and pressurization.
        Such a feature was implemented in Matlab Cesar Version, but was not really used as only very few rooms would actually have a reduced ventilation rate.
        Thus for the cesar-p only a fixed infiltration profile was implemented.

        :return: year profile with hourly values defining fraction of infiltration
        """
        return [self.base_data.get_infiltration_fraction_profile_base_value().m] * HOURS_PER_YEAR

    def get_infiltration_for_bldg(self):
        """
        Variability can be set when initializing the object.
        :return: infiltration rate in !!!m3/(hm2)!!! for the building type
        """
        return self.bldg_type.synthesize_value_by_room_area(self.__get_infiltration_rate_for_room_method)

    def __get_infiltration_rate_variable_for_room(self, room_type, variability_prc):
        inf_nom = self.base_data.get_infiltration_rate_stock(room_type)
        return numpy.random.normal(inf_nom.m, inf_nom.m * variability_prc, 1) * inf_nom.u
