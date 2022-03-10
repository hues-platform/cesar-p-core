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
import statistics
import random
import pint


class MinMaxValue:
    def __init__(self, min: pint.Quantity, max: pint.Quantity):
        assert min.u == max.u, f"MinMaxValue initialized with non-matching units for min ({min.u}) and max ({max.u})"
        self._min = min.m
        self._max = max.m
        self._unit = min.u

    def get_default(self) -> pint.Quantity:
        return statistics.mean([self._min, self._max]) * self._unit

    def get_random(self) -> pint.Quantity:
        return random.uniform(self._min, self._max) * self._unit

    def get_value(self, random: bool = True) -> pint.Quantity:
        if random:
            return self.get_random()
        return self.get_default()

    def __eq__(self, other):
        return self._min == other._min and self._max == other._max and self._unit == other._unit
