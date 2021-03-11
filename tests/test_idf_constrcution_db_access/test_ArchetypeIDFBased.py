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
import logging
import pytest
import cesarp.common
from cesarp.idf_constructions_db_access.ArchetypicalConstructionIDFBased import ArchetypicalConstructionIDFBased
from cesarp.construction.ListWithDefault import ListWithDefault
from cesarp.construction.MinMaxValue import MinMaxValue
from cesarp.model.BuildingConstruction import InstallationsCharacteristics, LightingCharacteristics
from cesarp.model.WindowConstruction import WindowFrameConstruction, WindowShadingMaterial
from cesarp.model.EnergySource import EnergySource

def test_archetype_equal():
    ureg = cesarp.common.init_unit_registry()
    logging.getLogger().setLevel(logging.DEBUG)
    myArchetype1 = ArchetypicalConstructionIDFBased(window_glass_constr_options=['window1.txt'],
                                                    window_glass_constr_default='window1.txt',
                                                    window_frame_construction=
                                                        WindowFrameConstruction(
                                                            name = "test",
                                                            short_name= "test",
                                                            frame_conductance= 9.5 * ureg.W / ureg.K / ureg.m**2,
                                                            frame_solar_absorptance=0.5 * ureg.solar_absorptance,
                                                            frame_visible_absorptance = 0.3 * ureg.visible_absorptance,
                                                            outside_reveal_solar_absorptance = 0.25 * ureg.solar_absorptance,
                                                            emb_co2_emission_per_m2=2*ureg.kg*ureg.CO2eq/ureg.m**2,
                                                            emb_non_ren_primary_energy_per_m2=0.4*ureg.MJ*ureg.Oileq/ureg.m**2
                                                            ),
                                                    window_shade_constr=WindowShadingMaterial.create_empty_unavailable(),
                                                    roof_constr_options=['roof1.txt'],
                                                    roof_constr_default='roof1.txt',
                                                    groundfloor_constr_options=['groundfloor1.txt'],
                                                    groundfloor_constr_default='groundfloor1.txt',
                                                    wall_constr_options = ['wall1.txt'],
                                                    wall_constr_default='wall1.txt',
                                                    internal_ceiling_constr='InternalCeiling.idf',
                                                    external_constr_materials_idf='material_for_bldg_elems_exterior.idf',
                                                    internal_constr_materials_idf='material_for_bldg_elems_interior.idf',
                                                    glazing_ratio_min=0.12 * ureg.dimensionless,
                                                    glazing_ratio_max=0.2 * ureg.dimensionless,
                                                    infiltration_rate=0.33 * ureg.ACH,
                                                    infiltration_fraction_profile_value=1,
                                                    installations_characteristics=InstallationsCharacteristics(fraction_radiant_from_activity=0.3,
                                                                                                               lighting_characteristics=
                                                                                                                    LightingCharacteristics(
                                                                                                                        return_air_fraction=0.4,
                                                                                                                        fraction_radiant=0.45,
                                                                                                                        fraction_visible = 0.2
                                                                                                                    ),
                                                                                                                dhw_fraction_lost=1,
                                                                                                                electric_appliances_fraction_radiant=0.75,
                                                                                                               e_carrier_dhw=EnergySource.ELECTRICITY,
                                                                                                               e_carrier_heating=EnergySource.HEATING_OIL))

    # use constructor withou parameter names to avoid unintended change in order of constructor parameters
    myArchetype2 = ArchetypicalConstructionIDFBased(['window1.txt'],
                                                    'window1.txt',
                                                    WindowFrameConstruction(
                                                        name="test",
                                                        short_name="test",
                                                        frame_conductance=9.5 * ureg.W / ureg.K / ureg.m ** 2,
                                                        frame_solar_absorptance=0.5 * ureg.solar_absorptance,
                                                        frame_visible_absorptance=0.3 * ureg.visible_absorptance,
                                                        outside_reveal_solar_absorptance=0.25 * ureg.solar_absorptance,
                                                        emb_co2_emission_per_m2=2*ureg.kg*ureg.CO2eq/ureg.m**2,
                                                        emb_non_ren_primary_energy_per_m2=0.4*ureg.MJ*ureg.Oileq/ureg.m**2
                                                    ),
                                                    WindowShadingMaterial.create_empty_unavailable(),
                                                    ['roof1.txt'],
                                                    'roof1.txt',
                                                    ['groundfloor1.txt'],
                                                    'groundfloor1.txt',
                                                    ['wall1.txt'],
                                                    'wall1.txt',
                                                    'InternalCeiling.idf',
                                                    'material_for_bldg_elems_exterior.idf',
                                                    'material_for_bldg_elems_interior.idf',
                                                    0.12 * ureg.dimensionless,
                                                    0.2 * ureg.dimensionless,
                                                    0.33 * ureg.ACH,
                                                    1,
                                                    InstallationsCharacteristics(0.3,
                                                                                 LightingCharacteristics(0.4,0.45,0.2),
                                                                                 1,
                                                                                 0.75,
                                                                                 EnergySource.ELECTRICITY,
                                                                                 EnergySource.HEATING_OIL))
    assert myArchetype1 == myArchetype2

    myArchetypeNotEqual = myArchetype2
    myArchetypeNotEqual.window_glass_constr = ListWithDefault(['dummy.txt'], 'dummy.txt')
    assert myArchetype1 != myArchetypeNotEqual

    myArchetypeNotEqual = myArchetype2
    myArchetypeNotEqual.roof_constr = ListWithDefault(['dummy.txt'], 'dummy.txt')
    assert myArchetype1 != myArchetypeNotEqual

    myArchetypeNotEqual = myArchetype2
    myArchetypeNotEqual.groundfloor_constr = ListWithDefault(['dummy.txt'], 'dummy.txt')
    assert myArchetype1 != myArchetypeNotEqual

    myArchetypeNotEqual = myArchetype2
    myArchetypeNotEqual.wall_constr = ListWithDefault(['dummy.txt'], 'dummy.txt')
    assert myArchetype1 != myArchetypeNotEqual

    myArchetypeNotEqual = myArchetype2
    myArchetypeNotEqual.internal_ceiling_constr = "dummy.idf"
    assert myArchetype1 != myArchetypeNotEqual

    myArchetypeNotEqual = myArchetype2
    myArchetypeNotEqual.infiltration_rate = 0.34
    assert myArchetype1 != myArchetypeNotEqual

    myArchetypeNotEqual = myArchetype2
    myArchetypeNotEqual.glazing_ratio = {'min': 0.11, 'max': 0.2}
    assert myArchetype1 != myArchetypeNotEqual

    myArchetypeNotEqual = myArchetype2
    myArchetypeNotEqual.window_frame_construction.name = "blabla"
    assert myArchetype1 != myArchetypeNotEqual

    myArchetypeNotEqual = myArchetype2
    myArchetypeNotEqual.exterior_constr_materials_idf = {'dummy': 0.0}
    assert myArchetype1 != myArchetypeNotEqual
    myArchetypeNotEqual = myArchetype2
    myArchetypeNotEqual.internal_constr_materials_idf = {'dummy': 0.0}
    assert myArchetype1 != myArchetypeNotEqual

