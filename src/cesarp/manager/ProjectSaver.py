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
from typing import Dict, Any, Optional, Union
import os
import shutil
import glob
import logging
from pathlib import Path, PurePath
import subprocess
from zipfile import ZipFile
import copy
from importlib.metadata import version
import sys
import requests

import cesarp.common.version_info
from cesarp.manager.FileStorageHandler import FileStorageHandler
from cesarp.manager.BuildingContainer import BuildingContainer
from cesarp.model.BuildingModel import BuildingModel
from cesarp.model.Site import Site
from cesarp.common import version_info
from cesarp.eplus_adapter.eplus_sim_runner import get_eplus_executable, get_idd_path, get_eplus_version
import cesarp.common
from cesarp.common.CesarpException import CesarpException
from cesarp.common.config_loader import save_config_to_file
from cesarp.graphdb_access import _default_config_file as graph_db_access_default_config


def add_folder_to_zip(zip_file: ZipFile, folder: Union[str, Path], sub_dir_in_zip: str = "") -> Dict[str, str]:
    """
    add folder and subelements to zip

    :param zip_file: [description]
    :type zip_file: ZipFile
    :param folder: [description]
    :type folder: Union[str, Path]
    :param sub_dir_in_zip: [description], defaults to ""
    :type sub_dir_in_zip: str, optional
    :return: dictionary with all added items, key is the original path, value the path in the zip
    :rtype: Dict[str,str]
    """
    added_items: Dict[str, str] = {}
    folder_to_add_name = PurePath(folder).name
    base_folder_in_zip = str(sub_dir_in_zip / Path(folder_to_add_name))
    for file in os.listdir(folder):
        full_path = os.path.join(folder, file)
        if os.path.isfile(full_path):
            full_path_in_zip = str(base_folder_in_zip / Path(file))
            zip_file.write(full_path, full_path_in_zip)
            added_items[full_path] = full_path_in_zip
        elif os.path.isdir(full_path):
            added_items.update(add_folder_to_zip(zip_file=zip_file, folder=full_path, sub_dir_in_zip=base_folder_in_zip))

    added_items[str(folder)] = base_folder_in_zip
    return added_items


def add_file_to_zip(zip_file: ZipFile, filepath, subdir="", filename_in_zip=None) -> str:
    if not filename_in_zip:
        filename_in_zip = os.path.basename(filepath)
    full_path_in_zip = str(subdir / Path(filename_in_zip))
    zip_file.write(filepath, full_path_in_zip)
    return full_path_in_zip


