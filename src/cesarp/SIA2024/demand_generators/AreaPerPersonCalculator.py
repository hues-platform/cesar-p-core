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
import logging
import pint
from typing import Protocol, Dict

from cesarp.common.profiles import profile_variability
from cesarp.SIA2024.demand_generators.ValuePerKeyCache import ValuePerKeyCache
from cesarp.SIA2024.demand_generators.BuildingTypeProtocol import BuildingTypeProtocol
from cesarp.SIA2024 import COL_STD, COL_MIN, COL_MAX


class BaseDataForAreaPPProtocol(Protocol):
    def get_area_per_person_std(self, room_type) -> pint.Quantity:
        ...

    def get_area_per_person_triple(self, room_type) -> Dict[str, pint.Quantity]:
        ...


class AreaPerPersonCalculator:
    """
    Gets the area per person per room and aggregated for the building.

    The object is specific for one building. If variability is activated, the area_per_person per room is cached,
    so repeated calls to get_area_pp_for_room() and get_area_pp_for_bldg() return the same value for the same object.
    """

    def __init__(self, bldg_type: BuildingTypeProtocol, base_data_accessor, area_pp_variability: bool):
        """
        :param bldg_type: building type for which to calculate the area per person, e.g. SIA2024_2015_BuildingType
        :param base_data_accessor: object providing access to base data, e.g. SIA2024DataAccessor
        :param area_pp_variability:
        """
        self._logger = logging.getLogger(__name__)
        self.base_data = base_data_accessor
        self.bldg_type = bldg_type
        self.area_pp_per_room_variable_cache = None
        self.area_pp_for_room_method = self.base_data.get_area_per_person_std
        if area_pp_variability:
            self.area_pp_per_room_variable_cache = ValuePerKeyCache(self.bldg_type.get_room_types(), self.__calc_area_pp_var_for_room)
            self.area_pp_for_room_method = self.area_pp_per_room_variable_cache.lookup_value

    def get_area_pp_for_room(self, room_type):
        """
        Returns the area of given room.
        Whether variability is introduced for the room area is defined in the constructor.
        :return: area per person for specific room type, m2/person
        """
        return self.area_pp_for_room_method(room_type)

    def get_area_pp_for_bldg(self):
        """
        Synthesize "area per person" for the building by combining the area per person of the different room types.

        Synthesizing is done with the inverse value, "person per area", which gets the
        average number of persons in the building. This takes into account that the stated area per person refers to the
        area available per person when a maximum of persons are in that room.

        :return: area per person aggregated for the building, m2/person
        """

        def get_pers_per_area(room_type):
            room_area_pp = self.get_area_pp_for_room(room_type)
            if room_area_pp != 0:
                return 1 / room_area_pp
            else:
                return 0

        synth_persons_per_area = self.bldg_type.synthesize_value_by_room_area(get_pers_per_area)
        if synth_persons_per_area != 0:
            synth_area_per_person = 1 / synth_persons_per_area
        else:
            synth_area_per_person = 0
        self._logger.debug(f"area_per_person for {self.bldg_type} is {synth_area_per_person}")
        return synth_area_per_person

    def __calc_area_pp_var_for_room(self, room_type):
        area_triple = self.base_data.get_area_per_person_triple(room_type)
        unit = area_triple[COL_STD].u
        (min, max, peak) = profile_variability.triang_dist_limits(area_triple[COL_MIN].m, area_triple[COL_MAX].m, area_triple[COL_STD].m, perc=0.05)
        self._logger.debug(f"area per person limits used for triang dist: {min}, {max}, {peak}, with originals from SIA beeing \n{area_triple}")
        return profile_variability.get_random_value_triangular_dist(min, max, peak) * unit
