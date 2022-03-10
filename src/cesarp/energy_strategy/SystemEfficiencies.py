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

from cesarp.model.EnergySource import EnergySource
from cesarp.energy_strategy.input_parser_helper import get_energysource_vs_timeperiod_params_table, check_timeperiod


class SystemEfficiencies:
    """
    The heating value factor is needed, because the primary
    energy factors are based on the higher heating value (Brennwert) but the
    system efficiencies for DHW and Heating are based on the lower heating
    value (Heizwert). These factors deliver the necessary coefficients for
    the correct calculation of the primary energy and co2 emissions!

    """

    COL_NR_ENERGY_CARRIER = 0  # for DHW_SYSTEM_EFFICIENCY_FILE and HEATING_SYSTEM_EFFICIENCY_FILE

    def __init__(self, energy_strategy_config: Dict[str, Any]):
        """
        :param ureg: pint UnitRegistry
        :param energy_strategy_config: dictonary with configuration entries of energy strategy in use
        """
        # self.age_class_archetype_dict = self.__get_constructional_archetype_per_age_class(custom_config)
        self._es_cfg = energy_strategy_config
        self.time_periods = self._es_cfg["TIME_PERIODS"]
        self.dhw_system_efficiencies = get_energysource_vs_timeperiod_params_table(
            self._es_cfg["EFFICIENCIES"]["DHW_SYSTEM_EFFICIENCY_FILE"], self.time_periods, self.COL_NR_ENERGY_CARRIER
        )
        self.heating_system_efficiencies = get_energysource_vs_timeperiod_params_table(
            self._es_cfg["EFFICIENCIES"]["HEATING_SYSTEM_EFFICIENCY_FILE"],
            self.time_periods,
            self.COL_NR_ENERGY_CARRIER,
        )
        self.heating_value_factor = get_energysource_vs_timeperiod_params_table(
            self._es_cfg["EFFICIENCIES"]["HEATING_VALUE_FACTOR_FILE"], self.time_periods, self.COL_NR_ENERGY_CARRIER
        )

    def get_dhw_system_efficiency(self, carrier: EnergySource, sim_year: int):
        check_timeperiod(sim_year, self.time_periods, "dhw system efficiency")
        return self.dhw_system_efficiencies.loc[carrier, sim_year]

    def get_heating_system_efficiency(self, carrier: EnergySource, sim_year: int):
        check_timeperiod(sim_year, self.time_periods, "heating system efficiency")
        return self.heating_system_efficiencies.loc[carrier, sim_year]

    def get_heating_value_factor(self, carrier: EnergySource, sim_year: int):
        """
        DHW and Heating system efficiencies are based on a lower heating value (Heizwert) of the energy source,
        but the Primary Energy Factors used in cesarp.energy_strategy.EnergyMix for CO2 coefficient and PEN factors
        are based on the higher heating value (Brennwert). Use this correction factor if you want to use both those
        sources for a calculation.

        :param carrier: energy carrier for which to get the correction factor
        :param sim_year: time period for which to get the correction factor (only for a few of the energy sources the correction is actually dependent on the time period)
        :return: heating value correction factor from lower to higher heating value
        """
        check_timeperiod(sim_year, self.time_periods, "heating value factor")
        return self.heating_value_factor.loc[carrier, sim_year]
