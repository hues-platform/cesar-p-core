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
import os
import pytest
import pandas
from pathlib import Path
import cesarp.common
from cesarp.graphdb_access.BldgElementConstructionReader import BldgElementConstructionReader
from cesarp.graphdb_access.GraphDBArchetypicalConstructionFactory import GraphDBArchetypicalConstructionFactory
from cesarp.graphdb_access.LocalFileReader import LocalFileReader
from cesarp.graphdb_access.GraphDBReader import GraphDBReader
from cesarp.graphdb_access.GraphDataException import GraphDataException
from cesarp.model.BuildingElement import BuildingElement
from cesarp.model.EnergySource import EnergySource
from cesarp.model.Layer import LayerFunction, Layer
from cesarp.model.Construction import Construction


@pytest.fixture
def local_db_access():
    ureg = cesarp.common.init_unit_registry()
    local_reader = LocalFileReader()
    reader = BldgElementConstructionReader(local_reader, ureg)
    return reader

@pytest.fixture
def remote_db_access():
    """
    you can replace local_db_access with remote_db_access if you whish to test remote db access
    make sure to set GRAPHDB_USER and GRAPHDB_PASSWORD in your environment variables
    """
    ureg = cesarp.common.init_unit_registry()
    db_access = GraphDBReader()
    reader = BldgElementConstructionReader(db_access, ureg)
    return reader

def test_get_construction_archetype(local_db_access):
    ureg = local_db_access.ureg
    myArchetype = local_db_access.get_bldg_elem_construction_archetype(archetype_uri="http://uesl_data/sources/archetypes/2006_SFH_Archetype")
    assert len(myArchetype.walls) == 5
    for wall in myArchetype.walls:
        assert wall.bldg_element == BuildingElement.WALL
        if "Wall2006_wood_construction" in wall.name:
            assert len(wall.layers) == 3
            assert [layer.thickness.m for layer in wall.layers] == [0.024, 0.13, 0.12]
            assert wall.layers[0].material.conductivity == ureg.Quantity("0.13 W / kelvin / meter")

def test_get_ageclass_for_archetype(local_db_access):
    ac = local_db_access.get_age_class_of_archetype("http://uesl_data/sources/archetypes/1918_SFH_Archetype")
    assert ac.min_age == None
    assert ac.max_age == 1918

def test_default_construction(local_db_access):
    myArchetype = local_db_access.get_bldg_elem_construction_archetype(archetype_uri="http://uesl_data/sources/archetypes/2006_SFH_Archetype")

    default_wall = local_db_access.get_default_construction(myArchetype.walls)
    assert default_wall.short_name == "Wall2006_concrete_high_ins"

    default_wall = local_db_access.get_default_construction(myArchetype.walls, "not_existing_archetype_name")
    assert default_wall.short_name == "Wall2006_concrete_high_ins"

    default_roof = local_db_access.get_default_construction(myArchetype.roofs)
    assert default_roof.short_name == "Roof2006_concrete_med_ins"

    default_ground = local_db_access.get_default_construction(myArchetype.grounds)
    assert default_ground.short_name == "Ground2006_concrete_slab_medium"

    default_window = local_db_access.get_default_construction(myArchetype.windows)
    assert default_window.short_name == "Window2006_LowE_Krypton_Double"


    default_constructions = open(str(os.path.dirname(__file__) / Path("list_with_default_constr.txt")), "r").read()
    for year in [1918, 1948, 1978, 1994, 2001, 2006, 2009, 2014, 2015]:
        myArchetype = local_db_access.get_bldg_elem_construction_archetype(f"http://uesl_data/sources/archetypes/{year}_SFH_Archetype")
        default_wall = local_db_access.get_default_construction(myArchetype.walls, myArchetype.short_name)
        assert default_wall.short_name in default_constructions
        default_roof = local_db_access.get_default_construction(myArchetype.roofs, myArchetype.short_name)
        assert default_roof.short_name in default_constructions
        default_ground = local_db_access.get_default_construction(myArchetype.grounds, myArchetype.short_name)
        assert default_ground.short_name in default_constructions
        default_window = local_db_access.get_default_construction(myArchetype.windows, myArchetype.short_name)
        assert default_window.short_name in default_constructions


