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
from cesarp.common import config_loader
import copy
import os
from pathlib import Path
import pytest

__HELLO_expected_test_config = {"WORLD": "How are you?", "SUNSHINE": "good"}

_TEST_CFG_PATH = os.path.dirname(__file__) / Path("./testfixture/testConfig.yml")
_TEST_SUBPKG_CONFIG_PATH  = os.path.dirname(__file__) / Path("./testfixture/testConfigSubpackage.yml")
_TEST_DUPLICATES_CONFIG_PATH = os.path.dirname(__file__) / Path("./testfixture/testConfigDuplicateKey.yml")

def test_config_default():
    config = config_loader.load_config_for_package(_TEST_CFG_PATH, "cesarp.hello")
    assert isinstance(config["WORLD"], str)
    assert config == __HELLO_expected_test_config

def test_config_with_custom():
    custom_cfg = {"HELLO": {"SUNSHINE": "warm", "DARKNESS": "cold"}}
    config = config_loader.load_config_for_package(_TEST_CFG_PATH, "cesarp.hello", custom_cfg)
    assert isinstance(config["WORLD"], str)
    assert config["WORLD"] == "How are you?"
    assert config["DARKNESS"] == "cold"
    assert config["SUNSHINE"] == "warm"

def test_merge_config():
    default = {"manager": {"path": "default_path", "separator": ","}, "geometry": {"win": "xy"}}
    custom = {"manager": {"path": "custom_path"}}
    res = config_loader.merge_config_recursive(default, custom)
    assert res == {"manager": {"path": "custom_path", "separator": ","}, "geometry": {"win": "xy"}}

def test_convert_pathes():
    config_path = _TEST_CFG_PATH
    config_dir = os.path.dirname(config_path)
    config = config_loader.load_config_full(config_path)
    config_loader.__convert_entries_to_abs_pathes(config, config_dir)

    assert(config["HELLO"] == __HELLO_expected_test_config) # entries in HELLO should be unchanged, no pathes
    assert(config["ABS_PATHES_TEST"] == {"TESTFILE": str(config_dir / Path("../test/test.txt")),
                                         "TEST_PATH": str(config_dir / Path("./yapath/subdir")),
                                         "SOMETHING": str(config_dir / Path("testfile.idf"))})

def test_config_subpackage():
    custom_cfg = {"MOM": {"CHILD": {"STATE": "smiling"}}}
    config = config_loader.load_config_for_package(_TEST_SUBPKG_CONFIG_PATH, "mom.child", custom_cfg)

    assert config["STATE"] == "smiling"
    assert config["LOCATION"] == "at home"


def test_config_validation_wrong_hierarchy():
    SIM_SET_KEY = "SIMULATION_SETTINGS"
    custom_cfg_wrong = {SIM_SET_KEY: {"TIMING": {"MIN_SYSTEM_TIMESTAMP": 2}}}
    (wrong, corrected, not_found) = config_loader.validate_custom_config([_TEST_CFG_PATH, _TEST_SUBPKG_CONFIG_PATH], custom_cfg_wrong)
    assert SIM_SET_KEY in wrong 
    assert isinstance(wrong[SIM_SET_KEY], str) # check that the key was marked
    EP_KEY = "EPLUS_ADAPTER"
    assert EP_KEY in corrected
    assert SIM_SET_KEY in corrected[EP_KEY] 
    assert isinstance(corrected[EP_KEY][SIM_SET_KEY], str)
    assert not_found == {}


def test_config_validation_not_existing():
    CO_SIM_KEY= "CO-SIMULATION"
    custom_cfg_not_existing = {CO_SIM_KEY: {"FMU": True}}
    custom_cfg = copy.deepcopy(custom_cfg_not_existing)
    custom_cfg.update({"HELLO": {"SUNSHINE": "warm"}})
    (wrong, corrected, not_found) = config_loader.validate_custom_config([_TEST_CFG_PATH, _TEST_SUBPKG_CONFIG_PATH], custom_cfg_not_existing)
    assert CO_SIM_KEY in wrong
    assert isinstance(wrong[CO_SIM_KEY], str) # check that the key was marked
    assert len(wrong) == 1
    assert corrected == {}
    assert CO_SIM_KEY in not_found
    assert len(not_found) == 1


def test_config_validation_duplicate_keys():
    with pytest.raises(config_loader.DuplicateConfigKeyException):
        custom_cfg_dict = config_loader.load_config_full(_TEST_DUPLICATES_CONFIG_PATH)


def test_get_default_config_files():
    all_config_files = config_loader.get_config_file_pathes('cesarp', recursive=True)
    expected_config_entry = "retrofit_embodied_config.yml"
    assert any(str(cfg_file).find(expected_config_entry) for cfg_file in all_config_files)    