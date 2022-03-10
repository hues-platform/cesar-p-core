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
"""
ATTENTION! With jsonpickle 1.4.1 something is broken with the object-reference id's. Thus we still use version 1.3!
Removing all pandas dataframes contained in the serialized object did not help.
"""
import pandas as pd
import pytest
import os
import shutil
from pathlib import Path

import cesarp.common
from cesarp.common.ScheduleFixedValue import ScheduleFixedValue
from cesarp.common.ScheduleFile import ScheduleFile
from cesarp.common.CesarpException import CesarpException
from cesarp.model.Construction import BuildingElement, Construction
from cesarp.model.Layer import Layer
from cesarp.model.OpaqueMaterial import OpaqueMaterial, OpaqueMaterialRoughness
from cesarp.model.TransparentMaterial import TransparentMaterial
from cesarp.model.WindowConstruction import WindowConstruction, WindowFrameConstruction, WindowGlassConstruction
from cesarp.model.BuildingModel import BuildingModel
from cesarp.model.BuildingConstruction import BuildingConstruction, InstallationsCharacteristics, LightingCharacteristics
from cesarp.model.BuildingOperation import BuildingOperation, Occupancy, InstallationOperation, HVACOperation, WindowShadingControl, NightVent
from cesarp.model.BuildingOperationMapping import BuildingOperationMapping
from cesarp.model.ShadingObjectConstruction import ShadingObjectConstruction
from cesarp.model.BldgShape import BldgShapeEnvelope, BldgShapeDetailed
from cesarp.model.Site import Site
from cesarp.model.SiteGroundTemperatures import SiteGroundTemperatures
from cesarp.model.EnergySource import EnergySource
from cesarp.model.BldgType import BldgType
from cesarp.model.WindowConstruction import WindowShadingMaterial
from cesarp.geometry.GeometryBuilderFactory import GeometryBuilderFactory
from cesarp.geometry.csv_input_parser import read_sitevertices_from_csv
from cesarp.eplus_adapter.CesarIDFWriter import CesarIDFWriter
import cesarp.manager.json_pickling
from cesarp.manager.BuildingContainer import BuildingContainer
from cesarp.eplus_adapter.eplus_error_file_handling import EplusErrorLevel

from dataclasses import dataclass

from cesarp.model.WindowLayer import WindowLayer

def get_schedule_file(filename, unit, type=cesarp.common.ScheduleTypeLimits.FRACTION()):
    return ScheduleFile(filename, type, 1, ",", 8760, 1, unit)

def config_sample_case():
    config = dict()
    config["MANAGER"] = dict()
    config["MANAGER"]["SITE_VERTICES_FILE"] = {"PATH": os.path.dirname(__file__) / Path("./testfixture/SiteVertices.csv")}
    config["MANAGER"]["BLDG_FID_FILE"] = {"PATH": os.path.dirname(__file__) / Path("./testfixture/BuildingInformation.csv")}
    config["MANAGER"]["BLDG_AGE_FILE"] = {"PATH": os.path.dirname(__file__) / Path("./testfixture/BuildingInformation.csv")}
    config["MANAGER"]["SINGLE_SITE"] = {"WEATHER_FILE": os.path.dirname(__file__) / Path("./testfixture/theWeather.epw")}
    config["MANAGER"]["BUILDING_OPERATION_SOURCE"] = "Fixed"
    return config


@pytest.fixture
def fixture_folder():
    return str(os.path.dirname(__file__) / Path("testfixture"))

