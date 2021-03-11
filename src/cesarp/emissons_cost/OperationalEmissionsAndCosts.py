# coding=utf-8
#
# Copyright (c) 2021, Empa, Leonie Fierz, Aaron Bojarski, Ricardo Parreira da Silva, Sven Eggimann.
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
from dataclasses import dataclass

import cesarp.common
from cesarp.emissons_cost import _default_config_file
from cesarp.energy_strategy.EnergyStrategy import EnergyStrategy
from cesarp.model.EnergySource import EnergySource
from cesarp.emissons_cost.EmissionAndCostCalculationError import EmissonAndCostCalculationError

FUEL_COST_UNIT = "CHF / year"
FUEL_DEMAND_UNIT = "kWh"
PEN_UNIT = "MJ * Oileq / m**2 / year"
CO2_EMISSION_UNIT = "kg * CO2eq / m ** 2 / year"
SPECIFIC_ENERGY_DEMAND_UNIT = "MJ / m ** 2 / year"


@dataclass
class PerSystemResults:

    pen: pint.Quantity
    co2_emission: pint.Quantity
    fuel_demand: pint.Quantity
    fuel_cost: pint.Quantity
    energy_carrier: EnergySource


@dataclass
class OperationalEmissionsAndCostsResult:
    total_pen: pint.Quantity
    total_co2_emission: pint.Quantity
    heating_system: PerSystemResults
    dhw_system: PerSystemResults
    electricity: PerSystemResults
    simulation_year: int


