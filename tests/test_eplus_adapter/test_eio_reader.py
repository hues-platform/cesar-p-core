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
from cesarp.eplus_adapter.EPlusEioResultAnalyzer import EPlusEioResultAnalyzer

@pytest.fixture
def eio_reader():
    ureg = cesarp.common.init_unit_registry()
    eplus_sample_res = os.path.dirname(__file__) / Path("testfixture")/ Path("eplus_output")/Path("fid_307143")
    return EPlusEioResultAnalyzer(eplus_sample_res,ureg=ureg)

@pytest.fixture
def ureg():
    return cesarp.common.init_unit_registry()

def test_total_floor_area(eio_reader, ureg):
    assert eio_reader.get_total_floor_area() == 1307.24 * ureg.m**2
