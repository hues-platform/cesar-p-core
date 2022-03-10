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
import pytest
import os
import sys
import shutil
from pathlib import Path
import logging

import cesarp.common
from cesarp.common.filehandling import scan_directory
from cesarp.manager.SimulationManager import SimulationManager
from tests.test_helpers import test_helpers
from cesarp.manager.debug_methods import run_single_bldg

_TESTFIXTURE_FOLDER = os.path.dirname(__file__) / Path("testfixture")
_TEST_WEATHER_FILE_PATH = str(os.path.dirname(__file__) / Path("testfixture") / Path("sample_case") / Path("Zurich_1.epw"))

@pytest.fixture(scope="module")
def ep_version_setup():
    try:
        previous_set_ver = os.environ['ENERGYPLUS_VER']
    except KeyError:
        previous_set_ver = None

    os.environ['ENERGYPLUS_VER'] = "9.5.0"
    yield None
    if previous_set_ver:
        os.environ['ENERGYPLUS_VER'] = previous_set_ver

@pytest.fixture
def result_main_folder():
    result_main_folder = os.path.dirname(__file__) / Path("result_nosim_93")
    shutil.rmtree(result_main_folder, ignore_errors=True)
    if not os.path.exists(result_main_folder):
        os.mkdir(result_main_folder)
    yield result_main_folder
    shutil.rmtree(result_main_folder, ignore_errors=True)

@pytest.fixture
def default_main_cfg():
    cfg = os.path.dirname(__file__) / Path("testfixture") / Path("base_example") / "main_config.yml"
    yield cfg


@pytest.fixture
def config_many_vertices():
    bldg_info_file = str(_TESTFIXTURE_FOLDER / Path("many_vertices/BuildingInfo.csv"))
    config = dict()
    config["MANAGER"] = dict()
    config["MANAGER"]["SITE_VERTICES_FILE"] = {"PATH": str(_TESTFIXTURE_FOLDER / Path("many_vertices") / Path("BuildingVertices14002.csv"))}
    config["MANAGER"]["BLDG_FID_FILE"] = {"PATH": bldg_info_file}
    config["MANAGER"]["BLDG_AGE_FILE"] = {"PATH": bldg_info_file}
    config["MANAGER"]["BLDG_INSTALLATION_FILE"] = {"PATH": bldg_info_file}
    config["MANAGER"]["BLDG_TYPE_PER_BLDG_FILE"] = {"PATH": bldg_info_file}
    config["MANAGER"]["SINGLE_SITE"] = {"WEATHER_FILE": _TEST_WEATHER_FILE_PATH}
    config["MANAGER"]["COPY_PROFILES"] = {"ACTIVE": True, "PROFILES_FOLDER_NAME_REL": "profiles"}

    config["MANAGER"]["BUILDING_OPERATION_FACTORY_CLASS"] = "cesarp.operation.fixed.FixedBuildingOperationFactory.FixedBuildingOperationFactory"
    config["CONSTRUCTION"] = {"CONSTRUCTION_DB": "GRAPH_DB"}
    config["EPLUS_ADAPTER"] = {"EPLUS_VERSION": "9.5"}
    # following porperties are set so that for the building 14002 less than 100 windows, but more than 10, are modeled
    config["GEOMETRY"] = {"MAIN_BLDG_SHAPE":{"WINDOW": {"MIN_WALL_WIDTH_FOR_WINDOW": 0.09, "MIN_WINDOW_WIDTH": 0.01, "WINDOW_FRAME": {"WIDTH": 0.002}}}}
    return config