class ProjectSaver:
    """
    Save a simulation as a zip file. Either to transfer to another PC or to save for storage.
    You have different options what should be included, see options of *create_zip_file()*.
    In general, the aim is that in the ZIP you have everything included necessary to re-run the
    simulation. To do so, create a instance of this class and then call *create_zip_file()*.

    If you use the SimulationManager, see its *save_to_zip()* method, which calls this ProjectSaver and initializes everything as needed.
    """

    GIT_STATUS_FILENAME = "git_status_extended.txt"
    PROJ_RESSOURCES_FOLDER = "project_ressources"
    CESARP_OUTPUTS_FOLDER = "cesarp_output"
    RUNTIME_ENV_FOLDER = "runtime_environment"
    README_FILENAME = "README.md"
    MAIN_CONFIG_FILENAME = "main_config.yml"
    CONSTRUCTION_DATA_FILENAME = "construction_and_retrofit_data.ttl"

    def __init__(
        self,
        zip_file_path: Union[Path, str],
        main_config: Dict[str, Any],
        main_script_path: str,
        file_storage_handler: FileStorageHandler,
        temp_dir: Optional[Path] = None,
        bldg_containers: Dict[int, BuildingContainer] = None,
    ):
        """
        :param zip_file_path: full path including file name and extension to save your zip to
        :type zip_file_path: Union[Path, str]
        :param main_config: main/custom config used in that project
        :type main_config: Dict[str, Any]
        :param main_script_path: path to main script used to run CESAR-P for current project. Script will be included in the ZIP.
        :type main_script_path: str
        :param file_storage_handler: file storage handler instance of the project. needed to know where which files are located.
        :type file_storage_handler: FileStorageHandler
        :param temp_dir: temporary directory where to store contents to be added to ZIP, such as the README, if None system TEMP resp TMPDIR folder will be used, defaults to None
        :type temp_dir: Optional[Path], optional
        :param bldg_containers: if serialized *BuildingContainer*, pass the *BuildingContainer* objects here, defaults to None
        :type bldg_containers: Dict[int, BuildingContainer], optional
        :raises Exception: CesarpException if environment variable TEMP nor TMPDIR is defined and no temp_dir is passed
        """
        if not temp_dir:
            sys_tmp_dir = os.environ.get("TMPDIR") or os.environ.get("TEMP")
            if not sys_tmp_dir:
                raise CesarpException("Please specify destination_dir_tmp as parameter for ProjectSaver() as neither TEMP nor TMPDIR was found in environment.")
            temp_dir = sys_tmp_dir / Path("cesar-p-saveproj")

        shutil.rmtree(temp_dir, ignore_errors=True)
        os.makedirs(temp_dir)
        self._temp_dir = temp_dir
        self._zip_file_path = zip_file_path
        self._main_config = main_config
        self._main_script_path = main_script_path
        self._file_storage_handler: FileStorageHandler = file_storage_handler
        self._bldg_containers: Optional[Dict[int, BuildingContainer]] = bldg_containers
        self._src_wheel_zip_rel_path = None
        self._track_zipped_items: Dict[str, str] = {}
        self._logger = logging.getLogger(__name__)

    def create_zip_file(self, include_bldg_models, include_idfs, include_eplus_output, include_src_pck) -> str:
        """
        saving all project input files and information needed for cesar-p installation so that the project can be transfered to another computer and results can be re-produced.
        if run from a cesar-p development installation, thus poetry is available, local source files are packed into a pip-installable wheel package.

        :param include_bldg_models: internal ceasar-p representation of each building saved as json, can be re-loaded into python objects for later analysis of modeled building parameters or to re-create IDF files, defaults to True
        :type include_bldg_models: bool, optional
        :param include_idfs: generated IDF files are saved, defaults to False
        :type include_idfs: bool, optional
        :param include_eplus_output: include energy plus raw output files - attention, that might be a lot of data!, defaults to False
        :type include_eplus_output: bool, optional
        :param include_src_pck: include source code as wheel package (only possible if CESAR-P is installed with poetry)
        :type include_src_pck: bool, optional
        :return: path of saved zip file
        """
        env_files = self.create_environment_files()
        env_files_dir = self.RUNTIME_ENV_FOLDER
        with ZipFile(self._zip_file_path, "w") as thezip:
            for env_file in env_files:
                thezip.write(env_file, env_files_dir + "/" + os.path.basename(env_file))
            if include_src_pck:
                src_wheel_tmp_file = self.create_source_wheel()
                if src_wheel_tmp_file:
                    self._src_wheel_zip_rel_path = env_files_dir + "/" + os.path.basename(src_wheel_tmp_file)
                    thezip.write(src_wheel_tmp_file, self._src_wheel_zip_rel_path)
            self.add_project_input_files(thezip)
            self.add_cesarp_output_files(thezip, include_bldg_models, include_idfs, include_eplus_output)
            add_file_to_zip(thezip, self._main_script_path)
            add_file_to_zip(thezip, self.create_readme(include_bldg_models, include_idfs, include_eplus_output))
            self.add_construction_data_ttl_file(thezip)

        return str(self._zip_file_path)

    def create_readme(self, include_bldg_models, include_idfs, include_eplus_output):
        tmp_readme = self._temp_dir / Path(self.README_FILENAME)
        with open(tmp_readme, "w") as fd:
            fd.writelines("README\n")
            fd.writelines("==========\n")
            self.write_zip_description(fd, include_bldg_models, include_idfs, include_eplus_output)
            self.write_installation_instructions(fd)
        return tmp_readme

    def add_cesarp_output_files(self, the_zip: ZipFile, include_bldg_models, include_idfs, include_eplus_output):
        cesarp_out_dir = self.CESARP_OUTPUTS_FOLDER
        add_file_to_zip(the_zip, self._file_storage_handler.get_result_summary_filepath(), cesarp_out_dir)
        add_file_to_zip(the_zip, self._file_storage_handler.get_bldg_infos_used_filepath(), cesarp_out_dir)

        if include_bldg_models and self._bldg_containers:
            self.add_building_containers(the_zip, cesarp_out_dir)
        if include_idfs:
            # not that weather mapping file is included in idf output dir
            self.check_weather_files()
            add_folder_to_zip(the_zip, self._file_storage_handler.idf_output_dir, cesarp_out_dir)
        if include_eplus_output:
            add_folder_to_zip(the_zip, self._file_storage_handler.eplus_output_dir, cesarp_out_dir)

    def check_weather_files(self):
        """
        Checks whether weather file referenced by the mapping file is included in the ZIP.
        This will only be the case for single site with same weather file for all buildings.
        In case of mutliple weather files it is up to the user to include those in the ZIP package.
        See cesarp.manager.FileStorageHandler::load_existing_weather_mapping to see how importing of the weather file
        assignment is handeld.

        Dev note: Adding all the weather files referenced in the mapping would be possible, but adapting the weather mapping file
        involves some more work as that file is added to the zip as part of the IDF files folder. Replacing an existing file
        in the ZIP is not possible, thus special handling for that file to be able to change it before including in the ZIP
        would be needed...
        """
        weather_files = self._file_storage_handler._read_weather_file_mapping()
        if not weather_files:
            self._logger.warning("Weather file mapping file is missing.")
        elif (
            len(set(weather_files.values())) != 1  # all buildings have same weather file
            or next(iter(weather_files.values())) not in self._track_zipped_items.keys()  # weather file was added to project ressources already
        ):
            self._logger.warning(
                f"Not all weather files used in your project and listed in the weather files mapping file {self._file_storage_handler.weather_files_mapped_save_path} are included in the ZIP."
            )

    def add_building_containers(self, the_zip, cesarp_out_dir):
        zip_cont_folder_path = cesarp_out_dir / Path(os.path.basename(self._file_storage_handler.container_save_path))
        for fid, bldg_cont in self._bldg_containers.items():
            try:
                bldg_cont_rel_pathes: BuildingContainer = bldg_cont.shallow_copy()
                bldg_cont_rel_pathes.set_bldg_model(self._convert_bldg_model_to_rel_pathes(the_zip, bldg_cont_rel_pathes.get_bldg_model()))
                tmp_bldg_cont_file = self._file_storage_handler.save_single_bldg_container(fid, bldg_cont_rel_pathes, self._temp_dir)
                add_file_to_zip(the_zip, tmp_bldg_cont_file, zip_cont_folder_path)
                os.remove(tmp_bldg_cont_file)
            except KeyError:
                self._logger.warning(f"Building Container for fid {fid} had an error and was therefore not included in the zip file.")

    def _convert_bldg_model_to_rel_pathes(self, the_zip, bldg_model: BuildingModel):
        """
        Note that there is a counterpart method convert_rel_to_abs_pathes_in_model in FileStorageHandler
        handling the relative pathes on loading the building models

        :param bldg_container: [description]
        :type bldg_container: BuildingContainer
        """

        def add_to_zip_if_not_there(orig_path: Union[Path, str]) -> str:
            orig_path_as_str: str = str(orig_path)
            if orig_path_as_str in self._track_zipped_items:
                zip_path = self._track_zipped_items[orig_path_as_str]
            else:
                zip_path = add_file_to_zip(the_zip, orig_path, self.PROJ_RESSOURCES_FOLDER)
                self._track_zipped_items[orig_path_as_str] = zip_path
            return zip_path

        def sched_to_zip_proj_ressources(schedule) -> None:
            if isinstance(schedule, cesarp.common.ScheduleFile):
                zip_path = add_to_zip_if_not_there(schedule.schedule_file)
                # ../.. - go up two folder levels from building model file location in zip to be in root
                schedule.schedule_file = str(Path("..") / Path("..") / Path(zip_path))

        def weather_to_zip_proj_ressources(site: Site) -> None:
            zip_path = add_to_zip_if_not_there(site.weather_file_path)
            # ../.. - go up two folder levels from building model file location in zip to be in root
            site.weather_file_path = str(Path("..") / Path("..") / Path(zip_path))

        model_rel_pathes = copy.deepcopy(bldg_model)

        for (floor_nrs, bldg_op) in model_rel_pathes.bldg_operation_mapping.get_operation_assignments():
            sched_to_zip_proj_ressources(bldg_op.occupancy.occupancy_fraction_schedule)
            sched_to_zip_proj_ressources(bldg_op.occupancy.activity_schedule)
            sched_to_zip_proj_ressources(bldg_op.electric_appliances.fraction_schedule)
            sched_to_zip_proj_ressources(bldg_op.lighting.fraction_schedule)
            sched_to_zip_proj_ressources(bldg_op.dhw.fraction_schedule)
            sched_to_zip_proj_ressources(bldg_op.hvac.heating_setpoint_schedule)
            sched_to_zip_proj_ressources(bldg_op.hvac.cooling_setpoint_schedule)
            sched_to_zip_proj_ressources(bldg_op.hvac.ventilation_fraction_schedule)
        sched_to_zip_proj_ressources(model_rel_pathes.bldg_construction.infiltration_profile)
        weather_to_zip_proj_ressources(model_rel_pathes.site)

        return model_rel_pathes

    def add_project_input_files(self, the_zip: ZipFile):
        cesarp_in_dir = self.PROJ_RESSOURCES_FOLDER
        zip_relative_config = self.add_files_from_config(the_zip, copy.deepcopy(self._main_config), cesarp_in_dir)
        zip_cnf_tmp_path = self._temp_dir / Path(self.MAIN_CONFIG_FILENAME)
        save_config_to_file(zip_relative_config, zip_cnf_tmp_path)
        add_file_to_zip(the_zip, zip_cnf_tmp_path)

    def add_construction_data_ttl_file(self, the_zip: ZipFile):
        graph_cfg = cesarp.common.load_config_for_package(graph_db_access_default_config, "cesarp.graphdb_access", self._main_config)
        if graph_cfg["REMOTE"]["ACTIVE"] and graph_cfg["REMOTE"]["SAVE_DB_EXPORT"]:
            try:
                user = os.environ["GRAPHDB_USER"]
                passwd = os.environ["GRAPHDB_PASSWORD"]
            except KeyError:
                logging.error("please set username and passwort as environment variables GRAPHDB_USER and GRAPHDB_PASSWORD")

            query = graph_cfg["REMOTE"]["SPARQL_ENDPOINT"] + "/statements?infer=False"
            headers = {
                "Accept": "text/turtle",
                "cache-control": "no-store",
                "connection": "keep-alive",
                "content-disposition": "attachment; filename=statements.ttl",
                "content-encoding": "gzip",
                "content-language": "en-US",
                "content-type": "text/turtle;charset=UTF-8",
                "keep-alive": "timeout=60",
                "server": "GraphDB-Free/9.3.0 RDF4J/3.2.0",
                "transfer-encoding": "chunked",
                "vary": "Accept",
                "x-content-type-options": "nosniff",
                "x-frame-options": "SAMEORIGIN",
                "x-xss-protection": "1; mode=block",
            }
            ttl_tmp_path = self._temp_dir / Path(self.CONSTRUCTION_DATA_FILENAME)
            r = requests.get(url=query, headers=headers, auth=(user, passwd))
            with open(ttl_tmp_path, "wb") as fd:
                fd.write(r.content)
            add_file_to_zip(the_zip, ttl_tmp_path, self.PROJ_RESSOURCES_FOLDER, self.CONSTRUCTION_DATA_FILENAME)

    def add_files_from_config(self, the_zip: ZipFile, config: Dict[str, Any], path_in_zip: str):
        for k, val in config.items():
            if type(val) is dict:
                config[k] = self.add_files_from_config(the_zip, val, path_in_zip)
            elif k in ["BLDG_CONTAINERS_FOLDER_REL", "OUTPUT_FOLDER_REL", "IDF_FOLDER_REL"]:
                # avoid copying cesar-p outputs...
                continue
            elif val in self._track_zipped_items:
                config[k] = self._track_zipped_items[val]
            elif os.path.isfile(val):
                path_in_zip = add_file_to_zip(the_zip, val, path_in_zip)
                config[k] = path_in_zip
                self._track_zipped_items[val] = path_in_zip
            elif k in ["PARAMSETS_VARIABLE_SAVE_FOLDER", "PARAMSETS_NOMINAL_SAVE_FOLDER"]:
                if os.path.isdir(val):
                    added_items = add_folder_to_zip(the_zip, val, path_in_zip)
                    self._track_zipped_items.update(added_items)
                config[k] = str(path_in_zip / Path(os.path.basename(val)))
        return config

    def create_environment_files(self):
        git_info_path = self._temp_dir / Path(self.GIT_STATUS_FILENAME)
        with open(git_info_path, "w") as fd:
            version_info.get_git_extended_status(fd)
        versions = self._temp_dir / Path("system_versions.txt")
        with open(versions, "w") as fd:
            version_info.get_env_info(fd)
            version_info.write_title("ENERGYPLUS", fd)
            fd.write(f"Energyplus Version:\t{get_eplus_version(custom_config=self._main_config)}\n")
            fd.write(f"Energyplus Executable:\t{get_eplus_executable(custom_config=self._main_config)}\n")
            fd.write(f"Energyplus IDD:\t{get_idd_path(custom_config=self._main_config)}\n")
        pip_freeze = self._temp_dir / Path("python_pip_requirements.txt")
        with open(pip_freeze, "w") as fd:
            version_info.write_python_pip_freeze(fd)
        return [git_info_path, versions, pip_freeze]

    def create_source_wheel(self):
        """
        In order to be able to create and include the tar in your project save, you must have a CESAR-P clone set up with poetry
        """
        if version_info.is_git_clone():
            git_root_dir = cesarp.common.version_info.get_git_clone_root()
            try:
                retcode = subprocess.call(["poetry", "build", "--format", "wheel"], shell=True, cwd=git_root_dir)
                if 1 == retcode:
                    self._logger.info("poetry not found or other error during generation of wheel package generation. wheel not included in ZIP export.")
                    return None
            except Exception as e:
                self._logger.warning("running poetry to create source wheel package failed", e)
                return None
            wheel_dist_files = glob.glob(str(git_root_dir / Path("dist") / Path("*.whl")))
            wheel_dist_files.sort(key=os.path.getctime, reverse=True)
            return wheel_dist_files[0]
        return None

    def write_zip_description(self, file_descriptor, include_bldg_models, include_idfs, include_eplus_output):
        # file_descriptor.writelines("===================================================\n")
        file_descriptor.writelines("ZIP PACKAGE CONTENTS\n")
        file_descriptor.writelines("----------------------------\n")
        file_descriptor.writelines("\n**root folder**\n\n")
        file_descriptor.writelines("Configuration and startup script.\n")
        file_descriptor.writelines(
            "Configuration was adapted to reflect relative pathes to the input files in that zip folder.\nNote that configuration is always saved as main_config_for_zip.yml, so you need to adapt to that name in the startup script.\n"
        )
        file_descriptor.writelines("\n**cesarp_output**\n\n")
        file_descriptor.writelines("output files from cesar-p run.\n")
        if include_bldg_models:
            file_descriptor.writelines(f"\n**{os.path.basename(self._file_storage_handler.container_save_path)}**\n\n")
            file_descriptor.writelines("In this folder you find the json dumps of the cesar-p internal building models. They include all data to create the IDF files.\n")
            file_descriptor.writelines(
                "You can re-load those models into a SimulationManager instance to query data on all building. In the example the roof construction per building is collected. Expected to be run as script in root folder of ZIP.\n\n"
            )
            file_descriptor.writelines(
                "\timport cesarp.common\n"
                "\tfrom cesarp.manager.SimulationManager import SimulationManager\n"
                f"\tsim_mgr = SimulationManager('{self.CESARP_OUTPUTS_FOLDER}', '{self.MAIN_CONFIG_FILENAME}', cesarp.common.init_unit_registry(), load_from_disk=True)\n"
            )
            file_descriptor.writelines(
                "\troof_constructions = {fid: ctr.get_bldg_model().bldg_construction.roof_constr.short_name for fid, ctr in sim_mgr.bldg_containers.items()}\n"
            )
        if include_idfs:
            file_descriptor.writelines(f"\n**{os.path.basename(self._file_storage_handler.idf_output_dir)}**\n\n")
            file_descriptor.writelines("In this folder you find the IDF files for all the simulated buildings.\n")
        if include_eplus_output:
            file_descriptor.writelines(f"**{os.path.basename(self._file_storage_handler.eplus_output_dir)}**\n\n")
            file_descriptor.writelines("In this folder you find raw simulation outputs of eneregy plus for each building.\n")
        file_descriptor.writelines("**project_ressources**\n")
        file_descriptor.writelines(
            "In this folder all project specific input files are stored, this means all files referenced in the configuration file should have been copied here when the ZIP file was created.\n"
        )
        file_descriptor.writelines("\n**runtime_environment**\n")
        file_descriptor.writelines("Here are collected information about the runtime setup from the computer where the ZIP file was created.\n")
        file_descriptor.writelines(
            "If possible a copy of used CESAR-P sources are included as installable pip-package (whl). This is only the case if CESAR-P was installed in developer mode and poetry was available when creating the ZIP.\n"
        )
        file_descriptor.writelines("\n\n")

    def write_installation_instructions(self, file_descriptor):
        # file_descriptor.writelines("===================================================\n")
        file_descriptor.writelines("INSTALLATION\n")
        file_descriptor.writelines("----------------------------\n")
        file_descriptor.writelines("\nUnzip all files to any location.\n")
        file_descriptor.writelines(
            "Open command promt, e.g. by typing cmd after pressing the main menu button (note that commands in that guide to not work in Windows PowerShell!)\n"
        )

        file_descriptor.writelines("\n**ENERGY PLUS**\n\n")
        file_descriptor.writelines(f"Download and install Energy Plus version {get_eplus_version(custom_config=self._main_config)} from https://www.energyplus.net/downloads\n")
        file_descriptor.writelines("Set energyplus version and executable as user environment variables:\n")
        file_descriptor.writelines(f"\tset ENERGYPLUS_VER={get_eplus_version(custom_config=self._main_config)}\n")
        file_descriptor.writelines("\tset ENERGYPLUS_EXE=C:/YOUR_INSTALLATION_DIRECTORY/energyplus.exe\n")
        file_descriptor.writelines("Close and re-open any open terminals and your IDE to activate the new environment variables.\n")

        file_descriptor.writelines("\n**PYTHON**\n\n")
        file_descriptor.writelines(
            f"Download and Install Python version {version_info.get_python_version()} from https://www.python.org/downloads/. If you already have a Python installation, do not tick 'Add Python X.Y to Path' during installation procedure.\n"
        )
        file_descriptor.writelines("In case python is not in your PATH, then preceed python with the path to your python installation.\n")
        file_descriptor.writelines(
            "Create a new virtual environment (you can adapt the location of the venv as you wish - your home directory or any other location on the fileserver is not a sensible choice and might run out of space when installing all dependencies.).\n\n"
        )
        file_descriptor.writelines(f"\tpython -m venv %USERPROFILE%/venv-cesarp-{Path(self._zip_file_path).stem}\n")
        file_descriptor.writelines("Activate your venv with:\n\n")
        file_descriptor.writelines(f"\t%USERPROFILE%/venv-cesarp-{Path(self._zip_file_path).stem}/Scripts/activate\n")

        file_descriptor.writelines("\n**CESAR-P (including dependencies)**\n\n")
        if self._src_wheel_zip_rel_path:
            file_descriptor.writelines("A code copy was packed with that project.\n")
            file_descriptor.writelines(
                f"CESAR-P version is {version('cesar-p')}, but it might have local code changes. For details see git diff under {self.RUNTIME_ENV_FOLDER + '/' + self.GIT_STATUS_FILENAME}\n"
            )
            file_descriptor.writelines("In the console with the activated virtual environment, navigate to the root folder of the unzipped project, then do:\n\n")
            file_descriptor.writelines(f"\tpip install {self._src_wheel_zip_rel_path}\n")
            file_descriptor.writelines("This will install CESAR-P and it's dependencies.\n")
        else:
            file_descriptor.writelines(
                f"The project used CESAR-P version {version('cesar-p')}. To install that version from the corresponding tagged git repository version, do:\n\n"
            )
            file_descriptor.writelines(f"\tpip install cesar-p=={version('cesar-p')}\n\n")
            file_descriptor.writelines("This will install CESAR-P and it's dependencies.")
            file_descriptor.writelines(
                "If the version is not released on PyPi you can see if there is a tag for it on https://github.com/hues-platform/cesar-p-core and install from that Tag with \n"
            )
            file_descriptor.writelines(f"\tpip install git+https://github.com/hues-platform/cesar-p-core.git@{version('cesar-p')}#egg=cesar_p\n\n")
        if "geopandas" in sys.modules:
            file_descriptor.writelines(
                f"\n\nThe library geopandas (version {version('geopandas')}) was installed in the python environment where the project was exported from.\nThus, the project might import site vertices form shape files.\n"
            )
            file_descriptor.writelines("As some requirements for geopandas are not available from PyPi for Windows, you have to manually install if shapefiles are used.\n")
            file_descriptor.writelines(
                f"Download wheels for GDAL version {version('gdal')} and Fiona version {version('fiona')} from https://www.lfd.uci.edu/~gohlke/pythonlibs (See also https://github.com/Toblerity/Fiona#windows).\n"
            )
            file_descriptor.writelines("Install first GDAL, then Fiona and then geopandas:\n\n")
            file_descriptor.writelines("\tpip install gdal-xxxx.whl\n")
            file_descriptor.writelines("\tpip install fiona-xxxx.whl\n")
            file_descriptor.writelines(f"\tpip install geopandas=={version('geopandas')}\n")

        # file_descriptor.writelines("\n===================================================\n")
        file_descriptor.writelines("\nRUN PROJECT\n")
        file_descriptor.writelines("----------------------------\n")
        main_script_name = os.path.basename(self._main_script_path)
        file_descriptor.writelines(f"The Python script {main_script_name} in the root of the ZIP should be the one to run the project.\n")
        file_descriptor.writelines(f"Edit {main_script_name} to point to configuration file {self.MAIN_CONFIG_FILENAME}\n")
        file_descriptor.writelines(
            f"Do not move {self.MAIN_CONFIG_FILENAME} to another folder level, as it points with relative pathes to the project input files under {self.PROJ_RESSOURCES_FOLDER}!\n"
        )

        file_descriptor.writelines("In the Python virtual environment created above then run the simulation script:\n")
        file_descriptor.writelines(f"\n\tpython {main_script_name}\n")

        file_descriptor.writelines(
            f"\nIn case your project has a special setup for weather files, make sure the weather files are available. If you load exisitng IDF files and the weather mapping file ({os.path.basename(self._file_storage_handler.weather_files_mapped_save_path)}) along with them, adapt pathes to the new project location\n"
        )
