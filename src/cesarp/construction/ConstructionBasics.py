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
from typing import Dict, Any, Optional
import pint

import cesarp.common
from cesarp.model.WindowConstruction import WindowFrameConstruction
from cesarp.model.BuildingConstruction import InstallationsCharacteristics, LightingCharacteristics
from cesarp.construction import _default_config_file
from cesarp.model.EnergySource import EnergySource


class ConstructionBasics:
    def __init__(self, ureg: pint.UnitRegistry, custom_config: Optional[Dict[str, Any]] = None):
        self._cfg = cesarp.common.config_loader.load_config_for_package(_default_config_file, __package__, custom_config)
        self.ureg = ureg

    def get_fixed_window_frame_construction(self):
        win_frame_props = self._cfg["FIXED_WINDOW_FRAME_CONSTRUCTION_PARAMETERS"]
        return WindowFrameConstruction(
            name=win_frame_props["name"],
            short_name=win_frame_props["name"],
            frame_conductance=self.ureg(win_frame_props["frame_conductance"]),
            frame_solar_absorptance=self.ureg(win_frame_props["frame_solar_absorptance"]),
            frame_visible_absorptance=self.ureg(win_frame_props["frame_visible_absorptance"]),
            outside_reveal_solar_absorptance=self.ureg(win_frame_props["outside_reveal_solar_absorptance"]),
            emb_co2_emission_per_m2=self.ureg(win_frame_props["embodied_co2_emission_per_m2"]),
            emb_non_ren_primary_energy_per_m2=self.ureg(win_frame_props["embodied_non_renewable_primary_energy_per_m2"]),
        )

    def get_inst_characteristics(self, e_carrier_dhw: Optional[EnergySource] = None, e_carrier_heating: Optional[EnergySource] = None):
        """get fixed installation characteristics and default CH EnergySource mix for DHW and HEATING"""
        props = self._cfg["FIXED_INSTALLATION_CHARACTERISTICS"]
        return InstallationsCharacteristics(
            fraction_radiant_from_activity=self.ureg(str(props["FRACTION_RADIANT_FROM_ACTIVITY"])),
            lighting_characteristics=LightingCharacteristics(
                self.ureg(str(props["LIGHTING_RETURN_AIR_FRACTION"])),
                self.ureg(str(props["LIGHTING_FRACTION_RADIANT"])),
                self.ureg(str(props["LIGHTING_FRACTION_VISIBLE"])),
            ),
            dhw_fraction_lost=self.ureg(str(props["DHW_FRACTION_LOST"])),
            electric_appliances_fraction_radiant=self.ureg(str(props["ELECTRIC_APPLIANCES_FRACTION_RADIANT"])),
            e_carrier_dhw=e_carrier_dhw,
            e_carrier_heating=e_carrier_heating,
        )
