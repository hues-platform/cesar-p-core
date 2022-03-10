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
import shutil
from pathlib import Path

import cesarp.common
from cesarp.common.filehandling import scan_directory
from cesarp.manager.SimulationManager import SimulationManager
from tests.test_helpers import test_helpers
from eppy.modeleditor import IDF

_TESTFIXTURE_FOLDER = os.path.dirname(__file__) / Path("testfixture")
_TEST_WEATHER_FILE_PATH = str(os.path.dirname(__file__) / Path("testfixture") / Path("sample_case") / Path("Zurich_1.epw"))

@pytest.fixture
def result_main_folder():
    result_main_folder = os.path.dirname(__file__) / Path("result_nosim")
    shutil.rmtree(result_main_folder, ignore_errors=True)
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
    config["MANAGER"]["CONSTRUCTION_DB"] = "GRAPH_DB"
    config["EPLUS_ADAPTER"] = {"WINDOW_SHADING": True, "NIGHT_VENTILATION": True}
    config["GEOMETRY"] = {"MAIN_BLDG_SHAPE":{"WINDOW": {"MIN_WALL_WIDTH_FOR_WINDOW":  0.05, "MIN_WINDOW_WIDTH": 0.01, "WINDOW_FRAME": {"WIDTH": 0.002}}}}
    return config

def test_weather_per_community(result_main_folder, default_main_cfg):
    base_folder = str(result_main_folder / Path("weather_per_community"))
    sim_manager = SimulationManager(base_folder, default_main_cfg, cesarp.common.init_unit_registry())

    sim_manager.create_bldg_models()
    sim_manager.save_bldg_containers()
    mdls_outpath = base_folder / Path("bldg_containers")
    assert len(os.listdir(mdls_outpath)) == 9
    assert any([os.path.getsize(mdls_outpath / Path(mdl_dump)) > 0 for mdl_dump in os.listdir(mdls_outpath)])

    sim_manager.create_IDFs()
    idf_output = base_folder / Path("idfs")
    idf_res_files = scan_directory(idf_output, "fid_{}.idf").values()
    assert len(idf_res_files) == 9
    assert any([os.path.getsize(idf_output / Path(idf)) > 0 for idf in idf_res_files])
    assert os.path.getsize(idf_output / Path("weather_files_mapped.csvy")) > 0
    assert len(os.listdir(idf_output / Path("profiles"))) == 1
