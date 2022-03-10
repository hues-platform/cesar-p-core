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
import cesarp.common
import pytest
from tests.test_helpers.mock_objects_generator import get_mock_wall_construction_for_emission_calc
from cesarp.retrofit.embodied.RetrofitEmbodiedEmissions import RetrofitEmbodiedEmissions
from cesarp.model.WindowConstruction import WindowConstruction, WindowGlassConstruction

def test_retrofit_embodied_emissions_lookup_opaque_bldg_elem():
    ureg = cesarp.common.init_unit_registry()
    mock_wall = get_mock_wall_construction_for_emission_calc(ureg)
    ret_em = RetrofitEmbodiedEmissions(ureg)
    co2_res_unit = ureg.kg * ureg.CO2eq / ureg.m**2
    pen_res_unit = ureg.MJ * ureg.Oileq / ureg.m**2
    density_l1_l3 = 1100 * ureg.kg / ureg.m**3
    density_l2 = 96 * ureg.kg / ureg.m**3
    co2_l1_l3 = 5 * ureg.kg * ureg.CO2eq / ureg.kg * density_l1_l3
    co2_l2 = 3 * ureg.kg * ureg.CO2eq / ureg.kg * density_l2
    pen_l1_l3 = 2 * ureg.MJ * ureg.Oileq / ureg.kg * density_l1_l3
    pen_l2 = 6 * ureg.MJ * ureg.Oileq / ureg.kg * density_l2
    expected_pen = ( 0.5 * ureg.m * pen_l2 + 0.1 * ureg.m * pen_l1_l3).to(pen_res_unit)
    expected_co2 = ( 0.5 * ureg.m * co2_l2 + 0.1 * ureg.m * co2_l1_l3).to(co2_res_unit)

    res_pen = ret_em.get_constr_ret_emb_non_renewable_pen(mock_wall)
    assert res_pen.u == pen_res_unit
    assert res_pen.m == pytest.approx(expected_pen.m)
    res_co2 = ret_em.get_constr_ret_emb_co2(mock_wall)
    assert res_co2.u == co2_res_unit
    assert res_co2.m == pytest.approx(expected_co2.m)

def test_win_glass_emissions():
    ureg = cesarp.common.init_unit_registry()
    ret_em = RetrofitEmbodiedEmissions(ureg)
    win_glass_emb_co2 = 32.2  * ureg.kg * ureg.CO2eq / ureg.m ** 2
    test_win = WindowConstruction(
        frame=None,
        glass=WindowGlassConstruction(name="http://uesl_data/sources/archetypes/windows/Window2001_LowE_Xenon_Double",
                                      layers= None,
                                      emb_co2_emission_per_m2 = win_glass_emb_co2,
                                      emb_non_ren_primary_energy_per_m2 = None
                                      ),
        shade=None
    )
    assert ret_em.get_win_ret_glass_emb_co2(test_win) == win_glass_emb_co2
    assert ret_em.get_win_ret_glass_emb_non_renewable_pen(test_win) == None
