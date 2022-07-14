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
"""
Module providing functions to read and aggregate results of several buildings.
"""
import logging
import esoreader
import pandas as pd
import pint
from typing import Mapping, Sequence, Dict, Any, Optional
from pathlib import Path
import cesarp.common
from cesarp.results.EnergyDemandSimulationResults import EnergyDemandSimulationResults
from cesarp.eplus_adapter import _default_config_file
from cesarp.eplus_adapter.EPlusEioResultAnalyzer import EPlusEioResultAnalyzer
from cesarp.eplus_adapter.idf_strings import ResultsFrequency

_ESO_FILE_NAME = "eplusout.eso"

PD_FRAME_IDX_UNIT_NAME = "unit"
PD_FRAME_IDX_VAR_NAME = "name"
PD_FRAME_IDX_FID = "bldg_fid"
TOTAL_FLOOR_AREA_LABEL = "Total Floor Area"

RES_KEY_HEATING_DEMAND = "DistrictHeating:HVAC"
RES_KEY_DHW_DEMAND = "DistrictHeating:Building"
RES_KEY_EL_DEMAND = "Electricity:Facility"
RES_KEY_COOLING_DEMAND = "DistrictCooling:Facility"

_CESAR_SIMULATION_RESULT = [RES_KEY_HEATING_DEMAND, RES_KEY_DHW_DEMAND, RES_KEY_EL_DEMAND, RES_KEY_COOLING_DEMAND]


def check_cesar_results_are_enabled(custom_config: Optional[Dict[str, Any]] = None) -> bool:
    all_annual_res = _get_all_annual_vars_from_config(custom_config)
    return all([req_res in all_annual_res for req_res in _CESAR_SIMULATION_RESULT])


def collect_cesar_simulation_summary(result_folder, ureg: pint.UnitRegistry) -> EnergyDemandSimulationResults:
    res_dict = _cesar_summary_one_bldg_annual(result_folder, _CESAR_SIMULATION_RESULT, ureg)
    total_floor_area = EPlusEioResultAnalyzer(result_folder, ureg).get_total_floor_area()

    sim_res = EnergyDemandSimulationResults(
        tot_heating_demand=res_dict[RES_KEY_HEATING_DEMAND],
        tot_dhw_demand=res_dict[RES_KEY_DHW_DEMAND],
        tot_electricity_demand=res_dict[RES_KEY_EL_DEMAND],
        tot_cooling_demand=res_dict[RES_KEY_COOLING_DEMAND],
        total_floor_area=total_floor_area,
    )

    return sim_res


def _cesar_summary_one_bldg_annual(single_result_folder: str, res_param_keys, ureg: pint.UnitRegistry) -> Dict[str, pint.Quantity]:
    """
    Quite tailered function to assemble yearly results for one building. It should replicate the result summary excel file known from the cesar Matlab version.
    All energies (Unit J) are reported by square meter, which is done by dividing the per building demand by the total floor area.
    Includes the total floor area of the building, which is retrieved from the eio eplus results file.

    :param single_result_folder: folder with energy plus result files for one building (expected files: eplusout.eso and eplusout.eio)
    :param res_param_keys: name of result parameters to collect
    :param ureg: reference to unit registry object
    :param do_report_agg_val: names of result parameters to add as per building values
    :return: pandas.DataFrame with one row, columns with a multiindex of parameter name and unit
    """
    eso = esoreader.read_from_path(single_result_folder / Path(_ESO_FILE_NAME))

    res = dict()
    # res = pd.DataFrame(columns=pd.MultiIndex(levels=[[], []], codes=[[], []], names=[PD_FRAME_IDX_VAR_NAME, PD_FRAME_IDX_UNIT_NAME]))
    for res_param in res_param_keys:
        variables = eso.find_variable(res_param, key=None, frequency=ResultsFrequency.ANNUAL.value)
        for var in variables:
            (data, unit_str) = __get_data_series_with_unit(eso, var)
            data_w_unit = data[0] * ureg(unit_str) / ureg.year
            try:
                data_w_unit = data_w_unit.to(ureg.kWh / ureg.year)
            except pint.errors.DimensionalityError:
                pass
            res[var[2]] = data_w_unit
    return res


