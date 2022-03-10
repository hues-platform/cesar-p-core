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
import pint
from typing import List, Optional
from dataclasses import dataclass
from cesarp.model.BuildingElement import BuildingElement
from cesarp.model.Layer import Layer


@dataclass
class Construction:
    name: str
    layers: List[Layer]  # layer at index 0 is external/outside
    bldg_element: BuildingElement
    co2_emission_per_m2: Optional[pint.Quantity] = None
    non_renewable_primary_energy_per_m2: Optional[pint.Quantity] = None

    @property
    def retrofitted(self) -> bool:
        return any(layer.retrofitted for layer in self.layers)

    @property
    def short_name(self) -> str:
        if "/" in self.name:
            return str(self.name.rsplit("/", 1)[1])
        else:
            return self.name
