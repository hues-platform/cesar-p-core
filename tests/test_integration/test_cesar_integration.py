# -*- coding: utf-8 -*-
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

"""Tests for `cesar` package."""

import os
import shutil
from pathlib import Path
import sys

import pytest
from cesarp.manager.SimulationManager import SimulationManager
from cesarp.manager.debug_methods import run_single_bldg
import cesarp.common

from tests.test_helpers.test_helpers import are_files_equal

_TESTFIXTURE_FOLDER = os.path.dirname(__file__) / Path("testfixture")
_TEST_WEATHER_FILE_PATH = str(os.path.dirname(__file__) / Path("testfixture") / Path("sample_case") / Path("Zurich_1.epw"))

@pytest.fixture
def result_main_folder():
    result_main_folder = os.path.dirname(__file__) / Path("result")
    try:
        shutil.rmtree(result_main_folder)
    except Exception:
        pass
    yield result_main_folder
    #shutil.rmtree(result_main_folder)



@pytest.fixture
def config_sample_case():
    bldg_info_file = str(_TESTFIXTURE_FOLDER / Path("sample_case/BuildingInformation.csv"))
    config = dict()
    config["MANAGER"] = dict()
    config["MANAGER"]["SITE_VERTICES_FILE"] = {"PATH": str(os.path.dirname(__file__) / Path("./testfixture/sample_case/SiteVertices.csv"))}
    config["MANAGER"]["BLDG_FID_FILE"] = {"PATH": bldg_info_file}
    config["MANAGER"]["BLDG_AGE_FILE"] = {"PATH": bldg_info_file}
    config["MANAGER"]["BLDG_INSTALLATION_FILE"] = {"PATH": bldg_info_file}
    config["MANAGER"]["BLDG_TYPE_PER_BLDG_FILE"] = {"PATH": bldg_info_file}
    config["MANAGER"]["SINGLE_SITE"] = {"WEATHER_FILE": _TEST_WEATHER_FILE_PATH}
    config["MANAGER"]["COPY_PROFILES"] = {"ACTIVE": True, "PROFILES_FOLDER_NAME_REL": "profiles"}
    config["MANAGER"]["BUILDING_OPERATION_FACTORY_CLASS"] = "cesarp.operation.fixed.FixedBuildingOperationFactory.FixedBuildingOperationFactory"
    config["CONSTRUCTION"] = dict()
    config["CONSTRUCTION"]["CONSTRUCTION_DB"] = "GRAPH_DB"
    config["OPERATION"] = {
                                "WINDOW_SHADING_CONTROL": {"ACTIVE": False},
                                "NIGHT_VENTILATION": {"ACTIVE": False}
                              }
    return config


@pytest.fixture
def config_no_adjacencies_case():
    bldg_info_file = os.path.dirname(__file__) / Path("./testfixture/no_adjacencies_case/building_info_mfh_testing.csv")
    config = dict()
    config["MANAGER"] = dict()
    config["MANAGER"]["SITE_VERTICES_FILE"] = {"PATH": os.path.dirname(__file__) / Path("./testfixture/no_adjacencies_case/site_vertices_mfh_testing.csv")}
    config["MANAGER"]["GLAZING_RATIO_PER_BLDG_FILE"] = {"PATH": bldg_info_file, "ACTIVE": True}
    config["MANAGER"]["BLDG_FID_FILE"] = {"PATH": bldg_info_file}
    config["MANAGER"]["BLDG_AGE_FILE"] = {"PATH": bldg_info_file}
    config["MANAGER"]["BLDG_INSTALLATION_FILE"] = {"PATH": bldg_info_file}
    config["MANAGER"]["BLDG_TYPE_PER_BLDG_FILE"] = {"PATH": bldg_info_file}
    config["MANAGER"]["SINGLE_SITE"] = {"WEATHER_FILE": os.path.dirname(__file__) / Path("./testfixture/no_adjacencies_case/Zermatt.epw")}
    config["MANAGER"]["COPY_PROFILES"] = {"ACTIVE": True, "PROFILES_FOLDER_NAME_REL": "profiles"}
    config["MANAGER"]["BUILDING_OPERATION_FACTORY_CLASS"] = "cesarp.operation.fixed.FixedBuildingOperationFactory.FixedBuildingOperationFactory"
    config["CONSTRUCTION"] = dict()
    config["CONSTRUCTION"]["CONSTRUCTION_DB"] = "GRAPH_DB"
    config["GEOMETRY"] = {"NEIGHBOURHOOD": {"RADIUS": 50}}
    config["OPERATION"] = {"FIXED": {
                                        "SCHED_THERMOSTAT_HEATING": os.path.dirname(__file__) / Path("./testfixture/no_adjacencies_case/mfh_nominal_thermostat_heating.csv"),
                                        "SCHED_DHW_PATH": os.path.dirname(__file__) / Path("./testfixture/no_adjacencies_case/mfh_nominal_dhw.csv")
                                    },
                            "WINDOW_SHADING_CONTROL": {"ACTIVE": False},
                            "NIGHT_VENTILATION": {"ACTIVE": False}
                          }
    return config


