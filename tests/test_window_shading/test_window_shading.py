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
import shutil

from tests.test_helpers.test_helpers import are_files_equal

import cesarp.common
from cesarp.construction.ConstructionBasics import ConstructionBasics
from cesarp.model.BuildingOperation import WindowShadingControl
from cesarp.eplus_adapter.CesarIDFWriter import CesarIDFWriter
import cesarp.eplus_adapter.idf_writing_helpers
import cesarp.eplus_adapter.idf_strings
from cesarp.eplus_adapter import _default_config_file as eplus_adpater_config_file
from cesarp.eplus_adapter import idf_writer_window_shading
from cesarp.graphdb_access.LocalFileReader import LocalFileReader
from cesarp.graphdb_access.BldgElementConstructionReader import BldgElementConstructionReader

_RESULT_FOLDER = os.path.dirname(__file__) / Path("results")
_EXPECTED_FOLDER = os.path.dirname(__file__) / Path("expected_results")
_FIXTURE_FOLDER = os.path.dirname(__file__) / Path("testfixture")


@pytest.fixture
def constr_basics():
    return ConstructionBasics(cesarp.common.init_unit_registry(), {})

@pytest.fixture
def local_db_access():
    ureg = cesarp.common.init_unit_registry()
    local_reader = LocalFileReader()
    reader = BldgElementConstructionReader(local_reader, ureg)
    return reader

@pytest.fixture
def res_folder():
    res_folder = Path(_RESULT_FOLDER).absolute()
    os.makedirs(res_folder, exist_ok=True)
    yield res_folder
    if os.path.exists(res_folder):
        shutil.rmtree(res_folder)


@pytest.fixture
def idf():
    eplus_cfg = cesarp.common.config_loader.load_config_for_package(eplus_adpater_config_file, "cesarp.eplus_adapter")
    IDF.setiddname(eplus_cfg["CUSTOM_IDD_9_5"])
    idfstring = cesarp.eplus_adapter.idf_strings.version.format("9.5")
    fhandle = StringIO(idfstring)
    idf = IDF(fhandle)
    return idf


def test_basic_Shade0101(res_folder , idf, local_db_access):
    expected_file_path = _EXPECTED_FOLDER / Path("./Shade0101.idf")
    shade_mat_idf_name = idf_writer_window_shading._add_shading_mat(idf, local_db_access.get_window_shading_constr("http://uesl_data/sources/archetypes/1918_SFH_Archetype"))
    idf_file_path = res_folder / Path('Shade0101_compare.idf')
    idf.save(idf_file_path)
    assert are_files_equal(idf_file_path, expected_file_path, ignore_line_nrs=[1])


def test_basic_Shade0801(res_folder , idf, local_db_access):
    expected_file_path = _EXPECTED_FOLDER / Path("./Shade0801.idf")
    shade_mat_idf_name = idf_writer_window_shading._add_shading_mat(idf, local_db_access.get_window_shading_constr("http://uesl_data/sources/archetypes/2014_SFH_Archetype"))
    idf_file_path = res_folder / Path('Shade0801_compare.idf')
    idf.save(idf_file_path)
    assert are_files_equal(idf_file_path, expected_file_path, ignore_line_nrs=[1])


def test_basic_Shade0901(res_folder, idf, local_db_access):
    expected_file_path = _EXPECTED_FOLDER / Path("./Shade0901.idf")
    shade_mat_idf_name = idf_writer_window_shading._add_shading_mat(idf, local_db_access.get_window_shading_constr("http://uesl_data/sources/archetypes/2015_SFH_Archetype"))
    idf_file_path = res_folder / Path('Shade0901_compare.idf')
    idf.save(idf_file_path)
    assert are_files_equal(idf_file_path, expected_file_path, ignore_line_nrs=[1])

