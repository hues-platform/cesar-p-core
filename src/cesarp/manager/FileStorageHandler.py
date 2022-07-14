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
import os
import logging
from pathlib import Path, PurePath
from typing import Dict, Any, List, Sequence, Union, Optional
from shutil import copyfileobj
import pandas as pd
from datetime import datetime

import cesarp.common
from cesarp.common.DatasetMetadata import DatasetMetadata
import cesarp.manager.json_pickling
from cesarp.manager import _default_config_file
from cesarp.manager.BuildingContainer import BuildingContainer
from cesarp.model.BuildingModel import BuildingModel


def get_timestamp():
    now = datetime.now()
    return now.strftime("%Y%m%d_%H%M")


class FileStorageHandler:
    """
    This class is responsible for reading and writing intermediate and final result files to disk.
    Further it assembles pathes for idf files and EnergyPlus output. Just anything that's written
    to disk should get at least the path over this FileStorageHandler.
    Directory structure is:

    base_directory:
    - eplus_output
    - idfs
    - bldg_containers

    You can change the names and to a certain degree also the structure by changing the configuration.

    idfs [name from cfg: IDF_FOLDER_REL]
    - profiles - folder holding operational profiles used by any of the idf's, only if COPY_PROFILES is set to true in config
    - fid_XXX.idf - idf file for each building
    - weather_files_mapped.csvy - assignment of weather file to use for each of the buildings [cfg: WEATHER_FILES_MAPPED_REL]

    eplus_output [name from cfg: OUTPUT_FOLDER_REL]

    - contains a directory per building, that directory contains the RAW EnergyPlus simulation output

    bldg_containers

    - contains a json file per building with serialized representation of that building (bldg model, results incl
      op costs and emission) main usage is to reload a previously simulated site to python or to derive a new
      simulation scenario from existing building models
    """

    def __init__(self, base_output_path, custom_config: Optional[Dict[str, Any]], reloading=False):
        """
        :param base_output_path: path to main folder to store files for that simulation run
        :param custom_config: custom config entries
        :param reloading: pass True if project already exists and you want to reload, if False init checks that
                          folders used for per-building files are empty
        """
        self.logger = logging.getLogger(__name__)
        self.base_output_path = base_output_path
        self._mgr_config = cesarp.common.config_loader.load_config_for_package(_default_config_file, __package__, custom_config)

        self.base_output_path = base_output_path
        os.makedirs(self.base_output_path, exist_ok=True)
        self.container_save_path = Path(self.base_output_path) / Path(self._mgr_config["BLDG_CONTAINERS_FOLDER_REL"])
        os.makedirs(self.container_save_path, exist_ok=True)
        self.idf_output_dir = self.base_output_path / Path(self._mgr_config["IDF_FOLDER_REL"])
        os.makedirs(self.idf_output_dir, exist_ok=True)
        self.weather_files_mapped_save_path = self.idf_output_dir / Path(self._mgr_config["WEATHER_FILES_MAPPED_REL"])
        self.eplus_output_dir = self.base_output_path / Path(self._mgr_config["OUTPUT_FOLDER_REL"])
        os.makedirs(self.eplus_output_dir, exist_ok=True)
        if not reloading:
            self._assert_no_files_in_dir(self.container_save_path)
            self._assert_no_files_in_dir(self.idf_output_dir)
            self._assert_no_files_in_dir(self.eplus_output_dir)

    @property
    def idf_aux_files_folder_name(self):
        return self._mgr_config["COPY_PROFILES"]["PROFILES_FOLDER_NAME_REL"]

    def _assert_no_files_in_dir(self, path) -> None:
        assert not list(filter(os.path.isfile, os.listdir(path))), f"{path} contains files! - Please delete and run again."

    def load_existing_bldg_containers(self) -> Dict[int, BuildingContainer]:
        """
        Try to load building containers.
        Expected path were the building containers are stored is specified in the configuration.
        It's not checked wheter the loaded containers contain all properties or for example only the building models...

        :return: dict with fid and its building container object, empty dict if building containers are not available on disk or could not be loaded
        """

        def fail_safe_read_from_disk(container_file_path):
            try:
                cont = cesarp.manager.json_pickling.read_bldg_container_from_disk(container_file_path)
                if cont.has_bldg_model():
                    FileStorageHandler.convert_rel_to_abs_pathes_in_model(cont.get_bldg_model(), self.container_save_path)
                return cont
            except Exception as ex:
                self.logger.error(f"Could not load builing model from {container_file_path}. Skip this file.")
                self.logger.exception(ex)
            return None

        if os.path.exists(self.container_save_path):
            containers_save_pathes = cesarp.common.filehandling.scan_directory(self.container_save_path, self._mgr_config["BLDG_CONTAINER_FILENAME_REL"])
            bldg_containers = {fid: fail_safe_read_from_disk(container_path) for fid, container_path in containers_save_pathes.items()}
            self.logger.info(f"loaded {len(bldg_containers)} building containers from {self.container_save_path}")

            return bldg_containers

        return {}

    def load_existing_idfs(self) -> Dict[int, Any]:
        """
        Try to load IDF files and weather assignment. Expected path is specified in the configuration.

        :return: dict with fid and it's IDF path, empty dict if no IDFs available
        """
        idf_pathes: Dict[int, Any] = {}
        if os.path.exists(self.idf_output_dir):
            idf_pathes = cesarp.common.filehandling.scan_directory(self.idf_output_dir, self._mgr_config["IDF_FILENAME_REL"])
            self.logger.info(f"loaded {len(idf_pathes)} idf files from folder {self.idf_output_dir}")

        return idf_pathes

    def load_existing_weather_mapping(self) -> Dict[int, Any]:
        """
        Loads weather file assignment from mapping file.
        In case you want to reload a project from a ZIP file saved with ProjectSaver the weather file pathes will not be valid, as they are not stored as ZIP relative pathes (it's not easy to accomplish that).
        Thus, when the pathes in the mapping file are not valid, but the project is using a single site, weather file as set in configuration is assigned for each building instead if the name of the weather file in the mapping file matches the configured weather file name.
        Relative pathes in the mapping file are resolved to absolute pathes relative to location of weather files mapping file.

        :return: dict where key is the fid and value the weather file path; dict is empty if loading weather files was not possible
        :rtype: Dict[int, Any]
        """
        weather_files = self._read_weather_file_mapping()
        mapping_file_folder = os.path.dirname(self.weather_files_mapped_save_path)
        if weather_files:
            weather_files_abs = {fid: (wf if os.path.exists(wf) else os.path.normpath(mapping_file_folder / Path(wf))) for fid, wf in weather_files.items()}
            if all(os.path.exists(wf) for wf in weather_files_abs.values()):
                self.logger.info(f"loaded weather file assignment from  {self.weather_files_mapped_save_path}")
                return weather_files_abs
            elif len(set(weather_files.values())) == 1:  # check if all entreis are the same
                assigned_path = next(iter(weather_files.values()))
                if self._mgr_config["SINGLE_SITE"]["ACTIVE"]:
                    default_weather_file = self._mgr_config["SINGLE_SITE"]["WEATHER_FILE"]
                    if Path(assigned_path).name == Path(default_weather_file).name and os.path.exists(default_weather_file):
                        self.logger.warning(
                            f"Weather file path in {self.weather_files_mapped_save_path} not valid. Weather file from config {default_weather_file} is used for all buildings."
                        )
                        return {fid: default_weather_file for fid in weather_files.keys()}
            else:
                self.logger.error(f"Error during loading of weather file mappings from {self.weather_files_mapped_save_path}. Referenced weather files not found.")
        self.logger.error(f"Error during loading of weather file mappings from {self.weather_files_mapped_save_path}. File does not exist or is empty.")
        self.logger.error("No weather files assigned to buildings, thus running E+ simulation is not possible for loaded project.")
        return {}

    def _read_weather_file_mapping(self) -> Dict[int, Any]:
        """
        to load weather files for use in SimulationManager use load_existing_weather_mapping()
        """
        if os.path.exists(self.weather_files_mapped_save_path):
            return cesarp.common.csv_reader.read_csvy(
                self.weather_files_mapped_save_path,
                ["bldg_fid", "weather_file"],
                {"bldg_fid": "bldg_fid", "weather_file": "weather_file"},
                index_column_name="bldg_fid",
            )["weather_file"].to_dict()
        return {}

    def load_existing_result_folders(self) -> Dict[int, Any]:
        """
        Try to load existing EnergyPlus simulation results. Expected path is specified in the configuration.
        :return: dict with fid - result folder pairs, empty dict if result folder does not exist or is empty
        """
        output_folders: Dict[int, Any] = {}
        output_dir = self.base_output_path / Path(self._mgr_config["OUTPUT_FOLDER_REL"])
        if os.path.exists(output_dir):
            output_folders = cesarp.common.filehandling.scan_directory(output_dir, self._mgr_config["BATCH_OUT_DIR_TEMPLATE_REL"])
            self.logger.info(f"found {len(output_folders)} E+ result folders in {output_dir}")
        return output_folders

    def get_result_summary_filepath(self):
        sum_outp_conf = self._mgr_config["SUMMARY_OUTPUT"]
        return self.base_output_path / Path(sum_outp_conf["PATH_REL"])

    def get_ZIP_filepath(self, save_folder_path=None):
        if not save_folder_path:
            save_folder_path = self.base_output_path
        zip_filename = get_timestamp() + "_" + PurePath(self.base_output_path).name + ".zip"
        return save_folder_path / Path(zip_filename)

    def save_result_summary(self, summary_res: pd.DataFrame, metadata: DatasetMetadata):
        sum_outp_conf = self._mgr_config["SUMMARY_OUTPUT"]
        sum_file_path = self.get_result_summary_filepath()
        header_data = {cesarp.common.csv_writer._KEY_SOURCE: metadata.get_as_dict()}
        cesarp.common.csv_writer.write_csv_with_header(
            header_data,
            summary_res,
            sum_file_path,
            sum_outp_conf["CSV_SEPARATOR"],
            float_format=sum_outp_conf["CSV_FLOAT_FORMAT"],
            separate_metadata=self._mgr_config["SEPARATE_METADATA"],
        )
        self.logger.info(f"simulation summary file written to {sum_file_path}")
        return sum_file_path

    def get_bldg_infos_used_filepath(self):
        return self.base_output_path / Path(self._mgr_config["BLDG_INFO_REPORT_FILENAME_REL"])

    def save_bldg_infos_used(self, all_per_bldg_info_used):
        cesarp.common.csv_writer.write_csv_with_header(
            {"DESCRIPTION": "The data listed here was used during creation of the building models for this site."},
            all_per_bldg_info_used,
            self.get_bldg_infos_used_filepath(),
            separate_metadata=self._mgr_config["SEPARATE_METADATA"],
        )

    def save_weather_file_mapping(self, weather_file_mapping: Dict[int, str]):
        cesarp.common.csv_writer.write_csv_with_header(
            {"DESCRIPTION": "Intermediate Cesar storage, not intended for reporting"},
            pd.DataFrame(
                weather_file_mapping.values(),
                index=pd.Index(weather_file_mapping.keys(), name="bldg_fid"),
                columns=["weather_file"],
            ),
            self.weather_files_mapped_save_path,
        )

    def create_idf_output_pathes(self, fids: List[int]):
        return {fid: str(self.idf_output_dir / Path(self._mgr_config["IDF_FILENAME_REL"].format(fid))) for fid in fids}

    def get_eplus_output_pathes(self, fids: List[int]):
        return {fid: self.eplus_output_dir / Path(self._mgr_config["BATCH_OUT_DIR_TEMPLATE_REL"].format(fid)) for fid in fids}

    def save_bldg_containers(self, bldg_containers_to_save) -> Sequence[int]:
        """
        Save all building containters to disk.

        :return: fid's for which the building model could not be saved.
        """
        assert bldg_containers_to_save, "nothing to safe, building containers empty"

        self.logger.info(f"saving building containers to {self.container_save_path}")
        save_failed = []
        for fid, container in bldg_containers_to_save.items():
            try:
                self.save_single_bldg_container(fid, container, self.container_save_path)
            except Exception as ex:
                self.logger.error(f"Could not save builing containter for {fid}. Skip this building for saving and continue...")
                self.logger.exception(ex)
                save_failed.append(fid)

        return save_failed

    def save_single_bldg_container(self, fid: int, bldg_container: BuildingContainer, save_folder_path: Union[str, Path]) -> str:
        filename = self._mgr_config["BLDG_CONTAINER_FILENAME_REL"].format(fid)
        filepath = str(save_folder_path / Path(filename))
        self.logger.debug(f"save building conteiner for {fid} to {filepath}")
        cesarp.manager.json_pickling.save_to_disk(bldg_container, filepath)
        return filepath

    def save_eplus_sim_time_log(self, eplus_run_timelog):
        pd.DataFrame(eplus_run_timelog.items(), columns=["idf path", "simulation time in sec"]).to_csv(self.base_output_path / Path("eplus_simulation_timelog.csv"))

    @staticmethod
    def convert_rel_to_abs_pathes_in_model(model: BuildingModel, base_dir: str) -> None:
        """
        Change all file references which are relative to absolute pathes.
        This method is the counterpart for cesarp.manager.ProjectSaver::_convert_bldg_model_to_rel_pathes

        :param base_dir: root directory to use for resolving relative pathes
        :type base_dir: str
        """

        def to_abs_path(in_path: Union[Path, str]) -> str:
            # check if it really relative path or it is already absolute
            if os.path.isabs(in_path):
                return str(in_path)
            else:
                abs_path = base_dir / Path(in_path)
                if not os.path.exists(abs_path):
                    raise Exception(f"Invalid ressource in building model for fid {model.fid}, relative path is {in_path}, which can not be found at absolute location {abs_path}")
                return str(os.path.normpath(abs_path))

        def shed_to_abs_path(schedule) -> None:
            if isinstance(schedule, cesarp.common.ScheduleFile):
                schedule.schedule_file = to_abs_path(schedule.schedule_file)

        for (floor_nrs, bldg_op) in model.bldg_operation_mapping.get_operation_assignments():
            shed_to_abs_path(bldg_op.occupancy.occupancy_fraction_schedule)
            shed_to_abs_path(bldg_op.occupancy.activity_schedule)
            shed_to_abs_path(bldg_op.electric_appliances.fraction_schedule)
            shed_to_abs_path(bldg_op.lighting.fraction_schedule)
            shed_to_abs_path(bldg_op.dhw.fraction_schedule)
            shed_to_abs_path(bldg_op.hvac.heating_setpoint_schedule)
            shed_to_abs_path(bldg_op.hvac.cooling_setpoint_schedule)
            shed_to_abs_path(bldg_op.hvac.ventilation_fraction_schedule)

        shed_to_abs_path(model.bldg_construction.infiltration_profile)

        model.site.weather_file_path = to_abs_path(model.site.weather_file_path)

    def combine_eplus_error_files(self, failed_fids: List[int], successful_fids: List[int], eplus_error_file_name: str):
        """
        :param failed_fids: list of fids for which simulation failed and error files should be collected
        :param successful_fids: list of fids for which simulation was successful and error files should be collected
        :param eplus_error_file_name: full path to file to which to write all the log files
        """
        summary_file_path = self.base_output_path / Path(self._mgr_config["EPLUS_ERROR_SUMMARY_REL"])
        with open(summary_file_path, "w") as sf:
            sf.writelines("For following FIDs the EnergyPlus simulation was not successful:\n")
            [sf.writelines(f"{ffid}\n") for ffid in failed_fids]

        eplus_error_files = [ep_out_path / Path(eplus_error_file_name) for ep_out_path in self.get_eplus_output_pathes(failed_fids + successful_fids).values()]
        self._combine_files(files_to_append=eplus_error_files, main_file=summary_file_path, append_to_main_file=True)

    @staticmethod
    def _combine_files(files_to_append: List[str], main_file: str, append_to_main_file=False):
        file_mod = "wb"
        if append_to_main_file:
            file_mod = "ab"
        with open(main_file, file_mod) as file_to_append_to:
            for filename_to_be_appended in files_to_append:
                file_sep_lines = f"\n=======\n{filename_to_be_appended}\n=======\n\n"
                file_to_append_to.write(file_sep_lines.encode("utf-8"))
                with open(filename_to_be_appended, "rb") as to_be_appended:
                    copyfileobj(to_be_appended, file_to_append_to, 1024)