#@pytest.mark.skipif(sys.platform != "win32",reason="E+ not running on git ci")
def test_run_cesar_no_neighbourhood(config_sample_case, result_main_folder):
    config = config_sample_case
    res_base_path = result_main_folder / Path("sample_case_no_neighbourhood")
    result_idf_file_path = res_base_path / Path("idfs") / "fid_2.idf"
    result_eplus_folder = res_base_path / Path("eplus_output") / Path("fid_2")
    result_file_path = result_eplus_folder / Path("eplustbl.csv")
    result_summary_path = res_base_path / Path("site_result_summary.csvy")

    expected_folder_path = os.path.dirname(__file__) / Path("./expected_result/sample_case_no_neighbourhood/gis_fid2/")
    expected_res_sum_path = os.path.dirname(__file__) / Path("./expected_result/sample_case_no_neighbourhood/site_result_summary.csvy")
    expected_idf_file_path = expected_folder_path / Path("fid_2_fixed_constr_fixed_sched_no_neighbourhood.idf")
    expected_res_file_path = expected_folder_path / Path("eplustbl_result_fid2_fixed_constr_fixed_sched_no_neighbourhood.csv")

    config["GEOMETRY"] = {"NEIGHBOURHOOD": {"RADIUS": 0}}
    gis_fid = 2
    sim_mgr = SimulationManager(res_base_path, config, cesarp.common.init_unit_registry(), fids_to_use=[gis_fid])
    sim_mgr.run_all_steps()

    assert are_files_equal(result_idf_file_path,
                           expected_idf_file_path,
                           ignore_line_nrs=[1],
                           ignore_filesep_mismatch=True) is True, "IDF files not equal"

    # Line 0 and 177 contain energyplus veriosn and date/time of execution, thus ignore those
    assert are_files_equal(result_file_path, expected_res_file_path, ignore_line_nrs=[1,178]) is True, "E+ results not equal"
    assert are_files_equal(result_summary_path, expected_res_sum_path, ignore_line_nrs=[189], ignore_changing_config=True)


def test_create_idf_with_SIA_generated_profiles(config_sample_case, result_main_folder):
    config = config_sample_case
    res_base_path = result_main_folder / Path("sia_test_sample_case_no_neighbourhood")
    config["MANAGER"]["BLDG_TYPE_PER_BLDG_FILE"] = {"PATH": str(os.path.dirname(__file__) / Path("./testfixture/sample_case/BuildingInformation.csv"))}
    config["MANAGER"]["BUILDING_OPERATION_FACTORY_CLASS"] = "cesarp.SIA2024.SIA2024Facade.SIA2024Facade"
    config["MANAGER"]["INFILTRATION_RATE_SOURCE"] = "SIA2024"
    expected_folder_path = os.path.dirname(__file__) / Path("./expected_result/sia_test_sample_case_no_neighbourhood/")
    expected_idf_file_path = expected_folder_path / Path("gis_fid2") / Path("fid_2.idf")
    config["GEOMETRY"] = {"NEIGHBOURHOOD": {"RADIUS": 0}}
    gis_fid = 2
    sim_mgr = SimulationManager(res_base_path, config, cesarp.common.init_unit_registry(), fids_to_use=[gis_fid])
    sim_mgr.create_bldg_models()
    sim_mgr.create_IDFs()
    assert are_files_equal(sim_mgr.idf_pathes[gis_fid],
                           expected_idf_file_path,
                           ignore_line_nrs=[1],
                           ignore_filesep_mismatch=True)