@pytest.fixture
def sample_model_with_constr():
    ureg = cesarp.common.init_unit_registry()
    ground_temps = SiteGroundTemperatures(building_surface=18*ureg.degreeC,
                                          shallow=17*ureg.degreeC,
                                          deep=15*ureg.degreeC,
                                          ground_temp_per_month = [10, 11, 12, 13, 15, 20, 22, 25, 21, 19, 17, 12]*ureg.degreeC)
    site = Site(weather_file_path="theWeather.epw", site_ground_temperatures=ground_temps, simulation_year=2020)

    win_frame = WindowFrameConstruction(name="window_frame_fixed_cesar-p",
                                        short_name="window_frame_fixed_cesar-p",
                                        frame_conductance= 9.5 * ureg.W / ureg.m**2 / ureg.K,
                                        frame_solar_absorptance= 0.5 * ureg.dimensionless,
                                        frame_visible_absorptance= 0.5 * ureg.dimensionless,
                                        outside_reveal_solar_absorptance=0.5 * ureg.dimensionless,
                                        emb_co2_emission_per_m2=2 * ureg.kg*ureg.CO2eq/ureg.m**2,
                                        emb_non_ren_primary_energy_per_m2=0.5*ureg.MJ*ureg.Oileq/ureg.m**2)

    win_shade = WindowShadingMaterial(
                True,
                "Shade0101",
                ureg("0.31 solar_transmittance"),
                ureg("0.5 solar_reflectance"),
                ureg("0.31 visible_transmittance"),
                ureg("0.5 visible_reflectance"),
                ureg("0.9 infrared_hemispherical_emissivity"),
                ureg("0.0 infrared_transmittance"),
                ureg("0.9 W/(m*K)"),
                ureg("0.001 m"),
                ureg("0.1 m"),
                0, 0, 0, 0,
                0
            )

    test_opaque_material = OpaqueMaterial(
                           "material",
                           ureg("10 kg/m3"),
                           OpaqueMaterialRoughness.ROUGH,
                           ureg("0.9 solar_absorptance"),
                           ureg("1200 J/K/kg"),
                           ureg("0.9 thermal_absorptance"),
                           ureg("0.9 W/(m*K)"),
                           ureg("0.9 visible_absorptance")
                           )
    test_transparent_material = TransparentMaterial(
                           "glass_material",
                           ureg("0.9 back_side_infrared_hemispherical_emissivity"),
                           ureg("0.9 back_side_solar_reflectance"),
                           ureg("0.9 back_side_visible_reflectance"),
                           ureg("0.9 W/(m*K)"),
                           ureg("1.0 dirt_correction_factor"),
                           ureg("0.9 front_side_infrared_hemispherical_emissivity"),
                           ureg("0.9 front_side_solar_reflectance"),
                           ureg("0.9 front_side_visible_reflectance"),
                           ureg("0.0 infrared_transmittance"),
                           ureg("0.31 solar_transmittance"),
                           ureg("0.31 visible_transmittance"),

    )
    roof_constr = Construction("Roof", [Layer("Roof_L1", ureg("0.3m"), test_opaque_material)],BuildingElement.ROOF)
    wall_constr = Construction("Wall", [Layer("Wall_L1", ureg("0.3m"), test_opaque_material)],BuildingElement.WALL)
    ground_constr = Construction("Ground", [Layer("Ground_L1", ureg("0.3m"), test_opaque_material)],BuildingElement.GROUNDFLOOR)
    internal_ceiling_constr = Construction("InternalCeiling", [Layer("InternalCeiling_L1", ureg("0.3m"), test_opaque_material)],BuildingElement.INTERNAL_CEILING)
    window_glas_constr = WindowGlassConstruction("Glass", [WindowLayer("Glass_L1", ureg("0.02m"), test_transparent_material)])


    construction = BuildingConstruction(
        # NOTE: reusing the same ConstructionAsIDF object or path's as WindowPath breks pickling/unpickling because jsonpickle recognizes them as same objects but does not unpickle it correct....
        window_construction=WindowConstruction(glass=window_glas_constr, frame=win_frame, shade=win_shade),
        roof_constr=roof_constr,
        groundfloor_constr=ground_constr,
        wall_constr=wall_constr,
        internal_ceiling_constr=internal_ceiling_constr,
        glazing_ratio=0.3,
        infiltration_rate=0.6 * ureg.ACH,
        infiltration_profile=ScheduleFixedValue(1 * ureg.dimensionless, cesarp.common.ScheduleTypeLimits.FRACTION()),
        installation_characteristics=InstallationsCharacteristics(fraction_radiant_from_activity=0.3  * ureg.dimensionless,
                                                                  lighting_characteristics=LightingCharacteristics(0.4 * ureg.dimensionless, 0.2 * ureg.dimensionless, 0.2 * ureg.dimensionless),
                                                                  dhw_fraction_lost=0.4 * ureg.dimensionless,
                                                                  electric_appliances_fraction_radiant=0.2 *
                                                                                                       ureg.dimensionless,
                                                                  e_carrier_heating=EnergySource.WOOD,
                                                                  e_carrier_dhw=EnergySource.SOLAR_THERMAL),
    )
    fract_type = cesarp.common.ScheduleTypeLimits.FRACTION()
    cooling_sched = get_schedule_file("cooling.csv", ureg.dimensionless, cesarp.common.ScheduleTypeLimits.TEMPERATURE())

    geom_fact = GeometryBuilderFactory(read_sitevertices_from_csv(
                                            os.path.dirname(__file__) / Path("./testfixture/SiteVertices.csv"),
                                            {'gis_fid': "TARGET_FID", 'height': "HEIGHT", 'x': 'POINT_X', 'y': 'POINT_Y'}
                                        ),
                                        {"GEOMETRY": {"NEIGHBOURHOOD": {"RADIUS": 100}}})
    geom_builder = geom_fact.get_geometry_builder(5, 0.3)
    bldg_shape_detailed = geom_builder.get_bldg_shape_detailed()
    neighbours = geom_builder.get_bldg_shape_of_neighbours()

    neighbours_construction_props = {BuildingElement.WALL.name:
                                        ShadingObjectConstruction(
                                            diffuse_solar_reflectance_unglazed_part = 0.3 * ureg.diffuse_solar_reflectance,
                                            diffuse_visible_reflectance_unglazed_part = 0.3 * ureg.diffuse_visible_reflectance,
                                            glazing_ratio = 0.3 * ureg.dimensionless,
                                            window_glass_construction=construction.window_constr.glass
                                        ),
                                     BuildingElement.ROOF.name:
                                         ShadingObjectConstruction(
                                             diffuse_solar_reflectance_unglazed_part=0.15 * ureg.diffuse_solar_reflectance,
                                             diffuse_visible_reflectance_unglazed_part=0.17 * ureg.diffuse_visible_reflectance,
                                             glazing_ratio=0 * ureg.dimensionless,
                                             window_glass_construction=construction.window_constr.glass
                                         ),
                                        }

    operation = BuildingOperation(name="test",
                                    occupancy=Occupancy(floor_area_per_person=50*ureg.m**2/ureg.person,
                                                      occupancy_fraction_schedule=get_schedule_file("occupancy.csv", ureg.dimensionless, fract_type),
                                                      activity_schedule=get_schedule_file("activity.csv", ureg.W / ureg.person, cesarp.common.ScheduleTypeLimits.ANY())),
                                                      electric_appliances=InstallationOperation(get_schedule_file("electirc_appliance.csv", ureg.dimensionless, fract_type),
                                                                                                3 * ureg.watt/ureg.m**2),
                                    lighting=InstallationOperation(get_schedule_file("lighting.csv", ureg.dimensionless, fract_type), 1.2 * ureg.watt/ureg.m**2),
                                    dhw=InstallationOperation(get_schedule_file("dhw.csv", ureg.dimensionless, fract_type), 12 * ureg.watt/ureg.m**2),
                                                      hvac_operation=HVACOperation(heating_setpoint_schedule=get_schedule_file("heating.csv", ureg.dimensionless,
                                                                                                                               cesarp.common.ScheduleTypeLimits.TEMPERATURE()),
                                                               cooling_setpoint_schedule=cooling_sched,
                                                               ventilation_fraction_schedule=get_schedule_file("ventilation.csv", ureg.dimensionless, fract_type),
                                                               outdoor_air_flow_per_zone_floor_area=3.2 * ureg.m**3/ureg.sec/ureg.m**2),
                                                    night_vent=NightVent(True, ureg("3.1 ACH"), ureg("20 degreeC"), ureg("2 degreeC"), ureg("5.5 m/sec"), "20:00", "07:00", cooling_sched),
                                                    win_shading_ctrl=WindowShadingControl(True, False, ureg("90 W/m2"), "xxx"))

    op_mapping = BuildingOperationMapping()
    op_mapping.add_operation_assignment(range(0, bldg_shape_detailed.get_nr_of_floors()), operation)

    return BuildingModel(22,
                         2015,
                         site,
                         bldg_shape_detailed,
                         neighbours,
                         neighbours_construction_props,
                         construction,
                         op_mapping,
                         BldgType.MFH)

