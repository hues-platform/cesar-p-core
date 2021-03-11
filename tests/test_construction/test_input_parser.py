# coding=utf-8
#
# Copyright (c) 2021, Empa, Leonie Fierz, Aaron Bojarski, Ricardo Parreira da Silva, Sven Eggimann.
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
from pathlib import Path
import pytest

import cesarp.common
from cesarp.common.AgeClass import AgeClass
from cesarp.idf_constructions_db_access import input_parser

__test_config_path = os.path.dirname(__file__) / Path("./testfixture/test_config.yml")

@pytest.fixture
def ureg():
    return cesarp.common.init_unit_registry()

def test_glazing_ratio(ureg):
    cfg_glazing = cesarp.common.config_loader.load_config_for_package(__test_config_path, "cesarp.construction")["INPUT_FILES"]["GLAZING_RATIO_PER_AGE_CLASS"]
    cfg_glazing["PATH"] = os.path.dirname(__file__) / Path(cfg_glazing["PATH"])
    glazing_ratio = input_parser.read_glazing_ratio(cfg_glazing, cesarp.common.init_unit_registry())
    ac_first = AgeClass(max_age=1918)
    ac_last = AgeClass(min_age=2015)
    assert glazing_ratio.loc[ac_first, "min"] == 0.1 * ureg.dimensionless
    assert glazing_ratio.loc[ac_first, "max"] == 0.16 * ureg.dimensionless
    assert glazing_ratio.loc[ac_last, "min"] == 0.23 * ureg.dimensionless
    assert glazing_ratio.loc[ac_last, "max"] == 0.38 * ureg.dimensionless


def test_infiltration_rate(ureg):
    cfg_inf = cesarp.common.config_loader.load_config_for_package(__test_config_path, "cesarp.construction")["INPUT_FILES"]["INFILTRATION_PER_AGE_CLASS"]
    cfg_inf["PATH"] = os.path.dirname(__file__) / Path(cfg_inf["PATH"])
    infiltration_rate = input_parser.read_infiltration_rate(cfg_inf, cesarp.common.init_unit_registry())
    assert infiltration_rate.loc[AgeClass(max_age=1918), "ACH_normal_pressure"] == 0.55 * ureg.ACH
    assert infiltration_rate.loc[AgeClass(min_age=2015), "ACH_normal_pressure"] == 0.1 * ureg.ACH