def test_run_cesar_with_neighbourhood(config_sample_case, result_main_folder):
    config = config_sample_case
    res_base_path = result_main_folder / Path("sample_case_with_neighbourhood")
    result_idf_file_path = res_base_path / "fid2_fixed_constr_fixed_sched_neighbourhood100.idf"
    result_eplus_folder = res_base_path / Path("eplusout")
    result_file_path = result_eplus_folder / Path("eplustbl.csv")
    expected_folder_path = os.path.dirname(__file__) / Path("expected_result") / Path("sample_case_with_neighbourhood") / Path("gis_fid2")
    expected_idf_file_path = expected_folder_path / Path("fid2_fixed_constr_fixed_sched_neighbourhood100.idf")
    expected_res_file_path = expected_folder_path / Path("eplustbl_result_fid2_fixed_constr_fixed_sched_neighbourhood100.csv")

    gis_fid = 2
    config["GEOMETRY"] = {"NEIGHBOURHOOD": {"RADIUS": 100}}
    ureg = cesarp.common.init_unit_registry()
    run_single_bldg(gis_fid, _TEST_WEATHER_FILE_PATH, result_idf_file_path, result_eplus_folder, config, ureg)
    assert are_files_equal(result_idf_file_path,
                           expected_idf_file_path,
                           ignore_line_nrs=[1],
                           ignore_filesep_mismatch=True
                           ) is True, "IDF files not equal"
    # Line 0 and 177 contain energyplus veriosn and date/time of execution, thus ignore those
    assert are_files_equal(result_file_path,
                           expected_res_file_path,
                           ignore_line_nrs=[1,178, 751]  # on line 751 there is a small numeric difference when run on windows vs linux...
                           ) is True, "E+ results not equal"


def test_no_adjacencies(config_no_adjacencies_case, result_main_folder):
    """ Testcase data provided by Manolis """
    """ Tests usage of parallel workers, as the run_all_steps() function is called and not the run_single_bldg() as in the other testcases """
    config = config_no_adjacencies_case
    expected_folder_path = os.path.dirname(__file__) / Path("expected_result") / Path("no_adjacencies_case")
    expected_idf_file_path = str(expected_folder_path / Path("fid_{}.idf"))
    expected_result_file_path = str(expected_folder_path / Path("fid_job{}Table.csv"))
    res_base_path = result_main_folder / Path("no_adjacencies_case/")

    bldg_fids = [307143, 1150082]

    sim_mgr = SimulationManager(res_base_path, config, cesarp.common.init_unit_registry())
    sim_mgr.run_all_steps()

    for bldg_fid in bldg_fids:
        assert are_files_equal(sim_mgr.idf_pathes[bldg_fid],
                               expected_idf_file_path.format(bldg_fid),
                               ignore_line_nrs = [1],
                               ignore_filesep_mismatch = True) is True, f'IDF files not equal for {bldg_fid}'
        # Line 0 and 177 contain energyplus veriosn and date/time of execution, thus ignore those;
        # on line 709 and 1463 there is a small numeric difference when run on windows vs linux...
        assert are_files_equal(sim_mgr.output_folders[bldg_fid] / Path("eplustbl.csv") , expected_result_file_path.format(bldg_fid), ignore_line_nrs=[1,178,709, 1463]) is True, f'result files not equal for {bldg_fid}'


