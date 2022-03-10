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
from dataclasses import dataclass
import pint
from typing import Union

from cesarp.model.TransparentMaterial import TransparentMaterial
from cesarp.model.Gas import Gas


@dataclass
class WindowLayer:
    name: str
    thickness: pint.Quantity
    material: Union[TransparentMaterial, Gas]

    @property
    def short_name(self):
        if "/" in self.name:
            return str(self.name.rsplit("/", 1)[1])
        else:
            return self.name

    @property
    def thermal_resistance(self):
        return self.thickness / self.material.conductivity
