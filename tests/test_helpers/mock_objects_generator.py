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
from cesarp.geometry.GeometryBuilderFactory import GeometryBuilderFactory
from cesarp.geometry.csv_input_parser import read_sitevertices_from_csv
import os
from pathlib import Path
import pint

import cesarp.common
from cesarp.model.OpaqueMaterial import OpaqueMaterial
from cesarp.model.Layer import LayerFunction, Layer
from cesarp.model.Construction import Construction
from cesarp.model.BuildingElement import BuildingElement
from cesarp.model.WindowConstruction import WindowConstruction, WindowFrameConstruction, WindowGlassConstruction
from cesarp.model.TransparentMaterial import TransparentMaterial
from cesarp.model.Gas import Gas


def get_mock_wall_construction_for_emission_calc(ureg: pint.UnitRegistry):
    render = OpaqueMaterial(name="render",
                            density=1100 * ureg.kg / ureg.m ** 3,
                            roughness=None,
                            solar_absorptance=None,
                            specific_heat=None,
                            thermal_absorptance=None,
                            conductivity=None,
                            visible_absorptance=None,
                            co2_emission_per_kg=5 * ureg.kg * ureg.CO2eq / ureg.kg,
                            non_renewable_primary_energy_per_kg=2 * ureg.MJ * ureg.Oileq / ureg.kg)
    isolation = OpaqueMaterial(name="mineral_wool",
                               density=96 * ureg.kg / ureg.m ** 3,
                               roughness=None,
                               solar_absorptance=None,
                               specific_heat=None,
                               thermal_absorptance=None,
                               conductivity=None,
                               visible_absorptance=None,
                               co2_emission_per_kg=3 * ureg.kg * ureg.CO2eq / ureg.kg,
                               non_renewable_primary_energy_per_kg=6 * ureg.MJ * ureg.Oileq / ureg.kg)

    # not a very realistic wall indeed... but enough for testing
    layer1 = Layer(name="zz", retrofitted=True, thickness=0.1 * ureg.m, material=render,
                   function=LayerFunction.OUTSIDE_FINISH)
    layer2 = Layer(name="yy", retrofitted=True, thickness=0.5 * ureg.m, material=isolation,
                   function=LayerFunction.INSULATION_OUTSIDE)
    layer3 = Layer(name="xx", retrofitted=False, thickness=0.1 * ureg.m, material=render,
                   function=LayerFunction.INSIDE_FINISH)
    return Construction(name="testconstr", layers=[layer1, layer2, layer3], bldg_element=BuildingElement.WALL)


def get_mock_window_construction_for_emission_calc(ureg: pint.UnitRegistry):
    glass = WindowGlassConstruction(
        name=None,
        layers=None,
        emb_co2_emission_per_kg=57.6 * ureg.kg * ureg.CO2eq / ureg.m ** 2,
        emb_non_ren_primary_energy_per_kg=837 * ureg.MJ * ureg.Oileq / ureg.m ** 2,
    )
    frame = WindowFrameConstruction(
        emb_co2_emission_per_m2 = 256  * ureg.kg * ureg.CO2eq / ureg.m**2,
        emb_non_ren_primary_energy_per_m2=3740 * ureg.MJ * ureg.Oileq / ureg.m**2
    )
    return WindowConstruction(name="winconstrtest", glass=glass, frame=frame)

@pytest.fixture
def bldg_shape_detailed_test_site_fid2():
    geom_fact = GeometryBuilderFactory(read_sitevertices_from_csv(
                                            os.path.dirname(__file__) / Path("./testfixture/SiteVertices_bldg_fid2.csv"),
                                            {'gis_fid': "TARGET_FID", 'height': "HEIGHT", 'x': 'POINT_X', 'y': 'POINT_Y'}
                                        ),
                                        {"GEOMETRY": {"NEIGHBOURHOOD": {"RADIUS": 0}}})
    geom_builder = geom_fact.get_geometry_builder(2, 0.16)
    return geom_builder.get_bldg_shape_detailed()

@pytest.fixture
def bldg_shape_detailed_non_rect_footprint():
    geom_fact = GeometryBuilderFactory(read_sitevertices_from_csv(
                                            os.path.dirname(__file__) / Path("./testfixture/SiteVertices_non_rectangular.csv"),
                                            {'gis_fid': "TARGET_FID", 'height': "HEIGHT", 'x': 'POINT_X', 'y': 'POINT_Y'}
                                        ),
                                        {"GEOMETRY": {"NEIGHBOURHOOD": {"RADIUS": 0}}})
    geom_builder = geom_fact.get_geometry_builder(22, 0.16)
    return geom_builder.get_bldg_shape_detailed()