def test_window_shading(result_main_folder, default_main_cfg, ep_version_setup, caplog):
    caplog.set_level(logging.DEBUG, logger="cesarp.manager.processing_steps")
    caplog.set_level(logging.DEBUG, logger="cesarp.manager.SimulationManager")
    all_config = cesarp.common.load_config_full(default_main_cfg)
    if not "EPLUS_ADAPTER" in all_config.keys():
        all_config["EPLUS_ADAPTER"] = {}
    all_config["EPLUS_ADAPTER"]["EPLUS_VERSION"] = "9.5"
    all_config["OPERATION"] = {"WINDOW_SHADING_CONTROL": {"ACTIVE": True}}
    if "GEOMETRY" not in all_config.keys():
        all_config["GEOMETRY"] = {}
    if "NEIGHBOURHOIOD" not in all_config["GEOMETRY"].keys():
        all_config["GEOMETRY"]["NEIGHBOURHOOD"] = {}
    all_config["GEOMETRY"]["NEIGHBOURHOOD"]["RADIUS"] = 0 # to get less complicated IDF
    base_folder = str(result_main_folder / Path("win_shading_ep95"))

    idf_output = base_folder / Path("idfs") / "fid_4.idf"
    #run_single_bldg(4, "dummy_weather.epw", idf_output, str(base_folder/Path("ep_res_fid4")), all_config, cesarp.common.init_unit_registry())

    sim_manager = SimulationManager(base_folder, all_config, cesarp.common.init_unit_registry(), fids_to_use=[4])

    sim_manager.create_bldg_models()
    sim_manager.create_IDFs()

    expected_output = os.path.dirname(__file__) / Path("expected_result") / Path("win_shading") / Path("fid_4_win_shading_ep95.idf")
    assert test_helpers.are_files_equal(idf_output, expected_output, ignore_changing_config=True, ignore_filesep_mismatch=True, ignore_line_nrs=[1])


def test_night_vent(result_main_folder, default_main_cfg, ep_version_setup, caplog):
    caplog.set_level(logging.DEBUG, logger="cesarp.manager.processing_steps")
    caplog.set_level(logging.DEBUG, logger="cesarp.manager.SimulationManager")
    all_config = cesarp.common.load_config_full(default_main_cfg)
    all_config["EPLUS_ADAPTER"] = {"EPLUS_VERSION": "9.5"}
    all_config["OPERATION"] = {"NIGHT_VENTILATION": {"ACTIVE": True}}
    if "GEOMETRY" not in all_config.keys():
        all_config["GEOMETRY"] = {}
    if "NEIGHBOURHOIOD" not in all_config["GEOMETRY"].keys():
        all_config["GEOMETRY"]["NEIGHBOURHOOD"] = {}
    if "CONSTRUCTION" not in all_config.keys():
        all_config["CONSTRUCTION"] = {}
    all_config["CONSTRUCTION"]["CONSTRUCTION_DB"] = "GRAPH_DB"
    all_config["GEOMETRY"]["NEIGHBOURHOOD"]["RADIUS"] = 0 # to get less complicated IDF
    base_folder = str(result_main_folder / Path("night_vent"))

    idf_output = base_folder / Path("idfs") / "fid_2.idf"
    #run_single_bldg(4, "dummy_weather.epw", idf_output, str(base_folder/Path("ep_res_fid4")), all_config, cesarp.common.init_unit_registry())

    sim_manager = SimulationManager(base_folder, all_config, cesarp.common.init_unit_registry(), fids_to_use=[2])

    sim_manager.create_bldg_models()
    sim_manager.create_IDFs()

    expected_output = os.path.dirname(__file__) / Path("expected_result") / Path("night_vent") / Path("fid_2_night_vent_ep95.idf")
    assert test_helpers.are_files_equal(idf_output, expected_output, ignore_changing_config=True, ignore_filesep_mismatch=True, ignore_line_nrs=[1])

def test_many_vertices_building(result_main_folder, config_many_vertices, ep_version_setup):
    fid = 14002
    res_base_path = result_main_folder / Path("sample_case_many_vertices_95")
    result_idf_file_path = res_base_path / Path("idfs") / f"fid_{fid}.idf"

    sim_mgr = SimulationManager(res_base_path, config_many_vertices, cesarp.common.init_unit_registry(), fids_to_use=[fid])
    sim_mgr.create_bldg_models()
    sim_mgr.create_IDFs()

    # if not enough vertices can be created or not enough windows can be added for windowshadingcontrol due to an error in the IDD or not adapted IDD
    # creation of IDF file crashes
    # not comparing IDF files to avoid the need to adapt this expected result file when other changes are made
    assert os.path.exists(result_idf_file_path)
