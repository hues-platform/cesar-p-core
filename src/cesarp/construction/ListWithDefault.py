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
import random


class ListWithDefault:
    def __init__(self, all_options, default):
        assert default in all_options, f"you set a default, {default} which is not available as an option"
        self._default = default
        self._all_options = all_options

    def _get_default(self):
        return self._default

    def _get_random(self):
        return random.choice(self._all_options)

    def get_value(self, random):
        if random:
            return self._get_random()
        return self._get_default()

    def __eq__(self, other):
        return self._default == other._default and self._all_options == other._all_options