@pytest.fixture
def res_folder():
    result_main_folder = os.path.dirname(__file__) / Path("result")
    shutil.rmtree(result_main_folder, ignore_errors=True)
    os.makedirs(result_main_folder)
    yield result_main_folder
    shutil.rmtree(result_main_folder)

def test_model_serialize(sample_model_with_constr, res_folder):
    save_path = res_folder / Path("sample_model.json")
    cesarp.manager.json_pickling.save_to_disk(sample_model_with_constr, save_path)
    parsed_model = cesarp.manager.json_pickling.read_from_disk(save_path)
    # just do some spot-checks
    assert parsed_model.bldg_construction.infiltration_rate == sample_model_with_constr.bldg_construction.infiltration_rate
    assert parsed_model.site.site_ground_temperatures.deep == sample_model_with_constr.site.site_ground_temperatures.deep
    assert parsed_model.bldg_type == BldgType.MFH
    assert parsed_model.bldg_shape.windows

    # test if we can write to model to IDF - to check if the pickling porcess did nothing bad, e.g. storing dicts or nested DataFrames as strings....
    my_idf_writer = CesarIDFWriter(res_folder / Path("sample_model.idf"), cesarp.common.init_unit_registry())
    my_idf_writer.write_bldg_model(parsed_model)

def test_nested_df_serialize(sample_model_with_constr, res_folder):
    save_path = res_folder / Path("walls.json")
    cesarp.manager.json_pickling.save_to_disk(sample_model_with_constr.bldg_shape.walls, save_path)
    parsed_walls = cesarp.manager.json_pickling.read_from_disk(save_path)
    assert isinstance(parsed_walls[0][0], pd.DataFrame)
    assert all(parsed_walls[0][0].columns == ["x", "y", "z"])

