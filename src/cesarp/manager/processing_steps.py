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
Methods running in process pool need to be top-level module methods, thus for each
processing step there is such a method.
Methods with suffix "_no_exception" catch exceptions caused by an error in a single building.
This is useful when many buildings are run at once and an error in one building should not lead to termination
of the whole site run.
Those methods are not really intended to be used from outside manager package... if you do, read descriptions and
study the type of the arguments and return values carefully.
"""

import os
import logging
import pandas as pd
import pint
import time
from typing import Dict, Tuple, List, Optional
from pathlib import Path

import cesarp.common
from cesarp.model.BuildingModel import BuildingModel
from cesarp.manager.BldgModelFactory import BldgModelFactory
from cesarp.eplus_adapter.CesarIDFWriter import CesarIDFWriter
import cesarp.eplus_adapter.eplus_sim_runner
from cesarp.eplus_adapter.eplus_error_file_handling import EplusErrorLevel
from cesarp.emissons_cost.OperationalEmissionsAndCosts import OperationalEmissionsAndCostsResult
from cesarp.results.EnergyDemandSimulationResults import EnergyDemandSimulationResults
from cesarp.results.ResultProcessor import ResultProcessor


def all_preparation_steps_batch_no_exception(
    bldg_fids_to_do,
    custom_config,
    sia_params_gen_lock,
    idf_save_folder,
    idf_file_pattern,
    profiles_files_handler,
):
    (bldg_models, per_bldg_infos, bldg_model_creation_failed) = create_bldg_models_batch_no_exception(bldg_fids_to_do, custom_config, sia_params_gen_lock)

    idf_pathes = {fid: str(idf_save_folder / Path(idf_file_pattern.format(fid))) for fid in bldg_models.keys()}
    write_idf_res = {fid: bldg_model_to_idf_no_exception(model, idf_pathes[fid], profiles_files_handler, custom_config) for fid, model in bldg_models.items()}
    weather_files = {}
    idf_pathes_written = {}
    idf_write_failed = []
    for fid, (successful, idf_path, weather_file) in write_idf_res.items():
        if successful:
            weather_files[fid] = weather_file
            idf_pathes_written[fid] = idf_path
        else:
            idf_write_failed.append(fid)

    if bldg_model_creation_failed:
        logging.getLogger(__name__).error(f"bldg model creation failed for fids {bldg_model_creation_failed}")
    if idf_write_failed:
        logging.getLogger(__name__).error(f"idf writing failed for fids {idf_write_failed}")
    all_failed_fids = bldg_model_creation_failed + idf_write_failed
    return (idf_pathes_written, weather_files, bldg_models, per_bldg_infos, all_failed_fids)


def create_bldg_models_batch_no_exception(bldg_fids_to_create_model_for, config, sia_params_gen_lock) -> Tuple[Dict[int, BuildingModel], pd.DataFrame, List[int]]:
    """
    Method used to create building models for a batch of fids.
    Module-Level method to be able to parallelize to mutliple processes.
    For building model creation we need to load all site vertices which is memory and time intensive, thus
    it makes sense to create one BldgModelFactory and reuse the instance for several buildings.

    :param args:
    :return: tuple with three entries (sucessfully created building models,
                                       infos per building used during model creation,
                                       fids for which building model could not be created)
    """
    bldg_models_factory = BldgModelFactory(pint.get_application_registry(), config, sia_params_gen_lock)

    bldg_models = {bldg_fid: _create_bldg_model_no_exception(bldg_fid, bldg_models_factory) for bldg_fid in bldg_fids_to_create_model_for}  # type: ignore
    failed_fids = [fid for fid, model in bldg_models.items() if not model]
    bldg_models_successful = {fid: model for fid, model in bldg_models.items() if model}
    per_bldg_infos = bldg_models_factory.per_bldg_infos_used.loc[bldg_fids_to_create_model_for]
    return (bldg_models_successful, per_bldg_infos, failed_fids)


def _create_bldg_model_no_exception(bldg_fid, bldg_models_factory: BldgModelFactory):
    try:
        return bldg_models_factory.create_bldg_model(bldg_fid)
    except Exception as ex:
        logger = logging.getLogger(__name__)
        logger.error(f"Could not create builing model for {bldg_fid}. Skip this building and continue....")
        logger.exception(ex)
    return None


def bldg_model_to_idf_no_exception(bldg_model, idf_file_path, profiles_files_handler, custom_config):
    """
    For each building defined it creates building geometry, construction and internal conditions and writes the
    assembled information to and idf file.

    :param args: list with [bldg_model: BuildingModel, idf_file_path, profiles_file_handler, custom_config], for last three see arguments of cesarp.eplus_adapter.CesarIDFWriter()
    :param idf_file_path: full filepath to idf file to be created
    :return: tuple(fid, True, weather_file) when idf writing was successful, tuple(fid, False, None) otherwise
    """
    unit_reg = pint.get_application_registry()

    logger = logging.getLogger(__name__)

    try:
        logger.info(f"create idf and get weather file for building fid {bldg_model.fid}, {idf_file_path}")
        my_idf_writer = CesarIDFWriter(idf_file_path, unit_reg, profiles_files_handler, custom_config=custom_config)
        my_idf_writer.write_bldg_model(bldg_model)
        return (True, idf_file_path, bldg_model.site.weather_file_path)
    except Exception as ex:
        fid = bldg_model.fid if bldg_model else None
        if os.path.isfile(idf_file_path):
            os.remove(idf_file_path)
        logger.error(f"Could not write IDF for {fid}")
        logger.exception(ex)
        return (False, None, None)


def run_simulation_no_exception(idf_path, weather_file, output_folder, config_eplus):
    start = time.time()
    logger = logging.getLogger(__name__)
    try:
        logger.info(f"run e+ with idf {idf_path}")
        cesarp.eplus_adapter.eplus_sim_runner.run_single(idf_path, weather_file, output_folder, ep_config=config_eplus)
        return (True, time.time() - start)
    except Exception as ex:
        logger.error(f"Exception during simulation run for {idf_path}")
        logger.exception(ex)
    return (False, time.time() - start)


def _collect_result_summary_batch(
    input_tuples_per_fid, do_calc_op_emissions_and_costs, custom_config
) -> Tuple[Dict[int, EplusErrorLevel], Dict[int, Optional[EnergyDemandSimulationResults]], Dict[int, Optional[OperationalEmissionsAndCostsResult]]]:
    """
    :param input_tuples_per_fid: {fid: (eplus_output_folder, heating_energy_carrier, dhw_energy_carrier, simulation_year)}}
    :param custom_config: custom configuration entries
    :return: (simulation res table, emission res table, fuel cost res table)
    """
    unit_reg = pint.get_application_registry()
    res_processor = ResultProcessor(unit_reg, do_calc_op_emissions_and_costs, custom_config)
    for (
        fid,
        (eplus_output_folder, heating_energy_carrier, dhw_energy_carrier, sim_year),
    ) in input_tuples_per_fid.items():
        res_processor.process_results_for(fid, eplus_output_folder, heating_energy_carrier, dhw_energy_carrier, sim_year)
    return (
        res_processor.eplus_err_level_per_bldg,
        res_processor.simulation_result_per_bldg,
        res_processor.emission_and_cost_per_bldg,
    )


def log_error(val):
    logger = logging.getLogger(__name__)
    logger.error("Error happend in a worker process:")
    logger.exception(val)
