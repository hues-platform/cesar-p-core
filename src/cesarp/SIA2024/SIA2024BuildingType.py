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
from typing import Dict, Callable, List
from enum import Enum

from cesarp.common.profiles import HOURS_PER_YEAR


class SIA2024BldgTypeKeys(Enum):
    """these names have to match with the building types defined in the building type YML configuration referenced from config"""

    MFH = 1
    SFH = 2
    OFFICE = 3
    SCHOOL = 4
    SHOP = 5
    RESTAURANT = 6
    HOSPITAL = 7


class SIA2024BuildingType:
    def __init__(self, bldg_type_key: str, sia_name: str, sia_nr, rooms: Dict, is_residential: bool):
        assert round(sum(rooms.values()), 4) == 1, f"for {bldg_type_key} sum of area fractions is is {sum(rooms.values())}, but should be 1 (eq 100%)"
        self.bldg_type_key = bldg_type_key
        # sia name and sia nr are currently only for completness of data and debugging
        self.sia_name = sia_name
        self.sia_nr = sia_nr
        self.__rooms = rooms
        self.is_residential = is_residential

    def get_room_types(self):
        return list(self.__rooms.keys())

    def get_room_types_area_fraction(self):
        return self.__rooms

    def synthesize_value_by_room_area(self, value_per_room_method: Callable[[Enum], float]):

        synthesized_value = sum([value_per_room_method(room_type) * room_area_fraction for room_type, room_area_fraction in self.__rooms.items()])
        return synthesized_value

    def synthesize_profiles_yearly_by_room_area_for_bldg(
        self,
        profile_per_room_method: Callable[[Enum], List[float]],
        additional_factor_per_room_method: Callable[[Enum], float] = None,
    ):
        if additional_factor_per_room_method is not None:
            add_factor_synth = self.synthesize_value_by_room_area(additional_factor_per_room_method)

        synth_prof = [0] * HOURS_PER_YEAR
        for room_type, room_area_fraction in self.__rooms.items():
            if additional_factor_per_room_method is not None:
                add_factor_room = (additional_factor_per_room_method(room_type) / add_factor_synth).m
            else:
                add_factor_room = 1
            profile_room = profile_per_room_method(room_type)
            synth_prof = [val_synth + val_room * room_area_fraction * add_factor_room for val_synth, val_room in zip(synth_prof, profile_room)]

        return synth_prof