class OperationalEmissionsAndCosts:
    def __init__(self, ureg: pint.UnitRegistry, custom_config: Dict[str, Any] = {}):
        self._ureg = ureg
        self._cfg = cesarp.common.load_config_for_package(_default_config_file, __package__, custom_config)
        self._energy_strategy = EnergyStrategy(ureg, custom_config)

    def get_operational_emissions_and_costs(
        self,
        specific_dhw_demand: pint.Quantity,
        total_dhw_demand: pint.Quantity,
        dhw_carrier: EnergySource,
        specific_heating_demand: pint.Quantity,
        total_heating_demand: pint.Quantity,
        heating_carrier: EnergySource,
        specific_electricity_demand: pint.Quantity,
        total_electricity_demand: pint.Quantity,
        sim_year: int,
    ) -> OperationalEmissionsAndCostsResult:
        """
        :param specific_dhw_demand: unit convertible to Ws/m2/year
        :param total_dhw_demand: unit convertible to Ws/year
        :param dhw_carrier:
        :param specific_heating_demand:
        :param total_heating_demand:
        :param heating_carrier:
        :param specific_electricity_demand:
        :param total_electricity_demand:
        :param sim_year:
        :return: data object containing the results for this building
        """

        heating_res: PerSystemResults = self._calc_heating_emissions_and_costs(specific_heating_demand, total_heating_demand, heating_carrier, sim_year)
        dhw_res: PerSystemResults = self._calc_dhw_emissions_and_costs(specific_dhw_demand, total_dhw_demand, dhw_carrier, sim_year)
        el_res: PerSystemResults = self._calc_electricity_emissions_and_costs(specific_electricity_demand, total_electricity_demand, sim_year)
        total_pen = heating_res.pen + dhw_res.pen + el_res.pen
        total_co2_emission = heating_res.co2_emission + dhw_res.co2_emission + el_res.co2_emission

        return OperationalEmissionsAndCostsResult(
            total_pen=total_pen, total_co2_emission=total_co2_emission, heating_system=heating_res, dhw_system=dhw_res, electricity=el_res, simulation_year=sim_year,
        )

    def _calc_heating_emissions_and_costs(
        self, specific_heating_energy_demand: pint.Quantity, total_heating_energy_demand: pint.Quantity, heating_energy_carrier: EnergySource, sim_year: int,
    ):
        if heating_energy_carrier == EnergySource.NO:  # no cost and emissions if energy source is NO - same as procedure in Matlab version
            return PerSystemResults(
                pen=0 * self._ureg(PEN_UNIT),
                co2_emission=0 * self._ureg(CO2_EMISSION_UNIT),
                fuel_demand=0 * self._ureg(FUEL_DEMAND_UNIT),
                fuel_cost=0 * self._ureg(FUEL_COST_UNIT),
                energy_carrier=heating_energy_carrier,
            )
        heating_sys_eff = self._energy_strategy.system_efficiencis.get_heating_system_efficiency(heating_energy_carrier, sim_year)
        heating_value_factor = self._energy_strategy.system_efficiencis.get_heating_value_factor(heating_energy_carrier, sim_year)
        pen_factor = self._energy_strategy.energy_mix.get_pen_factor_for(heating_energy_carrier, sim_year)
        co2_coeff = self._energy_strategy.energy_mix.get_co2_coeff_for(heating_energy_carrier, sim_year)
        fuel_cost_factor = self._energy_strategy.fuel_cost_factors.get_fuel_cost_factor(heating_energy_carrier, sim_year)

        if heating_sys_eff == 0:
            raise EmissonAndCostCalculationError(
                f"Could not calculate heating cost and emissions because heating system efficiency for energy carrier {heating_energy_carrier} "
                f"and simulation year {sim_year} is 0"
            )
        fuel_demand = total_heating_energy_demand / heating_sys_eff
        fuel_cost = (fuel_demand * fuel_cost_factor).to(FUEL_COST_UNIT)
        specific_heating_energy_demand = specific_heating_energy_demand.to(SPECIFIC_ENERGY_DEMAND_UNIT)
        co2_emission = (specific_heating_energy_demand / heating_sys_eff * co2_coeff * heating_value_factor).to(CO2_EMISSION_UNIT)
        pen = (specific_heating_energy_demand / heating_sys_eff * pen_factor * heating_value_factor).to(PEN_UNIT)

        return PerSystemResults(pen, co2_emission, fuel_demand, fuel_cost, heating_energy_carrier)

    def _calc_dhw_emissions_and_costs(
        self, specific_dhw_energy_demand: pint.Quantity, total_dhw_energy_demand: pint.Quantity, dhw_energy_carrier: EnergySource, sim_year: int,
    ):
        if dhw_energy_carrier == EnergySource.NO:
            return PerSystemResults(
                pen=0 * self._ureg(PEN_UNIT),
                co2_emission=0 * self._ureg(CO2_EMISSION_UNIT),
                fuel_demand=0 * self._ureg(FUEL_DEMAND_UNIT),
                fuel_cost=0 * self._ureg(FUEL_COST_UNIT),
                energy_carrier=dhw_energy_carrier,
            )

        dhw_sys_eff = self._energy_strategy.system_efficiencis.get_dhw_system_efficiency(dhw_energy_carrier, sim_year)
        heating_value_factor = self._energy_strategy.system_efficiencis.get_heating_value_factor(dhw_energy_carrier, sim_year)
        pen_factor = self._energy_strategy.energy_mix.get_pen_factor_for(dhw_energy_carrier, sim_year)
        co2_coeff = self._energy_strategy.energy_mix.get_co2_coeff_for(dhw_energy_carrier, sim_year)
        fuel_cost_factor = self._energy_strategy.fuel_cost_factors.get_fuel_cost_factor(dhw_energy_carrier, sim_year)

        if dhw_sys_eff == 0:
            raise EmissonAndCostCalculationError(
                f"Could not calculate dhw cost and emissions because dhw system efficiency for energy carrier {dhw_energy_carrier} " f"and simulation year {sim_year} is 0"
            )

        specific_dhw_energy_demand = specific_dhw_energy_demand.to(self._ureg.MJ / self._ureg.m ** 2 / self._ureg.year)
        pen = specific_dhw_energy_demand / dhw_sys_eff * pen_factor * heating_value_factor
        co2_emission = specific_dhw_energy_demand / dhw_sys_eff * co2_coeff * heating_value_factor
        fuel_demand = total_dhw_energy_demand / dhw_sys_eff
        fuel_cost = (fuel_demand * fuel_cost_factor).to(FUEL_COST_UNIT)
        return PerSystemResults(pen, co2_emission, fuel_demand, fuel_cost, dhw_energy_carrier)

    def _calc_electricity_emissions_and_costs(self, specific_el_demand: pint.Quantity, total_el_demand: pint.Quantity, sim_year):
        pen_factor = self._energy_strategy.energy_mix.get_pen_factor_for(EnergySource.ELECTRICITY, sim_year)
        co2_coeff = self._energy_strategy.energy_mix.get_co2_coeff_for(EnergySource.ELECTRICITY, sim_year)
        fuel_cost_factor = self._energy_strategy.fuel_cost_factors.get_fuel_cost_factor(EnergySource.ELECTRICITY, sim_year)

        pen = specific_el_demand * pen_factor
        co2_emission = specific_el_demand * co2_coeff
        fuel_cost = total_el_demand * fuel_cost_factor

        return PerSystemResults(
            pen=pen.to(PEN_UNIT), co2_emission=co2_emission.to(CO2_EMISSION_UNIT), fuel_demand=total_el_demand, fuel_cost=fuel_cost, energy_carrier=EnergySource.ELECTRICITY,
        )
