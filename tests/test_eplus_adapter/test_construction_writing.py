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
import pint
import shutil
from eppy.modeleditor import IDF
from six import StringIO

from tests.test_helpers.test_helpers import are_files_equal
import cesarp.common
from cesarp.model.OpaqueMaterial import OpaqueMaterial, OpaqueMaterialRoughness
from cesarp.model.TransparentMaterial import TransparentMaterial
from cesarp.model.Construction import Construction
from cesarp.model.WindowConstruction import WindowConstruction, WindowGlassConstruction, WindowFrameConstruction, WindowShadingMaterial
from cesarp.model.Layer import Layer
from cesarp.model.WindowLayer import WindowLayer
from cesarp.model.Gas import Gas
from cesarp.model.BuildingElement import BuildingElement

import cesarp.eplus_adapter.idf_strings
from cesarp.eplus_adapter import idf_writer_construction
from cesarp.eplus_adapter import _default_config_file as eplus_adpater_config_file

_RESULT_FOLDER = os.path.dirname(__file__) / Path("results_constr")

@pytest.fixture
def idf_res_path():
    res_folder = Path(_RESULT_FOLDER).absolute()
    shutil.rmtree(res_folder, ignore_errors = True)
    os.mkdir(res_folder)
    yield res_folder / Path("constr_test.idf")
    shutil.rmtree(res_folder, ignore_errors=True)

def get_sample_opaque_mat(ureg: pint.UnitRegistry):
    myMat = OpaqueMaterial(
                name = "Glasswool_TEST",
                density = 22 * ureg.kg / ureg.m ** 3,
                roughness = OpaqueMaterialRoughness.ROUGH,
                solar_absorptance = 0.6 * ureg.solar_absorptance,
                specific_heat= 830 * ureg.J / (ureg.kg * ureg.K),
                thermal_absorptance = 0.9 * ureg.solar_absorptance,
                conductivity = 0.040 * ureg.W / (ureg.m * ureg.K),
                visible_absorptance = 0.6 * ureg.solar_absorptance,
                co2_emission_per_kg = None,
                non_renewable_primary_energy_per_kg = None)
    return myMat

def get_sample_opaque_no_mass_mat(ureg: pint.UnitRegistry):
    myMat = OpaqueMaterial(
                name = "Vapour_Barrier_TEST",
                roughness = OpaqueMaterialRoughness.ROUGH,
                solar_absorptance = 0.7 * ureg.solar_absorptance,
                thermal_absorptance= 0.9 * ureg.solar_absorptance,
                conductivity=0.19 * ureg.W / (ureg.m * ureg.K),
                visible_absorptance=0.7 * ureg.solar_absorptance,
                density=None,
                specific_heat=None,
                co2_emission_per_kg=None,
                non_renewable_primary_energy_per_kg=None)
    return myMat

def get_sample_win_glazing_mat(ureg: pint.UnitRegistry):
    myMat = TransparentMaterial(
                name = "WinGlazing_Test",
                back_side_infrared_hemispherical_emissivity= 0.84 * ureg.back_side_infrared_hemispherical_emissivity,
                back_side_solar_reflectance= 0.071 * ureg.back_side_solar_reflectance,
                back_side_visible_reflectance= 0.08 * ureg.back_side_visible_reflectance,
                conductivity= 0.9 * ureg.W / (ureg.m * ureg.K),
                dirt_correction_factor= 1.0 * ureg.dirt_correction_factor,
                front_side_infrared_hemispherical_emissivity= 0.84 * ureg.front_side_infrared_hemispherical_emissivity,
                front_side_solar_reflectance= 0.071 * ureg.front_side_solar_reflectance,
                front_side_visible_reflectance= 0.08 * ureg.front_side_visible_reflectance,
                infrared_transmittance= 0.0 * ureg.infrared_transmittance,
                solar_transmittance= 0.775 * ureg.solar_transmittance,
                visible_transmittance= 0.881 * ureg.visible_transmittance)
    return myMat

def get_sample_gas(ureg: pint.UnitRegistry):
    return Gas(name="Air_Test", conductivity=0.4 * ureg.W/ureg.m/ureg.K)

