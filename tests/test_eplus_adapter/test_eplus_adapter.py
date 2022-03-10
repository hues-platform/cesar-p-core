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
from pathlib import Path
import pytest
from six import StringIO
from eppy.modeleditor import IDF

from tests.test_helpers.test_helpers import are_files_equal

from cesarp.manager.BldgModelFactory import BldgModelFactory
import cesarp.geometry.csv_input_parser
from cesarp.geometry.GeometryBuilder import GeometryBuilder
from cesarp.geometry import vertices_basics
import cesarp.common
from cesarp.construction.ConstructionBuilder import ConstructionBuilder
from cesarp.model.BuildingElement import BuildingElement
from cesarp.model.ShadingObjectConstruction import ShadingObjectConstruction
from cesarp.model.BuildingOperation import WindowShadingControl
from cesarp.model.WindowConstruction import WindowShadingMaterial
from cesarp.construction.NeighbouringBldgConstructionFactory import NeighbouringBldgConstructionFactory
from cesarp.eplus_adapter.CesarIDFWriter import CesarIDFWriter
import cesarp.eplus_adapter.idf_writing_helpers
import cesarp.eplus_adapter.idf_strings
from cesarp.eplus_adapter import _default_config_file as eplus_adpater_config_file
from cesarp.eplus_adapter.RelativeAuxiliaryFilesHandler import RelativeAuxiliaryFilesHandler
from cesarp.site.SiteGroundTemperatureFactory import SiteGroundTemperatureFactory
from cesarp.eplus_adapter.ConstructionIDFWritingHandler import ConstructionIDFWritingHandler
from cesarp.model.EnergySource import EnergySource
from cesarp.graphdb_access.GraphDBArchetypicalConstructionFactory import GraphDBArchetypicalConstructionFactory
from cesarp.graphdb_access.LocalFileReader import LocalFileReader

import shutil

__sitevertices_labels = {"gis_fid": "TARGET_FID", "height": "HEIGHT", "x": "POINT_X", "y": "POINT_Y"}

_RESULT_FOLDER =  os.path.dirname(__file__) / Path("results")

@pytest.fixture
def res_folder():
    res_folder = Path(_RESULT_FOLDER).absolute()
    shutil.rmtree(res_folder, ignore_errors=True)
    yield res_folder
    shutil.rmtree(res_folder, ignore_errors=True)

@pytest.fixture
def ureg():
    return cesarp.common.init_unit_registry()

@pytest.fixture

def idf():
    eplus_cfg = cesarp.common.config_loader.load_config_for_package(eplus_adpater_config_file, "cesarp.eplus_adapter")
    IDF.setiddname(eplus_cfg["CUSTOM_IDD_9_5"])
    idfstring = cesarp.eplus_adapter.idf_strings.version.format("9.5")
    fhandle = StringIO(idfstring)
    idf = IDF(fhandle)
    return idf


def get_sched_file_watt_per_squaremeter(ureg):
    return cesarp.common.ScheduleFile("testprofile.csv", cesarp.common.ScheduleTypeLimits.ANY(), 2, ";", 8760, 1, ureg.W/ureg.m**2)


def get_sched_fixed_fraction(ureg):
    return cesarp.common.ScheduleFixedValue(0.9 * ureg.dimensionless, cesarp.common.ScheduleTypeLimits.FRACTION())


def __get_constr_for(bldg_fid, year_of_construction, ureg):
    reader = LocalFileReader()
    construction_factory = GraphDBArchetypicalConstructionFactory({bldg_fid: year_of_construction},
                                                           {bldg_fid: EnergySource.DHW_OTHER},
                                                           {bldg_fid: EnergySource.HEATING_OTHER},
                                                           reader,
                                                           ureg)
    constr_archetype = construction_factory.get_archetype_for(bldg_fid)
    return ConstructionBuilder(bldg_fid, constr_archetype).build()


def __get_shading_constr(glass_constr, ureg):
    return {BuildingElement.WALL.name:
                ShadingObjectConstruction(
                        diffuse_solar_reflectance_unglazed_part = 0.3 * ureg.diffuse_solar_reflectance,
                        diffuse_visible_reflectance_unglazed_part = 0.3 * ureg.diffuse_visible_reflectance,
                        glazing_ratio = 0.3 * ureg.dimensionless,
                        window_glass_construction=glass_constr),
                BuildingElement.ROOF.name:
                     ShadingObjectConstruction(
                         diffuse_solar_reflectance_unglazed_part=0.15 * ureg.diffuse_solar_reflectance,
                         diffuse_visible_reflectance_unglazed_part=0.1 * ureg.diffuse_visible_reflectance,
                         glazing_ratio=0 * ureg.dimensionless,
                         window_glass_construction=glass_constr)
            }


