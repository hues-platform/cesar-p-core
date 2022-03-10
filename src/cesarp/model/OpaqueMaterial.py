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
from typing import Optional
from dataclasses import dataclass
import pint
from enum import Enum


class OpaqueMaterialRoughness(Enum):
    VERY_ROUGH = "VeryRough"
    ROUGH = "Rough"
    MEDIUM_ROUGH = "MediumRough"
    MEDIUM_SMOOTH = "MediumSmooth"
    SMOOTH = "Smooth"
    VERY_SMOOTH = "VerySmooth"


@dataclass
class OpaqueMaterial:
    name: str
    density: Optional[pint.Quantity]
    roughness: OpaqueMaterialRoughness
    solar_absorptance: pint.Quantity
    specific_heat: Optional[pint.Quantity]
    thermal_absorptance: pint.Quantity
    conductivity: pint.Quantity
    visible_absorptance: pint.Quantity
    co2_emission_per_kg: Optional[pint.Quantity] = None
    non_renewable_primary_energy_per_kg: Optional[pint.Quantity] = None

    @property
    def co2_emission_per_m3(self) -> Optional[pint.Quantity]:
        if self.co2_emission_per_kg:
            return self.co2_emission_per_kg * self.density
        else:
            return None

    @property
    def non_renewable_primary_energy_per_m3(self) -> Optional[pint.Quantity]:
        if self.non_renewable_primary_energy_per_kg:
            return self.non_renewable_primary_energy_per_kg * self.density
        else:
            return None

    @property
    def short_name(self) -> str:
        if "/" in self.name:
            return str(self.name.rsplit("/", 1)[1])
        else:
            return self.name

    def is_mass_fully_specified(self) -> bool:
        return self.density is not None and self.specific_heat is not None

    def are_emissions_fully_specified(self) -> bool:
        return self.co2_emission_per_kg is not None and self.non_renewable_primary_energy_per_kg is not None and self.density is not None
