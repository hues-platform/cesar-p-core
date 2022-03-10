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
import logging
import copy

from typing import Iterable, Dict, Any, Optional, Set, Sequence, List, Union
import multiprocessing
import atexit
import math
from multiprocessing.managers import SyncManager, BaseManager
import pandas as pd
import os
from pathlib import Path
import pint
import glob
import shutil

import cesarp.eplus_adapter
import cesarp.common
from cesarp.common import config_loader
import cesarp.common.filehandling
import cesarp.common.DatasetMetadata
from cesarp.manager import processing_steps

from cesarp.model.BuildingModel import BuildingModel
from cesarp.manager.BuildingContainer import BuildingContainer
from cesarp.manager import _default_config_file
from cesarp.manager.FileStorageHandler import FileStorageHandler, get_timestamp
from cesarp.manager.ProjectSaver import ProjectSaver
from cesarp.results.EnergyDemandSimulationResults import EnergyDemandSimulationResults
from cesarp.results.ResultProcessor import OperationalEmissionsAndCostsResult
import cesarp.eplus_adapter.eplus_eso_results_handling
import cesarp.eplus_adapter.eplus_sim_runner
from cesarp.eplus_adapter.eplus_error_file_handling import EPLUS_ERROR_FILE_NAME
from cesarp.eplus_adapter.idf_strings import ResultsFrequency
from cesarp.results.ResultProcessor import ResultProcessor
from cesarp.eplus_adapter.RelativeAuxiliaryFilesHandler import RelativeAuxiliaryFilesHandler


def define_fid_batches(all_fids, nr_of_batches):
    nr_of_bldgs = len(all_fids)
    per_worker = math.ceil(nr_of_bldgs / nr_of_batches)
    if per_worker < 10:
        per_worker = 10
        nr_of_batches = math.ceil(nr_of_bldgs / per_worker)
    fid_batches = []
    for i in range(0, nr_of_batches):
        start_index = i * per_worker
        if start_index < nr_of_bldgs:
            end_index = min(nr_of_bldgs, (i + 1) * per_worker)
            fid_batches.append(all_fids[start_index:end_index])
    return fid_batches


class MyManager(BaseManager):
    pass


MyManager.register("AuxFilesHandler", RelativeAuxiliaryFilesHandler)