def test_simulations_basic_settings(ureg, res_folder):
    expected_file_path = os.path.dirname(__file__) / Path(
        "./expected_results/idf_expected_simulation_basics.idf")

    os.makedirs(res_folder, exist_ok=True)
    aux_files_handler = RelativeAuxiliaryFilesHandler()
    aux_files_handler.set_destination(res_folder, "profiles")

    idf_file_path = res_folder / Path("idf_simulation_basics.idf")
    my_idf_writer = CesarIDFWriter(idf_file_path, ureg, aux_files_handler)
    idf = IDF(str(idf_file_path))
    my_idf_writer.add_basic_simulation_settings(idf, SiteGroundTemperatureFactory(ureg).get_ground_temperatures())
    idf.save()
    assert are_files_equal(idf_file_path, expected_file_path, ignore_line_nrs=[1]) == True


def test_building_geometry(ureg, res_folder):
    expected_file_path = os.path.dirname(__file__) / Path("./expected_results/idf_expected_geometry.idf")
    site_vertices_file = os.path.dirname(__file__) / Path("./testfixture/SiteVertices.csv")
    main_bldg_fid = 2
    glazing_ratio = 0.16
    infiltration_rate = 0.71 * ureg.ACH
    flat_vertices = cesarp.geometry.csv_input_parser.read_sitevertices_from_csv(site_vertices_file, __sitevertices_labels)
    site_bldgs = vertices_basics.convert_flat_site_vertices_to_per_bldg_footprint(flat_vertices)
    bldg_geometry = GeometryBuilder(main_bldg_fid, site_bldgs, glazing_ratio)
    bldg_shape = bldg_geometry.get_bldg_shape_detailed()

    idf_file_path = res_folder / Path("idf_geometry.idf")
    aux_files_handler = RelativeAuxiliaryFilesHandler()
    aux_files_handler.set_destination(res_folder, "profiles")
    my_idf_writer = CesarIDFWriter(idf_file_path, ureg, aux_files_handler)

    bldg_constr = __get_constr_for(main_bldg_fid, 1930, ureg)
    bldg_constr.infiltration_rate = infiltration_rate # overwrite because the default has higher precision than what was written with the matlab version
    idf = IDF(str(idf_file_path))
    my_idf_writer.add_building_geometry(idf, bldg_shape, ConstructionIDFWritingHandler(bldg_constr, None, ureg))
    idf.save()
    assert are_files_equal(idf_file_path, expected_file_path, ignore_line_nrs=[1])

    # test wrong infiltration rate unit
    bldg_constr.infiltration_rate = 3 * ureg.m ** 3 / ureg.sec
    with pytest.raises(Exception):
        my_idf_writer.add_building_geometry(idf, bldg_shape, ConstructionIDFWritingHandler(bldg_constr, None, ureg))


def test_neighbour_shading_objects(ureg, res_folder):
    expected_file_path = os.path.dirname(__file__) / Path("./expected_results/idf_expected_neighbours.idf")
    site_vertices_file = os.path.dirname(__file__) / Path("./testfixture/SiteVertices_minimized.csv")
    main_bldg_fid = 2
    glazing_ratio = 0.16

    flat_vertices = cesarp.geometry.csv_input_parser.read_sitevertices_from_csv(site_vertices_file, __sitevertices_labels)
    site_bldgs = vertices_basics.convert_flat_site_vertices_to_per_bldg_footprint(flat_vertices)
    bldg_geometry = GeometryBuilder(main_bldg_fid, site_bldgs, glazing_ratio)
    neighbours = bldg_geometry.get_bldg_shape_of_neighbours()

    idf_file_path = res_folder / Path("idf_neighbours.idf")

    aux_files_handler = RelativeAuxiliaryFilesHandler()
    aux_files_handler.set_destination(res_folder, "profiles")
    my_idf_writer = CesarIDFWriter(idf_file_path, ureg, aux_files_handler)

    win_glass_constr = __get_constr_for(main_bldg_fid, 1930, ureg).window_constr.glass
    neigh_constr = __get_shading_constr(win_glass_constr, ureg)
    idf = IDF(str(idf_file_path))
    my_idf_writer.add_neighbours(idf, neighbours, ConstructionIDFWritingHandler(None, neigh_constr, ureg))
    idf.save()
    assert are_files_equal(idf_file_path, expected_file_path, ignore_line_nrs=[1])


