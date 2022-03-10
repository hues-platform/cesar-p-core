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
from typing import Dict, Any
from cesarp.model.WindowConstruction import WindowGlassConstruction
from dataclasses import dataclass


@dataclass
class ShadingObjectConstruction:
    diffuse_solar_reflectance_unglazed_part: pint.Quantity
    diffuse_visible_reflectance_unglazed_part: pint.Quantity
    glazing_ratio: pint.Quantity
    window_glass_construction: WindowGlassConstruction

    @classmethod
    def init_from_dict(
        cls,
        props_as_dict: Dict[str, Any],
        window_glass_construction: WindowGlassConstruction,
        unit_reg: pint.UnitRegistry,
    ):
        return ShadingObjectConstruction(
            diffuse_solar_reflectance_unglazed_part=unit_reg(props_as_dict["diffuse_solar_reflectance_unglazed_part"]),
            diffuse_visible_reflectance_unglazed_part=unit_reg(props_as_dict["diffuse_visible_reflectance_unglazed_part"]),
            glazing_ratio=unit_reg(props_as_dict["glazing_ratio"]),
            window_glass_construction=window_glass_construction,
        )
