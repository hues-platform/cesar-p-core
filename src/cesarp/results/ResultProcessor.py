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
import logging
import pandas as pd
from collections import OrderedDict
from typing import Dict, Any, Tuple, Optional, Union
from enum import Enum
from pathlib import Path

from cesarp.emissons_cost.OperationalEmissionsAndCosts import (
    OperationalEmissionsAndCosts,
    OperationalEmissionsAndCostsResult,
    PEN_UNIT,
    CO2_EMISSION_UNIT,
)
import cesarp.eplus_adapter.eplus_eso_results_handling
from cesarp.eplus_adapter.eplus_error_file_handling import (
    check_eplus_error_level,
    EplusErrorLevel,
    EPLUS_ERROR_FILE_NAME,
)
from cesarp.results.EnergyDemandSimulationResults import EnergyDemandSimulationResults
from cesarp.model.EnergySource import EnergySource


_EPLUS_ERROR_LEVEL_COL_NAME = "EnergyPlus error level"


class ColHeaderSimResult(Enum):
    FID = "Original FID"
    HEATING_DEMAND = "Heating Annual"
    DHW_DEMAND = "DHW Annual"
    ELECTRICITY_DEMAND = "Electricity Annual"
    COOLING_DEMAND = "Cooling Annual"
    HEATING_DEMAND_SPEC = "Heating Annual specific"
    DHW_DEMAND_SPEC = "DHW Annual specific"
    ELECTRICITY_DEMAND_SPEC = "Electricity Annual specific"
    COOLING_DEMAND_SPEC = "Cooling Annual specific"
    FLOOR_AREA = "Total bldg floor area"


class ColHeaderFuelCosts(Enum):
    FID = "Original FID"
    HEATING = "Heating - Fuel Costs"
    DHW = "DHW - Fuel Costs"
    EL = "Electricity - Costs"
    SIM_YEAR = "Year used for lookup of cost factors"


class ColHeaderPENCO2(Enum):
    FID = "Original FID"
    PEN_TOTAL = "Total PEN"
    PEN_HEATING = "PEN Heating"
    PEN_DHW = "PEN DHW"
    PEN_EL = "PEN Elec"
    CO2_TOTAL = "Total CO2"
    CO2_HEATING = "CO2 Heating"
    CO2_DHW = "CO2 DHW"
    CO2_EL = "CO2 Elec"
    SIM_YEAR = "Year used for lookup of factors for PEN and CO2 calculation"


