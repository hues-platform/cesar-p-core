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
import shutil

from six import StringIO
from eppy.modeleditor import IDF
from tests.test_helpers.test_helpers import are_files_equal
import cesarp.common
from cesarp.common.ScheduleFixedValue import ScheduleFixedValue
from cesarp.common.ScheduleTypeLimits import ScheduleTypeLimits
from cesarp.model.BuildingOperation import NightVent
from cesarp.eplus_adapter.CesarIDFWriter import CesarIDFWriter
import cesarp.eplus_adapter.idf_writing_helpers
import cesarp.eplus_adapter.idf_strings
from cesarp.eplus_adapter import _default_config_file as eplus_adpater_config_file
from cesarp.eplus_adapter import idf_writer_night_vent

_RESULT_FOLDER = os.path.dirname(__file__) / Path("results")
_EXPECTED_FOLDER = os.path.dirname(__file__) / Path("expected_results")

@pytest.fixture
def res_folder():
    res_folder = Path(_RESULT_FOLDER).absolute()
    os.makedirs(res_folder, exist_ok=True)
    yield res_folder
    if os.path.exists(res_folder):
        pass
        #shutil.rmtree(res_folder)


@pytest.fixture
def idf():
    eplus_cfg = cesarp.common.config_loader.load_config_for_package(eplus_adpater_config_file, "cesarp.eplus_adapter")
    IDF.setiddname(eplus_cfg["CUSTOM_IDD_9_5"])
    idfstring = cesarp.eplus_adapter.idf_strings.version.format("9.5")
    fhandle = StringIO(idfstring)
    idf = IDF(fhandle)
    return idf


def test_add_night_vent_zone_flowrate(res_folder, idf):
    ureg = cesarp.common.init_unit_registry()
    expected_file_path = _EXPECTED_FOLDER / Path("./night_vent_zone_expected.idf")
    myModel = NightVent(is_active=True,
        flow_rate=ureg("2.5 ACH"),
        min_indoor_temperature=ureg("24 degreeC"),
        maximum_in_out_deltaT=ureg("2 degreeC"),
        max_wind_speed=ureg("40 m/s"),          # maximum wind speed threshold (m/s) - above this value the occupant closes the window - 40m/s is default in EnergyPlus Version 8.5
        start_hour="20:00",        # night ventilation starting hour (00:00 format)
        end_hour="6:00",          # night ventilation ending hour (00:00 format)
        maximum_indoor_temp_profile=ScheduleFixedValue(value=ureg("25 degreeC"), type_limit=ScheduleTypeLimits.TEMPERATURE()))
    idf_writer_night_vent.add_night_ventilation_for_zone(idf, "myzone", myModel)
    idf_file_path = res_folder / Path('night_vent_zone_result.idf')
    idf.save(idf_file_path)
    assert are_files_equal(idf_file_path, expected_file_path, ignore_line_nrs=[1])



