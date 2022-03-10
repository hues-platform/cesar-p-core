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
from typing import Dict, Any
import pint

from cesarp.model.EnergySource import EnergySource
from cesarp.energy_strategy.input_parser_helper import get_energysource_vs_timeperiod_params_table, check_timeperiod


class FuelCosts:
    COL_NR_ENERGY_CARRIER = 0

    def __init__(self, ureg: pint.Quantity, energy_strategy_config: Dict[str, Any]):
        """
        :param ureg: pint UnitRegistry
        :param energy_strategy_config: dictonary with configuration entries of energy strategy in use
        """
        self.ureg = ureg
        self._es_cfg = energy_strategy_config
        self.fuel_costs_param = get_energysource_vs_timeperiod_params_table(
            self._es_cfg["FUEL"]["FUEL_COST_FACTORS_FILE"], self._es_cfg["TIME_PERIODS"], self.COL_NR_ENERGY_CARRIER
        )

    def get_fuel_cost_factor(self, energy_carrier: EnergySource, time_period: int):
        check_timeperiod(time_period, self._es_cfg["TIME_PERIODS"], "fuel cost factor")
        # fuel costs in input are in Rappen, thus /100 to convert to CHF
        return self.fuel_costs_param.loc[energy_carrier, time_period] / 100 * self.ureg.CHF / (self.ureg.kW * self.ureg.h)