def test_pickle_BuildingConstruction(sample_model_with_constr, res_folder):
    """
    Note: jsonpickle can't handle a dictionary contianing the same object (in this case it was a WindowsPath or ConstructionAsIDF instance)
    """
    save_path = res_folder / Path("bldg_constr.json")
    cesarp.manager.json_pickling.save_to_disk(sample_model_with_constr.bldg_construction, save_path)
    parsed_constructions = cesarp.manager.json_pickling.read_from_disk(save_path)
    assert isinstance(parsed_constructions.window_constr, WindowConstruction)
    # TODO improve testing
    assert isinstance(parsed_constructions.roof_constr, Construction)

def test_pickle_neighbour_construction(sample_model_with_constr, res_folder):
    """
    Note: jsonpickle can't handle a dictionary contianing the same object (in this case it was a WindowsPath or ConstructionAsIDF instance)
    """
    save_path = res_folder / Path("neigh_constr.json")
    cesarp.manager.json_pickling.save_to_disk(sample_model_with_constr.neighbours_construction_props, save_path)
    parsed_constructions = cesarp.manager.json_pickling.read_from_disk(save_path)
    assert isinstance(parsed_constructions[BuildingElement.WALL.name], ShadingObjectConstruction)
    assert isinstance(parsed_constructions[BuildingElement.ROOF.name], ShadingObjectConstruction)

def test_enum_dict_keys(res_folder):

    save_path = res_folder / Path("dict_enumkeystest.json")
    cesarp.manager.json_pickling.save_to_disk(TestDummy(), save_path)
    loaded_dummy = cesarp.manager.json_pickling.read_from_disk(save_path)
    assert loaded_dummy.neighbour_bldg_elems[BuildingElement.ROOF.name]
    assert loaded_dummy.neighbour_bldg_elems[BuildingElement.WALL.name]


