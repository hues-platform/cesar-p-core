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
from dataclasses import dataclass
from enum import Enum

from cesarp.model.OpaqueMaterial import OpaqueMaterial


class LayerFunction(Enum):
    """
    Layer function defines the purpose of the layer. The numbering of the elements is chosen in a way that
    one can sort the layers according to those enum number values and gets a reasonable ordering.
    """

    OUTSIDE_FINISH = 1
    INSULATION_OUTSIDE = 21
    INSULATION_OUTSIDE_BACK_VENTILATED = 22
    INSULATION_INSIDE = 23
    INSULATION_IN_BETWEEN = 25
    INSIDE_FINISH = 3
    UNKNOWN = 0


@dataclass
class Layer:
    name: str
    thickness: pint.Quantity
    material: OpaqueMaterial
    retrofitted: bool = False
    function: LayerFunction = LayerFunction.UNKNOWN

    @property
    def short_name(self) -> str:
        if "/" in self.name:
            return str(self.name.rsplit("/", 1)[1])
        else:
            return self.name

    @property
    def thermal_resistance(self) -> pint.Quantity:
        return self.thickness / self.material.conductivity