def test_randomization():
    ureg = cesarp.common.init_unit_registry()
    myArchetype = ArchetypicalConstructionIDFBased(window_glass_constr_options = ['winX.txt', 'winY.txt', 'winZ.txt'],
                                                    window_glass_constr_default='winY.txt',
                                                    window_frame_construction=None,
                                                    window_shade_constr=None,
                                                    roof_constr_options=["roof1.txt", 'roof2.txt', 'roof3.txt', 'roof4.txt'],
                                                    roof_constr_default='roof1.txt',
                                                    groundfloor_constr_options=['groundfloor1.txt', 'groundfloor2.txt', 'groundfloor3.txt'],
                                                    groundfloor_constr_default='groundfloor1.txt',
                                                    wall_constr_options=['wall1.txt', 'wall2.txt', 'wall3.txt', 'wall4.txt'],
                                                    wall_constr_default='wall1.txt',
                                                    internal_ceiling_constr=None,
                                                    external_constr_materials_idf=None,
                                                    internal_constr_materials_idf=None,
                                                    glazing_ratio_min=0.12 * ureg.dimensionless,
                                                    glazing_ratio_max=0.2 * ureg.dimensionless,
                                                    infiltration_rate=0.33 * ureg.ACH,
                                                    infiltration_fraction_profile_value=1,
                                                    installations_characteristics=None)
    myArchetype.set_construction_selection_strategy(random_selection=True)
    _check_random(myArchetype.get_glazing_ratio)
    _check_random(myArchetype.get_window_construction)
    _check_random(myArchetype.get_roof_construction)
    _check_random(myArchetype.get_groundfloor_construction)
    _check_random(myArchetype.get_wall_construction)

def _check_random(the_method, nr_of_calls=10):
    random_vals = [the_method() for i in range(1, nr_of_calls)]
    assert len(set(random_vals)) > 1, f'no randomization, {nr_of_calls} times calling {the_method} returned always the same result, {random_vals[0]}'

def test_list_with_default_init_error():
    with pytest.raises(AssertionError):
        my_list_chooser = ListWithDefault(["a", "c", "x", "y"], "z")

def test_list_with_default_random_selection():
    my_list_chooser = ListWithDefault(["a", "c", "x", "y"], "a")
    assert my_list_chooser.get_value(random=False) == "a"
    random_selections = [my_list_chooser.get_value(random=True) for i in range(1, 1000)]
    nr_of_a = random_selections.count("a")
    nr_of_c = random_selections.count("c")
    nr_of_x = random_selections.count("x")
    nr_of_y = random_selections.count("y")
    tolerance = 40
    expected_nr_of_occurances = 1000/4
    assert abs(nr_of_a - expected_nr_of_occurances) < tolerance, f'a occured {nr_of_a} times, expected {expected_nr_of_occurances} +/- {tolerance}...'
    assert abs(nr_of_c - expected_nr_of_occurances) < tolerance, f'a occured {nr_of_a} times, expected {expected_nr_of_occurances} +/- {tolerance}...'
    assert abs(nr_of_x - expected_nr_of_occurances) < tolerance, f'a occured {nr_of_a} times, expected {expected_nr_of_occurances} +/- {tolerance}...'
    assert abs(nr_of_y - expected_nr_of_occurances) < tolerance, f'a occured {nr_of_a} times, expected {expected_nr_of_occurances} +/- {tolerance}...'

def test_random_min_max():
    ureg = cesarp.common.init_unit_registry()
    prc = ureg.percent
    randomizer = MinMaxValue(0.2 * prc, 0.9 * prc)
    assert randomizer.get_value(random=False) == 0.55 * prc
    random_vals = [randomizer.get_value(random=True) for i in range(1, 1000)]
    assert all([val.m >= 0.2 and val.m <= 0.9 for val in random_vals])
    assert abs(sum(random_vals)/len(random_vals)-randomizer.get_value(random=False)) < 0.02