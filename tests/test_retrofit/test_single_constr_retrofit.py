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
import cesarp.common
from cesarp.model.Construction import Construction, BuildingElement
from cesarp.model.OpaqueMaterial import OpaqueMaterial
from cesarp.model.Layer import Layer, LayerFunction
from cesarp.graphdb_access.ConstructionRetrofitter import ConstructionRetrofitter
from cesarp.graphdb_access.GraphDBFacade import GraphDBFacade

@pytest.fixture
def mock_opaque_construction():
    ureg = cesarp.common.init_unit_registry()
    render = OpaqueMaterial(name="render",
                             density = 1100 * ureg.kg / ureg.m**3,
                             roughness = None,
                             solar_absorptance = None,
                             specific_heat = None,
                             thermal_absorptance = None,
                             conductivity=None,
                             visible_absorptance = None,
                             co2_emission_per_kg = 0.1 * ureg.kg * ureg.CO2eq / ureg.kg,
                             non_renewable_primary_energy_per_kg = 1.7 * ureg.MJ * ureg.Oileq / ureg.kg)
    isolation = OpaqueMaterial(name="mineral_wool",
                             density = 96 * ureg.kg / ureg.m**3,
                             roughness = None,
                             solar_absorptance = None,
                             specific_heat = None,
                             thermal_absorptance = None,
                             conductivity=None,
                             visible_absorptance = None,
                             co2_emission_per_kg = 0.3 * ureg.kg * ureg.CO2eq / ureg.kg,
                             non_renewable_primary_energy_per_kg = 4.9 * ureg.MJ * ureg.Oileq / ureg.kg)

    layer1 = Layer(name="zz", retrofitted=False, thickness=0.1 * ureg.m, material=render, function=LayerFunction.INSULATION_INSIDE)
    layer2 = Layer(name="yy", retrofitted=True, thickness=0.5 * ureg.m, material=isolation, function=LayerFunction.INSULATION_OUTSIDE)
    layer3 = Layer(name="xx", retrofitted=False, thickness=0.1 * ureg.m, material=render, function=LayerFunction.INSIDE_FINISH)
    return Construction(name="testconstr", layers=[layer1, layer2, layer3], bldg_element=BuildingElement.WALL)


@pytest.fixture
def constr_retrofitter():
    return GraphDBFacade(cesarp.common.init_unit_registry()).get_graph_construction_retrofitter()


def test_get_construction_retrofit(constr_retrofitter):
    myConstr = Construction(layers=[], name="http://uesl_data/sources/archetypes/walls/Wall2006_wood_construction",
                            bldg_element=BuildingElement.WALL)
    retrofitted_constr = constr_retrofitter.get_retrofitted_construction(myConstr)
    assert retrofitted_constr.short_name == "Wall2006_wood_construction_R_SIA-380-1_MinReq"


def test_get_construction_not_found(constr_retrofitter):
    myConstr = Construction(layers=[], name="http://uesl_data/sources/archetypes/walls/Wall2006_concrete_construction",
                            bldg_element=BuildingElement.WALL)
    with pytest.raises(LookupError):
        retrofitted_constr = constr_retrofitter.get_retrofitted_construction(myConstr)


def test_construction(mock_opaque_construction):
    assert mock_opaque_construction.retrofitted == True


