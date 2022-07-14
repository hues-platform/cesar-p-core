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

from cesarp.energy_strategy import get_selected_energy_strategy_cfg
from cesarp.energy_strategy.FuelCosts import FuelCosts
from cesarp.energy_strategy.SystemEfficiencies import SystemEfficiencies
from cesarp.energy_strategy.EnergyMix import EnergyMix


class EnergyStrategy:
    """
    parent interface class to hold together all interfaces for querying operational emission and cost values.
    you can also directly initialize the individual classes
    *RetrofitRates* is not included, as it is not used together with the operational emission and cost values.
    """

    def __init__(self, ureg: pint.UnitRegistry, custom_config: Optional[Dict[str, Any]] = None):
        es_cfg = get_selected_energy_strategy_cfg(custom_config)
        self.fuel_cost_factors = FuelCosts(ureg, es_cfg)
        self.system_efficiencis = SystemEfficiencies(es_cfg)
        self.energy_mix = EnergyMix(ureg, es_cfg)
