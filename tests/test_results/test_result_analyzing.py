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
from pathlib import Path

import cesarp.common
from cesarp.results.ResultProcessor import ResultProcessor
from cesarp.model.EnergySource import EnergySource

@pytest.fixture
def example_res_folders():
    return \
        {
            307143: os.path.dirname(__file__) / Path("./testfixture/eplus_output/fid_307143"),
            1150082: os.path.dirname(__file__) / Path("./testfixture/eplus_output/fid_1150082"),
        }


def test_basic_running(example_res_folders):
    ureg = cesarp.common.init_unit_registry()
    res_processor = ResultProcessor(ureg)
    for fid, res_folder in example_res_folders.items():
        res_processor.process_results_for(fid, res_folder, EnergySource.HEATING_OIL, EnergySource.HEATING_OIL, 2015)

    the_res = res_processor.get_all_results()
    co2_total = the_res.loc[307143,"CO2eq * kilogram / meter ** 2 / year"]["Total CO2"]
    assert co2_total == pytest.approx(63.405, abs=0.01)