def test_retrofit_construction(local_db_access):
    myArchetype = local_db_access.get_bldg_elem_construction_archetype(archetype_uri="http://uesl_data/sources/archetypes/2006_SFH_Archetype")

    retrofitted_window = local_db_access.get_retrofitted_construction(myArchetype.windows[0])
    assert retrofitted_window.retrofitted == True

    wall = myArchetype.walls[0]
    retrofitted_wall = local_db_access.get_retrofitted_construction(wall)
    assert local_db_access.get_u_value(retrofitted_wall) < local_db_access.get_u_value(wall)

    assert retrofitted_wall.layers[1].function == LayerFunction.INSULATION_OUTSIDE

    assert myArchetype.walls[3].short_name == "Wall2006_stone_cavity_woodplank"
    assert local_db_access.get_retrofitted_construction(myArchetype.walls[3]).layers[2].function == LayerFunction.INSULATION_OUTSIDE_BACK_VENTILATED

    myArchetype = local_db_access.get_bldg_elem_construction_archetype(archetype_uri="http://uesl_data/sources/archetypes/2009_SFH_Archetype")
    with pytest.raises(LookupError):
        retrofitted_window = local_db_access.get_retrofitted_construction(myArchetype.windows[0]).short_name



def test_win_glass_emissions(local_db_access: BldgElementConstructionReader):
    ureg = local_db_access.ureg
    win_glass_no_emissions_uri = "http://uesl_data/sources/archetypes/windows/Window1994_LowE_Xenon_Double"
    win_glass_no_emissions = local_db_access.get_win_glass_constr_for(win_glass_no_emissions_uri)
    assert win_glass_no_emissions.emb_non_ren_primary_energy_per_m2 == None
    assert win_glass_no_emissions.emb_co2_emission_per_m2 == None
    with pytest.raises(GraphDataException):
        xx = local_db_access.get_win_glass_constr_for(win_glass_no_emissions_uri, emb_emissions_needed=True)

    win_glass_with_emissions_uri = "http://uesl_data/sources/archetypes/windows/Window2014_DoubleLowE_Air_Triple"
    win_glass_with_emissions = local_db_access.get_win_glass_constr_for(win_glass_with_emissions_uri)
    assert win_glass_with_emissions.emb_co2_emission_per_m2.u == ureg.kg * ureg.CO2eq / ureg.m2
    assert win_glass_with_emissions.emb_co2_emission_per_m2.m == pytest.approx(57.6)
    assert win_glass_with_emissions.emb_non_ren_primary_energy_per_m2.u == ureg.MJ * ureg.Oileq / ureg.m2
    assert win_glass_with_emissions.emb_non_ren_primary_energy_per_m2.m == 837


def test_material_properties_not_found(local_db_access):
    with pytest.raises(ValueError):
        material = local_db_access.get_opaque_material("http://uesl_data/sources/materials/no_material")


def test_glazing_and_infiltration(local_db_access):
    # TODO assert units
    assert local_db_access.get_glazing_ratio("http://uesl_data/sources/archetypes/2015_SFH_Archetype")._max == 0.38
    assert local_db_access.get_infiltration_rate("http://uesl_data/sources/archetypes/1948_SFH_Archetype") == \
           local_db_access.ureg.Quantity("0.71125 ACH")


