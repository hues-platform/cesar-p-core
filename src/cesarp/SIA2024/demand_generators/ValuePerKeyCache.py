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
from typing import Callable, List, Any


class ValuePerKeyCache:
    def __init__(self, cache_keys: List[Any], value_calc_for_key_method: Callable[[str], Any]):
        """
        :param cache_keys: keys for the cache
        :param value_calc_for_key_method: method to calculate the value to be stored, Argument should match key type
        """
        self.__init_lookup_table(cache_keys, value_calc_for_key_method)

    def __init_lookup_table(self, cache_keys, var_value_calc_method: Callable[[str], Any]):
        self.value_per_room_lookup_table = {room_type: var_value_calc_method(room_type) for room_type in cache_keys}

    def lookup_value(self, cache_key):
        return self.value_per_room_lookup_table[cache_key]
