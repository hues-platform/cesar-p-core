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
import pint
import copy

import cesarp.common
from cesarp.model.WindowConstruction import WindowConstruction, WindowGlassConstruction, WindowFrameConstruction, WindowShadingMaterial
from cesarp.model.Construction import Construction
from cesarp.model.BuildingElement import BuildingElement
from cesarp.model.BuildingConstruction import BuildingConstruction

from cesarp.retrofit.BuildingElementsRetrofitter import BuildingElementsRetrofitter

from tests.test_helpers.mock_objects_generator import bldg_shape_detailed_test_site_fid2

SUFFIX_RETROFITTED = "RETROFITTED"

def get_win_constr(name_glass, name_frame):
    return WindowConstruction(
        glass=WindowGlassConstruction(name_glass, None, None, None),
        frame=WindowFrameConstruction(name_frame, None, None, None, None, None, None, None),
        shade=WindowShadingMaterial.create_empty_unavailable()
        )

def get_constr(name):
    return Construction(name, None, None)

class MockRetrofitter():
    def get_retrofitted_construction(self, construction: Construction):
        return get_constr(construction.name + "_" + SUFFIX_RETROFITTED)

    def get_retrofitted_window(self, WindowConstruction):
        return get_win_constr("TEST_GLASS_" + SUFFIX_RETROFITTED, "TEST_FRAME")

    def get_retrofit_target_info(self):
        return "MockRetrofit"

class MockCostAndEmissions():
    def __init__(self, ureg: pint.UnitRegistry):
        self.ureg = ureg

    def get_costs_for_window_retrofit(self, window_constr: WindowConstruction) -> pint.Quantity:
        return 200 * self.ureg.CHF / self.ureg.m ** 2

    def get_costs_for_construction_retrofit(self, constr: Construction) -> pint.Quantity:
        return 200 * self.ureg.CHF / self.ureg.m**2

    def get_constr_ret_emb_co2(self, constr: Construction) -> pint.Quantity:
        return 5 * self.ureg.kg * self.ureg.CO2eq / self.ureg.m**2

    def get_constr_ret_emb_non_renewable_pen(self, constr: Construction) -> pint.Quantity:
        return 0.05 * self.ureg.MJ * self.ureg.Oileq / self.ureg.m ** 2

    def get_win_ret_glass_emb_co2(self, win_constr: WindowConstruction) -> pint.Quantity:
        return 7 * self.ureg.kg * self.ureg.CO2eq / self.ureg.m ** 2

    def get_win_ret_frame_emb_co2(self, win_constr: WindowConstruction) -> pint.Quantity:
        return 22 * self.ureg.kg * self.ureg.CO2eq / self.ureg.m ** 2

    def get_win_ret_glass_emb_non_renewable_pen(self, win_constr: WindowConstruction) -> pint.Quantity:
        return 0.5 * self.ureg.MJ * self.ureg.Oileq / self.ureg.m ** 2

    def get_win_ret_frame_emb_non_renewable_pen(self, win_constr: WindowConstruction) -> pint.Quantity:
        return 3 * self.ureg.MJ * self.ureg.Oileq / self.ureg.m ** 2


@pytest.fixture
def mock_bldg_construction():
    return BuildingConstruction(window_construction=get_win_constr("TEST_GLASS", "TEST_FRAME"),
                                roof_constr=get_constr("TEST_ROOF"),
                                groundfloor_constr=get_constr("TEST_GROUNDFLOOR"),
                                wall_constr=get_constr("TEST_WALL"),
                                internal_ceiling_constr=None,
                                glazing_ratio=None,
                                infiltration_rate=None,
                                infiltration_profile=None,
                                installation_characteristics=None)


def test_simple_construction_retrofitter(mock_bldg_construction,
                                         bldg_shape_detailed_test_site_fid2):
    ureg = cesarp.common.init_unit_registry()
    my_retrofitter = BuildingElementsRetrofitter(ureg)
    mock_cost_and_emission_calc = MockCostAndEmissions(ureg)
    my_retrofitter.emissions = mock_cost_and_emission_calc
    my_retrofitter.costs = mock_cost_and_emission_calc
    my_retrofitter.construction_retrofitter = MockRetrofitter()
    my_retrofitter.set_bldg_elems_to_retrofit([BuildingElement.ROOF, BuildingElement.WINDOW, BuildingElement.WALL])
    orig_bldg_constr = copy.deepcopy(mock_bldg_construction)
    my_retrofitter.retrofit_bldg_construction(33, mock_bldg_construction, bldg_shape_detailed_test_site_fid2)

    assert orig_bldg_constr.roof_constr.name != mock_bldg_construction.roof_constr.name
    assert orig_bldg_constr.window_constr.name != mock_bldg_construction.window_constr.name
    assert mock_bldg_construction.infiltration_rate == ureg("0.1 ACH")
    assert orig_bldg_constr.wall_constr.name != mock_bldg_construction.wall_constr.name
    assert orig_bldg_constr.groundfloor_constr == mock_bldg_construction.groundfloor_constr

    assert len(my_retrofitter.retrofit_log.my_log_entries) == 3