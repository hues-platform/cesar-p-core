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
from cesarp.eplus_adapter.eplus_res_surface_solar_potential import collect_surface_geometries
from cesarp.eplus_adapter.eplus_eso_results_handling import collect_multi_entry_annual_result
from cesarp.eplus_adapter.eplus_res_surface_solar_potential import solar_potential_for_building

@pytest.fixture
def test_eplus_out():
    return os.path.dirname(__file__) / Path("testfixture") / Path("solar_potential")

@pytest.fixture
def test_idf():
    return os.path.dirname(__file__) / Path("testfixture") / Path("solar_potential")/ Path("solar_potential_test.idf")


def test_collect_surfaces(test_idf):
    surfaces_df = collect_surface_geometries(test_idf)
    assert len(surfaces_df.index) == 24
    assert surfaces_df.loc[1].to_dict() == {'name': 'ZONEFLOOR0_WALL_0', 'azimuth': 15.69801079636362, 'tilt': 90.0,
                                            'sun_exposure': 'SunExposed', 'area': 118.15745375539855}

def test_collect_radiation_per_surface(test_eplus_out):
    varname = "Surface Outside Face Incident Solar Radiation Rate per Area"
    surfaces_dict = collect_multi_entry_annual_result(test_eplus_out,varname)
    assert  surfaces_dict['ZONEFLOOR0_WALL_0'] == pytest.approx(23.843591381791693)


def test_solar_potential(test_idf,test_eplus_out):
    surface_insolation_df = solar_potential_for_building(test_idf, test_eplus_out)
    assert len(surface_insolation_df.index) == 5

    insolatio_sum_E = surface_insolation_df.loc[surface_insolation_df['cardinal_orientation']=='E']['insolation_kwh','sum'].iloc[0]
    assert insolatio_sum_E == pytest.approx(47476.704)