class ResultProcessor:
    """
    Handles annual results aggregation.
    In case energy carriers for heating and domestic hot water are provided, operational emissions and costs are calculated.

    Usage:
    1. initialize the class
    2. call *process_results_for* for each of the buildings
    3. get all results with *get_all_results*

    :return: [description]
    :rtype: [type]
    """

    MULTI_IDX_NAMES = ["unit", "var_name"]

    def __init__(self, ureg: pint.UnitRegistry, do_calc_op_emissions_and_costs: bool = True, custom_config: Optional[Dict[str, Any]] = None):
        self.ureg = ureg
        self._do_calc_op_emissions_and_costs = do_calc_op_emissions_and_costs
        self._op_emission_cost_calc: Optional[OperationalEmissionsAndCosts] = None
        if self._do_calc_op_emissions_and_costs:
            self._op_emission_cost_calc = OperationalEmissionsAndCosts(ureg, custom_config=custom_config)
        self.eplus_err_level_per_bldg: Dict[int, EplusErrorLevel] = dict()
        self.simulation_result_per_bldg: Dict[int, Optional[EnergyDemandSimulationResults]] = dict()
        self.emission_and_cost_per_bldg: Dict[int, Optional[OperationalEmissionsAndCostsResult]] = dict()
        self._logger = logging.getLogger(__name__)

    def process_results_for(
        self,
        fid: int,
        eplus_result_folder: Union[Path, str],
        heating_energy_carrier: Optional[EnergySource],
        dhw_energy_carrier: Optional[EnergySource],
        sim_year: Optional[int],
    ) -> Tuple[EplusErrorLevel, Optional[EnergyDemandSimulationResults], Optional[OperationalEmissionsAndCostsResult]]:
        """
        Call this method for each building you want to add the results.
        Besides returning the results for that building, they are added to the class instance variable *simulation_result_per_bldg*.

        :param fid: building fid to process
        :type fid: int
        :param eplus_result_folder: EnergyPlus results folder
        :type eplus_result_folder: Union[Path, str]
        :param heating_energy_carrier: energy carrier used for heating for given building
        :type heating_energy_carrier: Optional[EnergySource]
        :param dhw_energy_carrier: energy carrier used for domestic hot water for given building
        :type dhw_energy_carrier: Optional[EnergySource]
        :param sim_year: simulation year, used to lookup cost and emission values
        :type sim_year: Optional[int]
        :return: see type
        :rtype: Tuple[EplusErrorLevel, Optional[EnergyDemandSimulationResults], Optional[OperationalEmissionsAndCostsResult]]
        """
        emission_and_costs = None
        sim_res: EnergyDemandSimulationResults = None  # type: ignore
        eplus_err_level = check_eplus_error_level(eplus_result_folder / Path(EPLUS_ERROR_FILE_NAME))
        if eplus_err_level != EplusErrorLevel.FATAL:
            sim_res = cesarp.eplus_adapter.eplus_eso_results_handling.collect_cesar_simulation_summary(eplus_result_folder, self.ureg)
        if self._op_emission_cost_calc:
            if dhw_energy_carrier and heating_energy_carrier and sim_year:
                emission_and_costs = self._op_emission_cost_calc.get_operational_emissions_and_costs(
                    sim_res.specific_dhw_demand,
                    sim_res.tot_dhw_demand,
                    dhw_energy_carrier,
                    sim_res.specific_heating_demand,
                    sim_res.tot_heating_demand,
                    heating_energy_carrier,
                    sim_res.specific_electricity_demand,
                    sim_res.tot_electricity_demand,
                    sim_year,
                )
            else:
                self._logger.error(
                    f"operational cost and emission results requested, dhw energy source "
                    f"{dhw_energy_carrier} or heating energy sourc {heating_energy_carrier} or "
                    f"simulation year {sim_year} is None"
                )

        self.eplus_err_level_per_bldg[fid] = eplus_err_level
        self.simulation_result_per_bldg[fid] = sim_res
        if emission_and_costs:
            self.emission_and_cost_per_bldg[fid] = emission_and_costs

        return (eplus_err_level, sim_res, emission_and_costs)

    def get_all_results(self) -> pd.DataFrame:
        if self.emission_and_cost_per_bldg:
            return pd.concat(
                [
                    self.convert_demand_results_to_df(self.simulation_result_per_bldg, self.ureg),
                    self.convert_emissions_to_df(self.emission_and_cost_per_bldg, self.ureg),
                    self.convert_fuel_cost_to_df(self.emission_and_cost_per_bldg, self.ureg),
                ],
                axis="columns",
            )
        else:
            return self.convert_demand_results_to_df(self.simulation_result_per_bldg, self.ureg)

    @staticmethod
    def convert_demand_results_to_df(sim_res_per_bldg: Dict[int, Optional[EnergyDemandSimulationResults]], ureg: pint.UnitRegistry) -> pd.DataFrame:
        """
        Precondition: you did run get_simulation_result(...) for all the buildings that should appear in the summary
        :return: pandas DataFrame that was written to the file
        """
        sim_res_rows_tot_demand = []
        sim_res_rows_specific_demand = []
        row_index = []
        demand_specific_u = ureg.kW * ureg.h / ureg.m ** 2 / ureg.year
        demand_tot_u = ureg.kW * ureg.h / ureg.year

        floor_area_unit = ureg.m ** 2
        sim_res_floor_area = pd.DataFrame(columns=["floor_area"])
        sim_res_floor_area.columns = pd.MultiIndex.from_arrays(
            [[floor_area_unit], [ColHeaderSimResult.FLOOR_AREA.value]],
            names=ResultProcessor.MULTI_IDX_NAMES,
        )

        for fid, sim_res in sim_res_per_bldg.items():
            if sim_res is not None:
                row_tot: OrderedDict = OrderedDict()
                row_tot[ColHeaderSimResult.HEATING_DEMAND] = sim_res.tot_heating_demand.to(demand_tot_u).m
                row_tot[ColHeaderSimResult.DHW_DEMAND] = sim_res.tot_dhw_demand.to(demand_tot_u).m
                row_tot[ColHeaderSimResult.ELECTRICITY_DEMAND] = sim_res.tot_electricity_demand.to(demand_tot_u).m
                row_tot[ColHeaderSimResult.COOLING_DEMAND] = sim_res.tot_cooling_demand.to(demand_tot_u).m
                sim_res_rows_tot_demand.append(row_tot)
                row_spec: OrderedDict = OrderedDict()
                row_spec[ColHeaderSimResult.HEATING_DEMAND_SPEC] = sim_res.specific_heating_demand.to(demand_specific_u).m
                row_spec[ColHeaderSimResult.DHW_DEMAND_SPEC] = sim_res.specific_dhw_demand.to(demand_specific_u).m
                row_spec[ColHeaderSimResult.ELECTRICITY_DEMAND_SPEC] = sim_res.specific_electricity_demand.to(demand_specific_u).m
                row_spec[ColHeaderSimResult.COOLING_DEMAND_SPEC] = sim_res.specific_cooling_demand.to(demand_specific_u).m
                sim_res_rows_specific_demand.append(row_spec)
                row_index.append(fid)
                sim_res_floor_area.loc[fid] = [sim_res.total_floor_area.to(floor_area_unit).m]

        col_names_tot = [k.value for k in sim_res_rows_tot_demand[0].keys()]
        demand_tot = pd.DataFrame(data=sim_res_rows_tot_demand, index=row_index)
        demand_tot.columns = pd.MultiIndex.from_arrays(
            [[str(demand_tot_u)] * len(col_names_tot), col_names_tot],
            names=ResultProcessor.MULTI_IDX_NAMES,
        )

        col_names_spec = [k.value for k in sim_res_rows_specific_demand[0].keys()]
        demand_spec = pd.DataFrame(data=sim_res_rows_specific_demand, index=row_index)
        demand_spec.columns = pd.MultiIndex.from_arrays(
            [[str(demand_specific_u)] * len(col_names_spec), col_names_spec],
            names=ResultProcessor.MULTI_IDX_NAMES,
        )

        return pd.concat([demand_tot, demand_spec, sim_res_floor_area], axis="columns")

    @staticmethod
    def convert_eplus_error_level_to_df(eplus_error_level_per_bldg: Dict[int, EplusErrorLevel]) -> pd.DataFrame:
        all_eplus_err_df = pd.DataFrame.from_dict(eplus_error_level_per_bldg, orient="index", columns=[_EPLUS_ERROR_LEVEL_COL_NAME])
        eplus_err_options = "|".join(el.name for el in sorted(EplusErrorLevel, key=lambda x: x.value))
        all_eplus_err_df.columns = pd.MultiIndex.from_arrays(
            [[eplus_err_options], [_EPLUS_ERROR_LEVEL_COL_NAME]],
            names=ResultProcessor.MULTI_IDX_NAMES,
        )
        return all_eplus_err_df

    @staticmethod
    def convert_fuel_cost_to_df(emission_and_cost_per_bldg: Dict[int, Optional[OperationalEmissionsAndCostsResult]], ureg: pint.UnitRegistry) -> pd.DataFrame:
        """
        Precondition: you did run get_emissions(...) for all the buildings that should appear in the summary
        :return: pandas DataFrame that was written to the file
        """
        fuel_cost_rows = []
        row_index = []
        fuel_cost_unit = ureg.CHF / ureg.year
        for fid, e_and_c in emission_and_cost_per_bldg.items():
            if e_and_c is not None:
                row: OrderedDict = OrderedDict()
                row[ColHeaderFuelCosts.HEATING] = e_and_c.heating_system.fuel_cost.to(fuel_cost_unit).m
                row[ColHeaderFuelCosts.DHW] = e_and_c.dhw_system.fuel_cost.to(fuel_cost_unit).m
                row[ColHeaderFuelCosts.EL] = e_and_c.electricity.fuel_cost.to(fuel_cost_unit).m
                row[ColHeaderFuelCosts.SIM_YEAR] = e_and_c.simulation_year
                fuel_cost_rows.append(row)
                row_index.append(fid)

        # Attention, the column index created here has to have the exact same order as the row dictionaries!
        col_keys = [
            ColHeaderFuelCosts.HEATING.value,
            ColHeaderFuelCosts.DHW.value,
            ColHeaderFuelCosts.EL.value,
            ColHeaderFuelCosts.SIM_YEAR.value,
        ]

        col_multiindex = pd.MultiIndex.from_arrays([[str(fuel_cost_unit)] * 3 + [""], col_keys], names=ResultProcessor.MULTI_IDX_NAMES)
        fuel_costs_table = pd.DataFrame(data=fuel_cost_rows, columns=fuel_cost_rows[0].keys(), index=row_index)
        fuel_costs_table.columns = col_multiindex
        return fuel_costs_table

    @staticmethod
    def convert_emissions_to_df(emission_and_cost_per_bldg: Dict[int, Optional[OperationalEmissionsAndCostsResult]], ureg: pint.UnitRegistry) -> pd.DataFrame:
        """
        Precondition: you did run get_emissions(...) for all the buildings that should appear in the summary
        :return: pandas DataFrame that was written to the file
        """
        emissions_rows = []
        emissions_row_index = []
        pen_unit = ureg(PEN_UNIT).u
        co2_unit = ureg[CO2_EMISSION_UNIT].u
        for fid, e_and_c in emission_and_cost_per_bldg.items():
            if e_and_c is not None:
                row: OrderedDict = OrderedDict()
                row[ColHeaderPENCO2.PEN_TOTAL] = e_and_c.total_pen.to(pen_unit).m
                row[ColHeaderPENCO2.PEN_HEATING] = e_and_c.heating_system.pen.to(pen_unit).m
                row[ColHeaderPENCO2.PEN_DHW] = e_and_c.dhw_system.pen.to(pen_unit).m
                row[ColHeaderPENCO2.PEN_EL] = e_and_c.electricity.pen.to(pen_unit).m
                row[ColHeaderPENCO2.CO2_TOTAL] = e_and_c.total_co2_emission.to(co2_unit).m
                row[ColHeaderPENCO2.CO2_HEATING] = e_and_c.heating_system.co2_emission.to(co2_unit).m
                row[ColHeaderPENCO2.CO2_DHW] = e_and_c.dhw_system.co2_emission.to(co2_unit).m
                row[ColHeaderPENCO2.CO2_EL] = e_and_c.electricity.co2_emission.to(co2_unit).m
                row[ColHeaderPENCO2.SIM_YEAR] = e_and_c.simulation_year
                emissions_rows.append(row)
                emissions_row_index.append(fid)

        # Attention, the column index created here has to have the exact same order as the row dictionaries!
        column_index: OrderedDict = OrderedDict()
        column_index[ColHeaderPENCO2.PEN_TOTAL.value] = str(pen_unit)
        column_index[ColHeaderPENCO2.PEN_HEATING.value] = str(pen_unit)
        column_index[ColHeaderPENCO2.PEN_DHW.value] = str(pen_unit)
        column_index[ColHeaderPENCO2.PEN_EL.value] = str(pen_unit)
        column_index[ColHeaderPENCO2.CO2_TOTAL.value] = str(co2_unit)
        column_index[ColHeaderPENCO2.CO2_HEATING.value] = str(co2_unit)
        column_index[ColHeaderPENCO2.CO2_DHW.value] = str(co2_unit)
        column_index[ColHeaderPENCO2.CO2_EL.value] = str(co2_unit)
        column_index[ColHeaderFuelCosts.SIM_YEAR.value] = ""

        col_multiindex = pd.MultiIndex.from_arrays([column_index.values(), column_index.keys()], names=ResultProcessor.MULTI_IDX_NAMES)
        emissions_table = pd.DataFrame(data=emissions_rows, columns=emissions_rows[0].keys(), index=emissions_row_index)
        emissions_table.columns = col_multiindex
        return emissions_table
