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
from typing import Dict, Any, Optional
import logging

import cesarp.common
from cesarp.retrofit.embodied import _default_config_file
from cesarp.model.Construction import Construction
from cesarp.model.WindowConstruction import WindowConstruction


class RetrofitEmbodiedEmissions:
    """
    Access to emissions for retrofit of opaque constructions such as walls, roof etc and windows.
    Windows have separate emission factors for the glass and for the frame.
    """

    def __init__(self, ureg: pint.UnitRegistry, custom_config: Optional[Dict[str, Any]] = None):
        self._cfg = cesarp.common.load_config_for_package(_default_config_file, __package__, custom_config)
        self.ureg = ureg
        self.logger = logging.getLogger(__name__)

    def get_constr_ret_emb_co2(self, constr: Construction) -> pint.Quantity:
        return sum([layer.material.co2_emission_per_m3 * layer.thickness for layer in constr.layers if layer.retrofitted])

    def get_constr_ret_emb_non_renewable_pen(self, constr: Construction) -> pint.Quantity:
        """Non renewable primary energy / embodied energy in MJ Oil-eq"""
        return sum([layer.material.non_renewable_primary_energy_per_m3 * layer.thickness for layer in constr.layers if layer.retrofitted])

    def get_win_ret_glass_emb_co2(self, win_constr: WindowConstruction) -> pint.Quantity:
        return win_constr.glass.emb_co2_emission_per_m2

    def get_win_ret_glass_emb_non_renewable_pen(self, win_constr: WindowConstruction) -> pint.Quantity:
        return win_constr.glass.emb_non_ren_primary_energy_per_m2

    def get_win_ret_frame_emb_co2(self, win_constr: WindowConstruction) -> pint.Quantity:
        return win_constr.frame.emb_co2_emission_per_m2

    def get_win_ret_frame_emb_non_renewable_pen(self, win_constr: WindowConstruction) -> pint.Quantity:
        return win_constr.frame.emb_non_ren_primary_energy_per_m2
