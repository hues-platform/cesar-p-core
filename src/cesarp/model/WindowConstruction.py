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
from typing import List, Optional
from cesarp.model.BuildingElement import BuildingElement
from cesarp.model.WindowLayer import WindowLayer


@dataclass
class WindowFrameConstruction:
    name: str
    short_name: str
    frame_conductance: pint.Quantity  # must be convertible to W/(m⋅K)
    frame_solar_absorptance: pint.Quantity  # dimensionless
    frame_visible_absorptance: pint.Quantity  # dimensionless
    outside_reveal_solar_absorptance: pint.Quantity  # dimensionless
    emb_co2_emission_per_m2: Optional[pint.Quantity] = None  # expected to be kg*CO2eq/m2, embodied co2 emisson per m2 frame area
    emb_non_ren_primary_energy_per_m2: Optional[pint.Quantity] = None  # expected to be MJ*Oileq/m2, embodied pen per m2 frame area


@dataclass
class WindowGlassConstruction:
    name: str
    layers: List[WindowLayer]  # list order: first entry is external layer facing to outside environment, last entry is the internal layer facing the building inside
    emb_co2_emission_per_m2: Optional[pint.Quantity] = None
    emb_non_ren_primary_energy_per_m2: Optional[pint.Quantity] = None
    bldg_element: BuildingElement = BuildingElement.WINDOW
    retrofitted: bool = False

    @property
    def short_name(self):
        if "/" in self.name:
            return str(self.name.rsplit("/", 1)[1])
        else:
            return self.name

    def __hash__(self):
        return hash((self.name, self.short_name, self.layers))


@dataclass
class WindowShadingMaterial:
    is_shading_available: bool
    name: str
    solar_transmittance: pint.Quantity
    solar_reflectance: pint.Quantity
    visible_transmittance: pint.Quantity
    visible_reflectance: pint.Quantity
    infrared_hemispherical_emissivity: pint.Quantity
    infrared_transmittance: pint.Quantity
    conductivity: pint.Quantity
    thickness: pint.Quantity
    shade_to_glass_distance: pint.Quantity
    top_opening_multiplier: float
    bottom_opening_multiplier: float
    leftside_opening_multiplier: float
    rightside_opening_multiplier: float
    airflow_permeability: float

    @property
    def short_name(self):
        if "/" in self.name:
            return str(self.name.rsplit("/", 1)[1])
        else:
            return self.name

    @classmethod
    def create_empty_unavailable(cls):
        return cls(False, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None)


@dataclass
class WindowConstruction:
    frame: WindowFrameConstruction
    glass: WindowGlassConstruction
    shade: WindowShadingMaterial
    bldg_element: BuildingElement = BuildingElement.WINDOW

    @property
    def name(self):
        return self.glass.name + "_" + self.frame.name

    def __eq__(self, other):
        return self.frame == other.frame and self.glass == other.glass and self.bldg_element == other.bldg_element

    def __hash__(self):
        return hash((self.frame, self.glass, self.shade, self.bldg_element))