class SimulationManager:
    """
    Main interface for basic cesar-p-core library usage.

    - Extract and aggregate building geometry, construction, internal gains and control schedules from the different input sources.
    - Create IDF file
    - Run simulation
    - Collect simulation results

    All input sources and parametrization can be defined by passing a custom configuration file when creating your
    SimulationManager instance. For each sub-module there are reasonable defaults set and you only need to set the
    configuration parameters you want to overwrite in your custom configuration. For the manager config you have to
    set at SITE_VERTICES_FILE, BLDG_INFORMATION_FILE, BLDG_TYPE_PER_BLDG_FILE and WEATHER_FILE as those do not point to any valid
    file by default. Depending on the settings you need to specify some more pathes which point by default to not existing files.

    Within the SimulationManager a worker pool is started and each of the workflow steps
    (createing building models, writing the IDF, running simulation, collecting results) are distributed to those workers.
    The number of worker processes is configurable in the configuration, property NR_OF_PARALLEL_WORKERS.
    Make sure that you have the if-guard *__name__ == "__main__"* in your main script when using the SimulationManager,
    as the workers started will re-execute the parts of your main script not protectd by that guard.

    Exceptions and errors processing one of the buildings are reported and execution is pursued with the next building.
    FID's of buildings where something went wrong are saved to member failed_fids, so you can check after running if you
    do not want to scan the console output manually.

    """

    def __init__(
        self,
        base_output_path: Union[str, Path],
        main_config: Union[str, Path, Dict[str, Any]],
        unit_reg: pint.UnitRegistry,
        load_from_disk: bool = False,
        fids_to_use: List[int] = None,
        delete_old_logs=True,
    ):
        """
        :param base_output_path: full folder path where idf, eplus output and other cesar-p output and intermediate files are stored.
        :type base_output_path: Union[str, Path]
        :param main_config: either dict with configuration entries or path to custom config yml file.
                            for details about how the configuration works see class description
        :type main_config: Union[str, Path, Dict[str, Any]]
        :param unit_reg: pint Unit Registry application wide instance ()
        :type unit_reg: pint.UnitRegistry
        :param load_from_disk: True if you want to load existing simulation files into memory. cannot be combined with fids_to_use, defaults to False
        :type load_from_disk: bool
        :param fids_to_use: pass list of FID's for which called methods on the manager object should be performed, if not provided all fids defined in the input file are used
        :type fids_to_use: List[int]
        :param delete_old_logs: if true old \\*-cesarp-logs folder are deleted when a new worker pool is created
        :type delete_old_logs: bool
        """
        self.logger = logging.getLogger(__name__)
        assert not (load_from_disk and (fids_to_use is not None)), "if load_from_disk is True you cannot pass fids_to_use"
        self._unit_reg = unit_reg
        self.delete_old_logs = delete_old_logs

        if not isinstance(main_config, dict):
            self._custom_config = config_loader.load_config_full(main_config)
        else:
            self._custom_config = main_config
        self.__validate_custom_config(self._custom_config)

        self._mgr_config = config_loader.load_config_for_package(_default_config_file, __package__, self._custom_config)

        self._storage = FileStorageHandler(base_output_path, self._custom_config, reloading=load_from_disk)

        self.failed_fids: Set[int] = set()

        self._worker_pool = None

        if not fids_to_use:
            fids_to_use = self.get_fids_from_config()
        self._fids_to_use = fids_to_use

        self.bldg_containers = self._init_empty_bldg_containers(fids_to_use)
        self.output_folders: Dict[int, str] = {}
        self.idf_pathes: Dict[int, str] = {}
        self.weather_files: Dict[int, str] = {}

        if load_from_disk:
            self.bldg_containers = self._storage.load_existing_bldg_containers()
            self.idf_pathes = self._storage.load_existing_idfs()
            if self.idf_pathes:
                self.weather_files = self._storage.load_existing_weather_mapping()
            self.output_folders = self._storage.load_existing_result_folders()
            self._fids_to_use = list(set(list(self.bldg_containers.keys()) + list(self.idf_pathes.keys()) + list(self.output_folders.keys())))

    def __validate_custom_config(self, custom_config: Dict[str, Any]):
        wrong_entries, _, _ = config_loader.validate_custom_cesarp_config(custom_config, self.logger)
        if wrong_entries:
            raise cesarp.common.CesarpException.CesarpException("Validation of custom/main configuration failed! Check Log output for details and your configuration entries.")

    @property
    def base_output_path(self):
        return self._storage.base_output_path

    def is_ready_to_run_sim(self):
        return self.idf_pathes and all(fid in self.weather_files.keys() for fid in self.idf_pathes.keys())

    def is_demand_results_available(self):
        """return True if at least for one building energy demand results are available"""
        try:
            for bldg_c in self.bldg_containers.values():
                if not bldg_c.has_error():
                    return bldg_c.has_demand_result()
        except KeyError:  # no bldg_containers
            return False

    def _init_empty_bldg_containers(self, fids_to_use=None):
        if not fids_to_use:
            fids_to_use = self.get_fids_from_config()
        return {fid: BuildingContainer() for fid in fids_to_use}

    def get_fids_from_config(self) -> List[int]:
        """
        You can use this method as a base if you want to run e.g. 100 buildings of your site, but the fid's are not consecutive. You would just pass e.g. the first 100 entries
        returned by this method to run_all_steps().
        To accomplish permanently that only part of your buildings are simulated, adapt the file referenced by configuration entry "BLDG_FID_FILE".

        :return: list of all fid's of the site
        """
        all_bldg_fids = cesarp.common.csv_reader.read_csvy(
            self._mgr_config["BLDG_FID_FILE"]["PATH"],
            ["gis_fid"],
            self._mgr_config["BLDG_FID_FILE"]["LABELS"],
            self._mgr_config["BLDG_FID_FILE"]["SEPARATOR"],
            "gis_fid",
        )
        bldg_gis_ids_to_simulate = all_bldg_fids["gis_fid"].to_list()
        return bldg_gis_ids_to_simulate

    def run_all_steps(self) -> None:
        """
        Extract and aggregate building information, create IDF and run EnergyPlus simulation for given building gis fid's.
        Uses a pool of parallel workers.
        Input file pathes are specified in config, see cesarp.manager.default_config.yml for details.

        :return: summary result with all annual output parameters
        """
        try:
            self.create_bldg_models()
            self.create_IDFs()
            self.run_simulations()
            self.process_results()
            self.save_bldg_containers()
            self.save_summary_result()
        except Exception as e:
            self.save_bldg_containers()
            raise e

    def save_summary_result(self):
        self._storage.save_result_summary(self.get_all_results_summary(), self.__get_metadata_full_run())

    def save_bldg_containers(self):
        self._storage.save_bldg_containers(self.bldg_containers)

    def create_bldg_models(self) -> Set[int]:
        """
        Initializes the building model for given fid's.
        The building model is filled with data depending on the configuration settings  (custom_config and default config of each package used) and attached factories.

        :return: fid's for which BuildingModel creation failed
        """
        worker_pool = self._get_worker_pool()
        fid_batches = define_fid_batches(list(self.bldg_containers.keys()), worker_pool._processes)
        sia_params_gen_lock = self._get_lock()
        job_res_list = [
            self._get_worker_pool().apply_async(
                processing_steps.create_bldg_models_batch_no_exception,
                (fid_batch, self._custom_config, sia_params_gen_lock),
            )
            for fid_batch in fid_batches
        ]
        result_per_worker = [res.get() for res in job_res_list]

        all_per_bldg_info_used = pd.DataFrame()
        bldg_model_creation_failed: Set[int] = set()
        all_bldg_models: Dict[int, BuildingModel] = {}
        for (bldg_models_successful, per_bldg_infos, failed_fids) in result_per_worker:
            all_bldg_models.update(bldg_models_successful)
            all_per_bldg_info_used = pd.concat([all_per_bldg_info_used, per_bldg_infos], sort=False)
            bldg_model_creation_failed.update(failed_fids)

        for fid, bldg_model in all_bldg_models.items():
            self.bldg_containers[fid].set_bldg_model(bldg_model)

        if bldg_model_creation_failed:
            self.logger.error(f"bldg model creation failed for fids {bldg_model_creation_failed}")
            self.failed_fids.update(bldg_model_creation_failed)
            for fid in bldg_model_creation_failed:
                self.bldg_containers[fid].set_error()
        self._storage.save_bldg_infos_used(all_per_bldg_info_used)
        return bldg_model_creation_failed

    def create_IDFs(self) -> Sequence[int]:
        """
        Create IDF input files according to building models for all buildings which have a model assigned
        :return: fid's for which IDF creation failed
        """
        aux_fh = self._get_managed_aux_fh()

        idf_pathes_to_write = self._storage.create_idf_output_pathes(self._get_fids_having_bldg_model())
        assert idf_pathes_to_write, "No of the buildings has a model assigned. call create_bldg_models() first."

        job_res_dict = {
            fid: self._get_worker_pool().apply_async(
                processing_steps.bldg_model_to_idf_no_exception,
                (self.bldg_containers[fid].get_bldg_model(), idf_path_for_fid, aux_fh, self._custom_config),
                error_callback=processing_steps.log_error,
            )
            for fid, idf_path_for_fid in idf_pathes_to_write.items()
        }
        res_tuples_dict = {fid: res.get() for fid, res in job_res_dict.items()}

        idf_write_failed = []
        # the entries of the result correspond to the return values of processing_steps.bldg_model_to_idf_no_exception
        for fid, (successful, idf_path, weather_file) in res_tuples_dict.items():
            if successful:
                self.weather_files[fid] = weather_file
                self.idf_pathes[fid] = idf_path
            else:
                idf_write_failed.append(fid)
                self.bldg_containers[fid].set_error()

        if idf_write_failed:
            self.logger.error(f"writing idf failed for bldg fids {idf_write_failed}")
            self.failed_fids.update(idf_write_failed)

        self._storage.save_weather_file_mapping(self.weather_files)

        return idf_write_failed

    def run_simulations(self) -> List[int]:
        """
        Run EnergyPlus simulation

        :param bldg_fids_to_create_idf_for: gis fids of buildings for which to run the simulation; if None simulation is run for all created IDF's
        :return: fid's for which EnergyPlus simulation failed
        """
        assert self.is_ready_to_run_sim(), "please run create_IDFs before calling run_simulation"

        # clear any results
        for container in self.bldg_containers.values():
            container.clear_results()

        bldg_gis_ids_to_simulate = list(self.idf_pathes.keys())
        expected_output_folders = self._storage.get_eplus_output_pathes(bldg_gis_ids_to_simulate)

        # avoid loading config from disk for each simulation, thus load here and pass on
        config_eplus = cesarp.eplus_adapter.eplus_sim_runner.get_config(self._custom_config)
        job_res_dict = {
            fid: self._get_worker_pool().apply_async(
                processing_steps.run_simulation_no_exception,
                (self.idf_pathes[fid], self.weather_files[fid], expected_output_folders[fid], config_eplus),
            )
            for fid in bldg_gis_ids_to_simulate
        }
        res_tuples_dict = {fid: res.get() for fid, res in job_res_dict.items()}
        eplus_run_timelog = {}
        fids_sim_failed = []
        fids_sim_successful = []
        for fid, (successful, sim_time) in res_tuples_dict.items():
            eplus_run_timelog[fid] = sim_time
            if successful:
                fids_sim_successful.append(fid)
                self.output_folders[fid] = expected_output_folders[fid]
            else:
                fids_sim_failed.append(fid)
                self.bldg_containers[fid].set_error()

        if fids_sim_failed:
            self.logger.error(f"simulation failed for fids {fids_sim_failed}")
            self.failed_fids.update(fids_sim_failed)

        self._storage.save_eplus_sim_time_log(eplus_run_timelog)
        self._storage.combine_eplus_error_files(fids_sim_failed, fids_sim_successful, EPLUS_ERROR_FILE_NAME)
        return fids_sim_failed

    def process_results(self, bldg_fids_to_use: Optional[Iterable[Any]] = None) -> None:
        """
        Process EnergyPlus output of all the simulations run and collect all annual results.
        Make sure you add the all parameters you want to be in the summary with frequency ANNUAL in your YML config according to cesarp.eplus_adapter.default_config.yml

        :param bldg_fids_to_create_idf_for: gis fids of buildings which to integrate in the summary; if None results for all simulations run are collected
        :param save_summary: if True, the summary table is saved to a CSVY file in the base folder, filename according to configuration
        :return: results table, one row per building and a column per parameter. Mutltiindex column header consisting of parameter name and unit.
        """
        if not bldg_fids_to_use:
            bldg_fids_to_use = list(self.output_folders.keys())

        worker_pool = self._get_worker_pool()
        fid_batches = define_fid_batches(bldg_fids_to_use, worker_pool._processes)

        job_res_list = []
        for fid_batch in fid_batches:
            inputs_for_batch = {}
            for fid in fid_batch:
                this_bldg_model: BuildingModel = self.bldg_containers[fid].get_bldg_model()
                inputs_for_batch[fid] = (
                    self.output_folders[fid],
                    this_bldg_model.bldg_construction.installation_characteristics.e_carrier_heating,
                    this_bldg_model.bldg_construction.installation_characteristics.e_carrier_dhw,
                    this_bldg_model.site.simulation_year,
                )

            job_res = self._get_worker_pool().apply_async(
                processing_steps._collect_result_summary_batch,
                (inputs_for_batch, self._mgr_config["DO_CALC_OP_EMISSIONS_AND_COSTS"], self._custom_config),
                error_callback=processing_steps.log_error,
            )
            job_res_list.append(job_res)

        # get back worker result
        res_list = [res.get() for res in job_res_list]
        all_eplus_err_levels: Dict[int, EnergyDemandSimulationResults] = {}
        all_demand_res: Dict[int, EnergyDemandSimulationResults] = {}
        all_op_emission_cost_res: Dict[int, OperationalEmissionsAndCostsResult] = {}
        for (err_levels, demands, op_emissions_costs) in res_list:
            all_eplus_err_levels.update(err_levels)
            all_demand_res.update(demands)
            all_op_emission_cost_res.update(op_emissions_costs)

        # make sure no old result entries are present, should be cleared before running the simulations, but to make sure
        map(lambda x: x.clear_results(), self.bldg_containers.values())

        # fill result to containers
        for fid, eplus_err_level in all_eplus_err_levels.items():
            self.bldg_containers[fid].set_eplus_error_level(eplus_err_level)

        for fid, demand_res in all_demand_res.items():
            self.bldg_containers[fid].set_energy_demand_sim_res(demand_res)

        for fid, op_emissions_cost in all_op_emission_cost_res.items():
            self.bldg_containers[fid].set_op_cost_and_emission(op_emissions_cost)

        return None

    def get_all_results_summary(self):
        all_eplus_err_levels = {fid: cont.get_eplus_error_level().name if cont.get_eplus_error_level() else "" for fid, cont in self.bldg_containers.items()}
        all_eplus_err_df = ResultProcessor.convert_eplus_error_level_to_df(all_eplus_err_levels)

        all_demand_res = {fid: cont.get_energy_demand_sim_res() for fid, cont in self.bldg_containers.items()}
        demand_res_df = ResultProcessor.convert_demand_results_to_df(all_demand_res, self._unit_reg)

        all_results = pd.concat([all_eplus_err_df, demand_res_df], axis="columns")

        all_op_em_cost_res = {fid: cont.get_op_cost_and_emission() for fid, cont in self.bldg_containers.items() if cont.has_op_cost_and_emission_result()}

        if self._mgr_config["DO_CALC_OP_EMISSIONS_AND_COSTS"] and all_op_em_cost_res:
            all_results = pd.concat(
                [
                    all_results,
                    ResultProcessor.convert_emissions_to_df(all_op_em_cost_res, self._unit_reg),
                    ResultProcessor.convert_fuel_cost_to_df(all_op_em_cost_res, self._unit_reg),
                ],
                axis="columns",
            )

        return all_results

    def collect_custom_results(self, result_keys: Sequence, results_frequency: ResultsFrequency) -> pd.DataFrame:
        """
        Process EnergyPlus output of all the simulated buildings. You can specify which parameters should be collected and the frequency (e.g. ANNUAL, HOURLY).
        If you need to get two parameters and they have different frequencies, you need to call the method twice.
        Make sure you add the result parameters you want to be able to collect in the correct frequency in your YML config according to cesarp.eplus_adapter.default_config.yml

        :param result_keys: list of EnergyPlus result parameters which should be collected
        :param results_frequency: frequency of the result parameter
        :return: pandas DataFrame, index/rows beeing the time index, e.g. hour if frequency is HOURLY, columns are a multiindex consisting of building fid, parameter name, unit
        """
        worker_pool = self._get_worker_pool()
        fid_batches = define_fid_batches(list(self.output_folders.keys()), worker_pool._processes)
        job_res_list = [
            self._get_worker_pool().apply_async(
                cesarp.eplus_adapter.eplus_eso_results_handling.collect_multi_params_for_site,
                (
                    {fid: output_folder for fid, output_folder in self.output_folders.items() if fid in fid_batch},
                    result_keys,
                    results_frequency,
                ),
                error_callback=processing_steps.log_error,
            )
            for fid_batch in fid_batches
        ]

        per_batch_summary = [res.get() for res in job_res_list]
        all_results = pd.concat(per_batch_summary, axis=0, sort=False)
        return all_results

    def save_to_zip(self, main_script_path, include_bldg_models=True, include_idfs=False, include_eplus_output=False, include_src_pck=True, save_folder_path=None) -> str:
        """
        saving all project input files and information needed for cesar-p installation so that the project can be transfered to another computer and results can be re-produced.
        if run from a cesar-p development installation, thus poetry is available, local source files are packed into a pip-installable wheel package.

        :param main_script_path: path to main script used to run CESAR-P for current project. Script will be included in the ZIP.
        :type main_script_path: str
        :param include_bldg_models: internal ceasar-p representation of each building saved as json, can be re-loaded into python objects for later analysis of modeled building parameters or to re-create IDF files, defaults to True
        :type include_bldg_models: bool, optional
        :param include_idfs: generated IDF files are saved, defaults to False
        :type include_idfs: bool, optional
        :param include_eplus_output: include energy plus raw output files - attention, that might be a lot of data!, defaults to False
        :type include_eplus_output: bool, optional
        :param include_src_pck: include source code as wheel package (only possible if CESAR-P is installed with poetry)
        :type include_src_pck: bool, optional
        :param save_folder_path: path to save zip file to, if None zip is saved to project basefolder
        :type save_folder_path: str, optional
        :return: path of saved zip file
        """
        projSaver = ProjectSaver(
            zip_file_path=self._storage.get_ZIP_filepath(save_folder_path),
            main_config=self._custom_config,
            main_script_path=main_script_path,
            file_storage_handler=self._storage,
            bldg_containers=self.bldg_containers,
        )
        return projSaver.create_zip_file(include_bldg_models, include_idfs, include_eplus_output, include_src_pck)

    def _get_fids_having_bldg_model(self) -> List[int]:
        """returns list of building fids for which a building model exists"""
        bldg_model_exists = [fid for fid, bldg_container in self.bldg_containers.items() if bldg_container.has_bldg_model()]
        return bldg_model_exists

    def __get_metadata_full_run(self):
        return cesarp.common.DatasetMetadata.DatasetMetadata(
            source=f"energy plus simulation results EnergyPlus Version {cesarp.eplus_adapter.eplus_sim_runner.get_eplus_version(custom_config=self._custom_config)} "
            f"and calculated emissions and fuel costs with cesar-p "
            f"using emisson and cost data input files listed in the configuration entries for ENERGY_STRATEGY",
            description="idf generation, simualtion run and results aggregation with cesar-p. See configuration settings dumped above for top level and custom settings",
            config_entries={
                "CUSTOM_CONFIG": self._custom_config,
                "MANAGER_CONFIG": self._mgr_config,
                "ENERGY_STRATEGY_CONFIG": cesarp.common.config_loader.load_config_for_package(
                    cesarp.energy_strategy._default_config_file, "cesarp.energy_strategy", self._custom_config
                ),
            },
        )

    def _get_worker_pool(self):
        if self._worker_pool is None:
            if self.delete_old_logs:
                delete_old_logs()
            mplogger = multiprocessing.log_to_stderr()
            mplogger.setLevel(logging.WARNING)  # set to INFO if you want to see details about process management
            processors = self._mgr_config["NR_OF_PARALLEL_WORKERS"]
            if processors == -1:
                processors = max(1, round(multiprocessing.cpu_count() / 2))
            self.logger.info(f"creating worker pool with {processors} processors")
            self._worker_pool = multiprocessing.Pool(processors, initializer=init_worker)
            atexit.register(self._worker_pool.close)

        return self._worker_pool

    def _get_managed_aux_fh(self):
        if self._mgr_config["COPY_PROFILES"]["ACTIVE"]:
            manager = MyManager()
            manager.start()
            aux_fh = manager.AuxFilesHandler()  # type: ignore
            aux_fh.set_destination(self._storage.idf_output_dir, self._storage.idf_aux_files_folder_name)
        else:
            aux_fh = None
        return aux_fh

    def _get_lock(self):
        manager = SyncManager()
        manager.start()
        sia_params_gen_lock = manager.Lock()
        return sia_params_gen_lock

    @classmethod
    def new_manager_from_template(cls, base_scenario_manager, new_manager_basepath):
        """
        Create new Simulation manager, copy configuration and building models from existing SimulationManager

        :param base_scenario_manager: SimulationManager to be used as a template for the newly created instance
        :param new_manager_basepath: basepath folder for the new SimulationManager
        :return: new instance of SimulationManager class
        """
        new_manager = cls(
            new_manager_basepath,
            base_scenario_manager._custom_config,
            base_scenario_manager._unit_reg,
            base_scenario_manager._fids_to_use,
        )
        new_manager.bldg_containers = {fid: BuildingContainer() for fid in base_scenario_manager.bldg_containers.keys()}
        for fid, container in new_manager.bldg_containers.items():
            container.set_bldg_model(copy.deepcopy(base_scenario_manager.bldg_containers[fid].get_bldg_model()))
            try:
                container.set_retrofit_log(copy.deepcopy(base_scenario_manager.bldg_containers[fid].get_retrofit_log()))
            except KeyError:
                pass

        return new_manager


def init_worker():
    init_log_to_file()
    cesarp.common.init_unit_registry()


def init_log_to_file():
    log_dir = f"{get_timestamp()}-cesarp-logs"
    os.makedirs(log_dir, exist_ok=True)  # only first worker initialization needs to create directory
    file_handler = logging.FileHandler(f"{log_dir}/cesarp-worker-{multiprocessing.current_process().name}.log")
    formatter = logging.Formatter("%(asctime)s %(processName)-10s %(name)s %(levelname)-8s %(message)s")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    root = logging.getLogger()
    root.addHandler(file_handler)
    root.setLevel(logging.DEBUG)
    cl = logging.getLogger("cesarp")
    cl.setLevel(logging.INFO)
    cl.propagate = False
    cl.addHandler(file_handler)


def delete_old_logs():
    for dir_entry in glob.glob("*-cesarp-logs", recursive=False):
        shutil.rmtree(dir_entry, ignore_errors=True)