def test_pickle_operation(sample_model_with_constr, res_folder):
    save_path = res_folder / Path("bldg_op_file.json")
    bldg_op = sample_model_with_constr.bldg_operation_mapping.get_operation_for_floor(0)
    ureg = cesarp.common.init_unit_registry()

    cesarp.manager.json_pickling.save_to_disk(bldg_op, save_path)
    parsed_building_op: BuildingOperation = cesarp.manager.json_pickling.read_from_disk(save_path)
    assert isinstance(parsed_building_op, BuildingOperation)
    assert 90 == parsed_building_op.win_shading_ctrl.radiation_min_setpoint.m
    assert isinstance(parsed_building_op.night_vent.maximum_indoor_temp_profile, ScheduleFile)

def test_pickle_id_identical_obj(res_folder):
    theBatch = ChocolateChips(flour=200, sugar=100, chocolact_chips=500, oatmeal=200, egg=1)
    batches = {"yummy_ones": theBatch, "more_needed": theBatch} # list containing id-identical objects
    json_file = res_folder / Path("chocolates.json")
    cesarp.manager.json_pickling.save_to_disk(batches, json_file)
    parsed_batches = cesarp.manager.json_pickling.read_from_disk(json_file)
    assert isinstance(parsed_batches["more_needed"], ChocolateChips) # when setting make_refs=False, the second list item gets encoded and decoded as string/__repr__ - this seems to be fixed with jsonpickling version 2.0.0! so I did set now make_refs=False!


def test_unpickle_bldg_container_cesarp_1_1_0(fixture_folder):
    ureg = cesarp.common.init_unit_registry()
    bldg_cont_file_path = fixture_folder / Path("bldg_container_cesarp_v_1_1_0.json")
    parsed_bldg_container = cesarp.manager.json_pickling.read_bldg_container_from_disk(bldg_cont_file_path)
    assert isinstance(parsed_bldg_container, BuildingContainer)
    assert parsed_bldg_container.get_eplus_error_level() is EplusErrorLevel.UNKNOWN
    assert isinstance(parsed_bldg_container.get_bldg_model().bldg_shape, BldgShapeDetailed)

def test_unpickle_bldg_model_version_1_2(fixture_folder):
    ureg = cesarp.common.init_unit_registry()
    bldg_cont_file_path = fixture_folder / Path("bldg_container_fid_1_bldg_model_1_2.json")
    with pytest.raises(CesarpException):
        parsed_bldg_container = cesarp.manager.json_pickling.read_bldg_container_from_disk(bldg_cont_file_path)

    # the upgrade functionality for building model version 1.2 is not tested anymore, as in the normal workflow the functionality is not used anymore from cesar-p version 2.0.0 upwards

def test_unpickle_bldg_container_version_2(fixture_folder):
    ureg = cesarp.common.init_unit_registry()
    bldg_cont_file_path = fixture_folder / Path("bldg_container_fid_1_version_2.json")
    with pytest.raises(CesarpException):
        parsed_bldg_container = cesarp.manager.json_pickling.read_bldg_container_from_disk(bldg_cont_file_path)

    # the upgrade functionality for building container version 2 is not tested anymore, as in the normal workflow the functionality is not used anymore from cesar-p version 2.0.0 upwards


@dataclass
class ChocolateChips:
    flour: int
    sugar: int
    chocolact_chips: int
    oatmeal: int
    egg: int

class TestDummy:
    def __init__(self):
        self.main_bldg_elems = {BuildingElement.WALL.name: "theMainWallDefinition", BuildingElement.GROUNDFLOOR.name: "theMainGroundfloorDefinition"}
        self.neighbour_bldg_elems = {BuildingElement.WALL.name: "theNeighbourWallDefinition", BuildingElement.ROOF.name: "theNeighbourRoofDefinition"}