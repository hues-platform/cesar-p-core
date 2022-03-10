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
from cesarp.retrofit.embodied.ConstructionRetrofitCosts import ConstructionRetrofitCosts
from cesarp.model.WindowConstruction import WindowConstruction, WindowGlassConstruction
from cesarp.model.Construction import Construction
from cesarp.model.BuildingElement import BuildingElement
from cesarp.model.Layer import Layer, LayerFunction

def test_window_costs():
    ureg = cesarp.common.init_unit_registry()
    retCosts = ConstructionRetrofitCosts(ureg, {})
    glass_constr = WindowGlassConstruction(
        "http://uesl_data/sources/archetypes/windows/Window2014_DoubleLowE_Air_Triple", None, None, None)
    ret_win = WindowConstruction(glass=glass_constr, frame=None, shade=None)
    assert retCosts.get_costs_for_window_retrofit(ret_win) == 1000 * ureg.CHF / ureg.m**2


def test_window_costs_not_defined():
    ureg = cesarp.common.init_unit_registry()
    retCosts = ConstructionRetrofitCosts(ureg, {})
    glass_constr = WindowGlassConstruction(
        "http://uesl_data/sources/archetypes/windows/AFancyWindow", None, None, None)
    ret_win = WindowConstruction(glass=glass_constr, frame=None, shade=None)
    assert retCosts.get_costs_for_window_retrofit(ret_win) == 0 * ureg.CHF / ureg.m**2

def test_constr_costs():
    ureg = cesarp.common.init_unit_registry()
    my_constr = Construction(name="test_constr",
                             layers=[
                                 Layer(name="outside",
                                       thickness=0.02*ureg.m,
                                       material=None,
                                       function=LayerFunction.OUTSIDE_FINISH,
                                       retrofitted=True),
                                 Layer(name="insulation_new",
                                       thickness=0.05 * ureg.m,
                                       material=None,
                                       function=LayerFunction.INSULATION_OUTSIDE_BACK_VENTILATED,
                                       retrofitted=True),
                                 Layer(name="insulation_old",
                                       thickness=0.16 * ureg.m,
                                       material=None,
                                       function=LayerFunction.INSULATION_IN_BETWEEN,
                                       retrofitted=False),
                             ],
                             bldg_element=BuildingElement.WALL)

    retCosts = ConstructionRetrofitCosts(ureg, {})
    # test interpolation
    # extrapolation to 0m linear from 0 CHF to first entry
    expected_cost_layer2_5cm = (290 - 5 * 29) * ureg.CHF / ureg.m ** 2
    # interpolation between two thicknesses - linear
    expected_cost_layer2_19_5cm = 435 * ureg.CHF / ureg.m ** 2
    assert retCosts.get_costs_for_construction_retrofit(my_constr) == expected_cost_layer2_5cm
    my_constr.layers[1].thickness = 0.195 * ureg.m
    assert retCosts.get_costs_for_construction_retrofit(my_constr) == expected_cost_layer2_19_5cm
    # tests when two layers have retrofit costs
    expected_cost_layer3_16cm = 90 * ureg.CHF / ureg.m ** 2
    my_constr.layers[2].retrofitted=True
    assert retCosts.get_costs_for_construction_retrofit(my_constr) == (expected_cost_layer2_19_5cm +
                                                                       expected_cost_layer3_16cm)