def get_sample_opaque_constr(ureg: pint.UnitRegistry):
    sample_opaque_mat = get_sample_opaque_mat(ureg)
    sample_no_mass_mat = get_sample_opaque_no_mass_mat(ureg)
    the_layers = [
        Layer(name="sample_mat.250", thickness=0.25 * ureg.m, material=sample_opaque_mat),
        Layer(name="sample_mat.150", thickness=0.15 * ureg.m, material=sample_opaque_mat),
        Layer(name="vapour_barrier_.0.004", thickness=0.004 * ureg.m, material=sample_no_mass_mat),
        Layer(name="cavity", thickness=0.03 * ureg.m, material=get_sample_gas(ureg)),
        Layer(name="sample_mat.250", thickness=0.25 * ureg.m, material=sample_opaque_mat),
    ]

    return Construction(name="the_sample_construction",
                        layers=the_layers,
                        bldg_element=BuildingElement.WALL
                        )

def get_sample_win_constr(ureg: pint.UnitRegistry):
    win_frame = WindowFrameConstruction(name="window_frame_fixed_cesar-p",
                                        short_name="window_frame_fixed_cesar-p",
                                        frame_conductance=9.5 * ureg.W / ureg.m ** 2 / ureg.K,
                                        frame_solar_absorptance=0.5 * ureg.dimensionless,
                                        frame_visible_absorptance=0.5 * ureg.dimensionless,
                                        outside_reveal_solar_absorptance=0.5 * ureg.dimensionless,
                                        emb_co2_emission_per_m2=None,
                                        emb_non_ren_primary_energy_per_m2=None)

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

    win_air_layer = WindowLayer(name="WindowAirGap", material=get_sample_gas(ureg), thickness=0.02 * ureg.m)
    win_glass_layer = WindowLayer(name="TestGlazing", material=get_sample_win_glazing_mat(ureg),
                                  thickness=0.006 * ureg.m)

    win_constr_name = "My_Window_Glass_Constr_Test"
    return WindowConstruction(
        frame = win_frame,
        glass = WindowGlassConstruction(
            name=win_constr_name,
            layers=[win_glass_layer, win_air_layer, win_glass_layer],
            emb_co2_emission_per_m2=None,
            emb_non_ren_primary_energy_per_m2=None
        ),
        shade=win_shade
    )



@pytest.fixture
def idf():
    eplus_cfg = cesarp.common.config_loader.load_config_for_package(eplus_adpater_config_file, "cesarp.eplus_adapter")
    IDF.setiddname(eplus_cfg["CUSTOM_IDD_9_5"])
    idfstring = cesarp.eplus_adapter.idf_strings.version.format("9.5.0")
    fhandle = StringIO(idfstring)
    return IDF(fhandle)


@pytest.fixture
def ureg():
    return cesarp.common.init_unit_registry()

def test_add_construction(ureg, idf, idf_res_path):
    sample_constr = get_sample_opaque_constr(ureg)
    idf_writer_construction.add_detailed_construction(idf=idf, construction=sample_constr, ureg=ureg)
    idf.save(idf_res_path)

    assert are_files_equal(idf_res_path,
                           os.path.dirname(__file__) / Path("./expected_results/constr/constr_opaque.idf"),
                           ignore_line_nrs=[1])


def test_add_window_construction(ureg, idf, idf_res_path):
    sample_constr = get_sample_win_constr(ureg)
    idf_writer_construction.add_win_glass_construction(idf=idf, glass_constr=sample_constr.glass, ureg=ureg)
    idf_writer_construction.add_win_frame_construction(idf=idf, frame_constr=sample_constr.frame, ureg=ureg)
    idf.save(idf_res_path)

    assert are_files_equal(idf_res_path,
                           os.path.dirname(__file__) / Path("./expected_results/constr/constr_window.idf"),
                           ignore_line_nrs=[1])


def test_add_opaque_material(ureg, idf, idf_res_path):
    sample_mat = get_sample_opaque_mat(ureg)
    idf_writer_construction.add_opaque_material(idf=idf,
                                                idf_obj_name="Glasswool_TEST.2500",
                                                thickness=0.25 * ureg.m,
                                                mat_def=sample_mat, ureg=ureg)
    idf.save(idf_res_path)

    assert are_files_equal(idf_res_path,
                           os.path.dirname(__file__) / Path("./expected_results/constr/opaque_mat.idf"),
                           ignore_line_nrs=[1])


def test_add_win_glazing_material(ureg, idf, idf_res_path):
    sample_win_glazing_mat = get_sample_win_glazing_mat(ureg)
    idf_writer_construction.add_window_glazing_material(idf=idf,
                                                        idf_obj_name="my_test_win_mat",
                                                        thickness=0.006 * ureg.m,
                                                        mat_def=sample_win_glazing_mat, ureg=ureg)
    idf.save(idf_res_path)
    assert are_files_equal(idf_res_path,
                           os.path.dirname(__file__) / Path("./expected_results/constr/window_glazing_mat.idf"),
                           ignore_line_nrs=[1])