def test_window_shading(result_main_folder):
    """ validated agains matlab implementation of ricardo """
    cfg_file = _TESTFIXTURE_FOLDER / Path("cooling") / Path("main_config.yml")
    cfg = cesarp.common.load_config_full(cfg_file)
    cfg["OPERATION"] = {
                            "WINDOW_SHADING_CONTROL": {"ACTIVE": True},
                            "NIGHT_VENTILATION": {"ACTIVE": False}
                          }
    # Note: trick to debug results: remove deleting result folder in res_folder(), then run it once, then uncomment
    #       sim_mgr.run_all_steps(), change load_from_disk=True and then debug and check the results...
    sim_mgr = SimulationManager(result_main_folder / Path("sim_test"), cfg, cesarp.common.init_unit_registry(),
                                load_from_disk=False)
    sim_mgr.run_all_steps()
    results = sim_mgr.get_all_results_summary()
    dhw_annual_expected = pytest.approx(10351.6, rel=0.005)
    electricity_annual_expected = pytest.approx(71953)
    assert results.loc[2, "h * kiloW / year"]["Cooling Annual"] == pytest.approx(297.6, rel=0.005)
    assert results.loc[2, "h * kiloW / year"]["Heating Annual"] == pytest.approx(172524, rel=0.005)
    assert results.loc[2, "h * kiloW / year"]["DHW Annual"] == dhw_annual_expected
    assert results.loc[2, "h * kiloW / year"]["Electricity Annual"] == electricity_annual_expected

    assert results.loc[7, "h * kiloW / year"]["Cooling Annual"] == pytest.approx(13718.5, rel=0.005)
    assert results.loc[7, "h * kiloW / year"]["Heating Annual"] == pytest.approx(21194.7, rel=0.005)
    assert results.loc[7, "h * kiloW / year"]["DHW Annual"] == dhw_annual_expected
    assert results.loc[7, "h * kiloW / year"]["Electricity Annual"] == electricity_annual_expected

    assert results.loc[8, "h * kiloW / year"]["Cooling Annual"] == pytest.approx(16000.9, rel=0.005)
    assert results.loc[8, "h * kiloW / year"]["Heating Annual"] == pytest.approx(15840.86, rel=0.005)
    assert results.loc[8, "h * kiloW / year"]["DHW Annual"] == dhw_annual_expected
    assert results.loc[8, "h * kiloW / year"]["Electricity Annual"] == electricity_annual_expected

    assert results.loc[9, "h * kiloW / year"]["Cooling Annual"] == pytest.approx(14822.8, rel=0.005)
    assert results.loc[9, "h * kiloW / year"]["Heating Annual"] == pytest.approx(14548.6, rel=0.005)
    assert results.loc[9, "h * kiloW / year"]["DHW Annual"] == dhw_annual_expected
    assert results.loc[9, "h * kiloW / year"]["Electricity Annual"] == electricity_annual_expected


def test_night_ventilation(result_main_folder):
    cfg_file = _TESTFIXTURE_FOLDER / Path("cooling") / Path("main_config.yml")
    cfg = cesarp.common.load_config_full(cfg_file)
    cfg["OPERATION"] = {
                            "WINDOW_SHADING_CONTROL": {"ACTIVE": False},
                            "NIGHT_VENTILATION": {"ACTIVE": True}
                          }
    # Note: trick to debug results: remove deleting result folder in res_folder(), then run it once, then uncomment
    #       sim_mgr.run_all_steps(), change load_from_disk=True and then debug and check the results...
    sim_mgr = SimulationManager(result_main_folder / Path("sim_test"), cfg, cesarp.common.init_unit_registry(),
                                load_from_disk=False, fids_to_use=[7])
    sim_mgr.run_all_steps()
    results = sim_mgr.get_all_results_summary()
    dhw_annual_expected = pytest.approx(10364.1775, rel=0.005)
    electricity_annual_expected = pytest.approx(71952.9883)
    assert results.loc[7, "h * kiloW / year"]["Cooling Annual"] == pytest.approx(13633.8, rel=0.005)
    assert results.loc[7, "h * kiloW / year"]["Heating Annual"] == pytest.approx(14744.2, rel=0.005)
    assert results.loc[7, "h * kiloW / year"]["DHW Annual"] == dhw_annual_expected
    assert results.loc[7, "h * kiloW / year"]["Electricity Annual"] == electricity_annual_expected