def test_construction_factory():
    ureg = cesarp.common.init_unit_registry()
    local_reader = LocalFileReader()
    custom_config = {"GRAPHDB_ACCESS": {"ARCHETYPES": {"1948_SFH_ARCHETYPE": {"DEFAULT_CONSTRUCTION_SPECIFIC": {
        "ACTIVE": False}}}}}

    factory = GraphDBArchetypicalConstructionFactory({1:2001, 2:1950, 3:2018, 4:2017, 5:2019},
                                                     {1:EnergySource.DHW_OTHER, 2:EnergySource.DHW_OTHER, 3:EnergySource.DHW_OTHER, 4:EnergySource.DHW_OTHER, 5:EnergySource.ELECTRICITY},
                                                     {fid: EnergySource.HEATING_OTHER for fid in range(1, 6)},
                                                     local_reader,
                                                     ureg,
                                                     custom_config)
    archetype2001 = factory.get_archetype_for(1)
    inf_rate = archetype2001.get_infiltration_rate()
    assert inf_rate.u == ureg.ACH
    assert inf_rate.m == 0.39125
    assert archetype2001.get_glazing_ratio().m == 0.27
    assert archetype2001.get_wall_construction().short_name == "Wall2001_concrete_med_ins"

    archetype1948 = factory.get_archetype_for(2)
    assert archetype1948.get_wall_construction().short_name == "Wall1978_sandstone_heavy"
    win_constr = archetype1948.get_window_construction()
    assert win_constr.glass.short_name == "Window1978_StdAirIns_Double"
    assert win_constr.shade.short_name == "Shade0101"
    assert factory.get_archetype_for(3) == factory.get_archetype_for(4)
    assert factory.get_archetype_for(4) != factory.get_archetype_for(5)
    assert factory.get_archetype_for(4).get_installation_characteristics() != factory.get_archetype_for(5).get_installation_characteristics()

def test_LayerFunction_mapping(local_db_access):
    layer_function = pandas.DataFrame(columns=["Construction", "Layer", "Function", "Material", "Material "
                                                                                                "Conductivity"])
    filename = str(os.path.dirname(__file__) / Path("ressources/construction_layer_LayerFunctions.csv"))
    layer_function_lookup = pandas.read_csv(filename)
    for year in [1918, 1948, 1978, 1994, 2001, 2006, 2009, 2014, 2015]:
        myArchetype = local_db_access.get_bldg_elem_construction_archetype(f"http://uesl_data/sources/archetypes/{year}_SFH_Archetype")
        for construction in myArchetype.walls:
            construction = local_db_access.get_retrofitted_construction(construction)
            for layer in construction.layers:
                layer_function.loc[len(layer_function.index)] = [construction.short_name, layer.short_name, str(layer.function),
                                                                 layer.material.short_name,
                                                                 layer.material.conductivity.m]
        for construction in myArchetype.grounds:
            construction = local_db_access.get_retrofitted_construction(construction)
            for layer in construction.layers:
                layer_function.loc[len(layer_function.index)] = [construction.short_name, layer.short_name, str(layer.function),
                                                                 layer.material.short_name, layer.material.conductivity.m]
        for construction in myArchetype.roofs:
            construction = local_db_access.get_retrofitted_construction(construction)
            for layer in construction.layers:
                layer_function.loc[len(layer_function.index)] = [construction.short_name, layer.short_name,
                                                                 str(layer.function),
                                                                 layer.material.short_name, layer.material.conductivity.m]
    pandas.testing.assert_frame_equal(layer_function, layer_function_lookup, check_dtype=False)

    myArchetype = local_db_access.get_bldg_elem_construction_archetype("http://uesl_data/sources/archetypes/1948_SFH_Archetype")
    wall_layer = Layer("Test_Layer", local_db_access.ureg.Quantity("0.1 m"), myArchetype.walls[3].layers[2].material)
    wall = Construction("Test_Wall", [wall_layer], BuildingElement.WALL)
    wall = local_db_access.set_layer_functions(wall)
    assert wall.layers[0].function == LayerFunction.INSULATION_OUTSIDE

def test_shading_material(local_db_access: BldgElementConstructionReader):
    shading = local_db_access.get_window_shading_constr("http://uesl_data/sources/archetypes/1918_SFH_Archetype")
    ureg = local_db_access.ureg
    assert(shading.name == "Shade0101")
    assert(shading.is_shading_available)
    assert(type(shading.airflow_permeability) == float)
    assert(shading.conductivity.u == ureg.W / ureg.m / ureg.K)
    assert(shading.solar_reflectance.u == ureg.solar_reflectance)
    assert(shading.thickness.u == ureg.m)
    assert(shading.airflow_permeability == pytest.approx(0))
    assert(shading.solar_transmittance.m == pytest.approx(0.31))