def test_full_idf(res_folder):
    gis_fid = 2
    expected_file_path = os.path.dirname(__file__) / Path("./expected_results/idf_expected_full.idf")
    result_idf_file_path = res_folder / Path(f"fid_{gis_fid}_full.idf")
    config = dict()
    config["MANAGER"] = dict()
    config["MANAGER"]["SITE_VERTICES_FILE"] = {"PATH": os.path.dirname(__file__) / Path("./testfixture/SiteVertices.csv")}
    config["MANAGER"]["BLDG_FID_FILE"] = {"PATH": os.path.dirname(__file__) / Path("./testfixture/BuildingInformation.csv")}
    config["MANAGER"]["BLDG_AGE_FILE"] = {"PATH": os.path.dirname(__file__) / Path("./testfixture/BuildingInformation.csv")}
    config["MANAGER"]["BLDG_TYPE_PER_BLDG_FILE"] = {"PATH": os.path.dirname(__file__) / Path("./testfixture/BuildingInformation.csv")}
    config["MANAGER"]["BLDG_INSTALLATION_FILE"] = {"PATH": os.path.dirname(__file__) / Path("./testfixture/BuildingInformation.csv")}
    config["MANAGER"]["BUILDING_OPERATION_FACTORY_CLASS"] = "cesarp.operation.fixed.FixedBuildingOperationFactory.FixedBuildingOperationFactory"
    config["MANAGER"]["SINGLE_SITE"] = {"ACTIVE": True, "WEATHER_FILE": os.path.dirname(__file__) / Path("./testfixture/DummyWeather.epw")}
    config["MANAGER"]["SITE_PER_CH_COMMUNITY"] = {"ACTIVE": False}
    config["GEOMETRY"] = {"NEIGHBOURHOOD": {"RADIUS": 1}}

    unit_reg = cesarp.common.init_unit_registry()
    bldg_models_factory = BldgModelFactory(unit_reg, config)
    bldg_model = bldg_models_factory.create_bldg_model(gis_fid)
    profile_file_handler = RelativeAuxiliaryFilesHandler()
    profile_file_handler.set_destination(res_folder, "profiles")
    my_idf_writer = cesarp.eplus_adapter.CesarIDFWriter.CesarIDFWriter(result_idf_file_path, unit_reg, profile_file_handler, custom_config=config)
    my_idf_writer.write_bldg_model(bldg_model)
    assert are_files_equal(result_idf_file_path, expected_file_path, ignore_line_nrs=[1], ignore_case=True, ignore_filesep_mismatch=True)


def test_write_schedule_fixed(ureg, idf):
    sched_fixed = get_sched_fixed_fraction(ureg)
    cesarp.eplus_adapter.idf_writing_helpers.add_schedule(idf, sched_fixed, required_type=cesarp.common.ScheduleTypeLimits.FRACTION())
    my_idf_sched_obj =  idf.getobject('SCHEDULE:CONSTANT', 'Constant_0.9')
    assert my_idf_sched_obj is not None
    assert my_idf_sched_obj.Hourly_Value == 0.9


def test_write_schedule_file(ureg, idf):
    sched = get_sched_file_watt_per_squaremeter(ureg)
    sched.name = "test"
    cesarp.eplus_adapter.idf_writing_helpers.add_schedule(idf, sched, required_unit=ureg.W/ureg.m**2)
    my_idf_sched_obj =  idf.getobject('SCHEDULE:FILE', 'test')
    assert my_idf_sched_obj is not None


def test_write_schedule_fixed_unit_error(ureg, idf):
    sched_fixed = get_sched_fixed_fraction(ureg)
    with pytest.raises(Exception):
        cesarp.eplus_adapter.idf_writing_helpers.add_schedule(idf, sched_fixed, required_unit=ureg.W)
    my_idf_sched_obj =  idf.getobject('SCHEDULE:CONSTANT', 'Constant_0.9')
    assert my_idf_sched_obj is None


def test_write_schedule_file_unit_error(ureg, idf):
    sched = get_sched_file_watt_per_squaremeter(ureg)
    with pytest.raises(Exception):
        cesarp.eplus_adapter.idf_writing_helpers.add_schedule(idf, sched, required_unit=ureg.W/ureg.m**3)
    my_idf_sched_obj =  idf.getobject('SCHEDULE:FILE', 'test')
    assert my_idf_sched_obj is None


def test_write_schedule_type_error(ureg, idf):
    sched_fixed = get_sched_fixed_fraction(ureg)
    with pytest.raises(Exception):
        cesarp.eplus_adapter.idf_writing_helpers.add_schedule(idf, sched_fixed, required_type=cesarp.common.ScheduleTypeLimits.ON_OFF())
    my_idf_sched_obj =  idf.getobject('SCHEDULE:CONSTANT', 'Constant_0.9')
    assert my_idf_sched_obj is None