def collect_multi_params_for_site(result_folders: Mapping[int, str], result_keys: Sequence, results_frequency: ResultsFrequency) -> pd.DataFrame:
    """
    Returns data in a flat pandas DataFrame. Index is sequence from 0..n, columns are timing, fid, var (variable name), value, unit.
    You can import this data series e.g. into Excel and create a pivot table to analyze the data.

    To convert the result to a mutli-indexed DataFrame, do:
        `res_mi = res_df.set_index(["fid", "var", "unit"], append=True)`
    if you further want to convert the row-multiindex to column-multiindex, do:
        `res_tbl = res_mi.unstack(["fid", "var", "unit"])`
    To select data from the res_tbl with columns mutli-index, do:
        Select all results for certain fid:
            `fid_res = res_tbl.xs(1, level="fid", axis=1)`
        To remove the unit header do:
            `fid_res.columns = fid_res.columns.droplevel("unit")`
        Select all results for timestep 3 (if hourly that would be hour 4) - result is a series
        `res_tbl.loc[3]`

    :param result_folders: folders containing result files, one eso file named eplusout.eso is expected per folder
    :param result_keys: List of names of the result parameters to get. Parameter name has to point to unique result, e.g. DistrictHeating:HVAC (not only DistrictHeating).
    :param results_frequency: Time steps of results, e.g. RunPeriod, Hourly
    :return: pandas.DataFrame with MulitIndex, Level 0 fid, Level 1 result key
    """

    aggregated_res = pd.DataFrame(columns=["fid", "var", "value", "unit"])
    for fid, single_result_folder in result_folders.items():
        try:
            eso_path = single_result_folder / Path(_ESO_FILE_NAME)
            logging.getLogger(__name__).debug(f"Open {eso_path}")
            eso = esoreader.read_from_path(eso_path)
        except FileNotFoundError:
            logging.getLogger(__name__).warning(f"No {eso_path} not found. Skipping.")
            continue
        except Exception as msg:
            logging.getLogger(__name__).warning(f"Malformed eso {eso_path}. Skipping. Caused by: {msg}")
            continue
        for result_key in result_keys:
            try:
                vars_matching = eso.find_variable(result_key, frequency=results_frequency.value)
                if not vars_matching:
                    logging.getLogger(__name__).warning(f"{result_key} not found in {eso_path}. Skipping.")
                    continue
                (data, unit) = __get_data_series_with_unit(eso, vars_matching[0])
                res = pd.DataFrame(data, columns=["value"])
                res["fid"] = fid
                res["unit"] = unit
                res["var"] = result_key
                aggregated_res = pd.concat([aggregated_res, res], sort=False)
                aggregated_res.index.name = "timing"
            except Exception as msg:
                logging.getLogger(__name__).warning(f"Variable {result_key} could not be extracted from {eso_path}. Skipping this variable. Caused by: {msg}")
                continue
    return aggregated_res


def collect_single_param_for_site(result_folders: Mapping[int, str], result_key, results_frequency: ResultsFrequency) -> pd.DataFrame:
    """
    Get one result parameter for all buildings in a flat table structure.

    :param result_folders: mapping building fid to the result folder path, which is expected to contain a eplusout.eso
    :param result_key: name of the result parameter you want to collect
    :param results_frequency: frequency of the results
    :return: pandas.DataFrame, columns are timing (always 0 for frequency ANNUAL), fid, value and unit
    """
    res = collect_multi_params_for_site(result_folders, [result_key], results_frequency)
    return res.drop(result_key, axis=1)


def collect_multi_entry_annual_result(single_result_folder: str, var_name: str):

    eso = esoreader.read_from_path(single_result_folder / Path(_ESO_FILE_NAME))

    variable_instances = eso.dd.find_variable(var_name)

    results_dict = {}

    for var_def in variable_instances:
        # index pos 1 = entry name e.g. surface name
        (data, unit) = __get_data_series_with_unit(eso, var_def)
        assert len(data) == 1, f"data (f{var_def}) is not a single value, it has more than one value!"
        results_dict[var_def[1]] = data[0]

    return results_dict


def _get_all_annual_vars_from_config(custom_config: Optional[Dict[str, Any]] = None):
    cfg = cesarp.common.config_loader.load_config_for_package(_default_config_file, __package__, custom_config)
    try:
        output_meters = cfg["OUTPUT_METER"]["ANNUAL"]
    except KeyError:
        output_meters = []
    try:
        output_vars = cfg["OUTPUT_VARS"]["ANNUAL"]
    except KeyError:
        output_vars = []
    return output_meters + output_vars


def __get_data_series_with_unit(eso, var):
    idx = eso.dd.index[var]
    data = eso.data[idx]
    unit = eso.dd.variables[idx][3]
    return data, unit
