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
from cesarp.common.CesarpException import CesarpException
from cesarp.SIA2024.SIA2024Facade import SIA2024Facade
from cesarp.SIA2024.SIA2024BuildingType import SIA2024BldgTypeKeys
from cesarp.operation.PassiveCoolingOperationFactory import PassiveCoolingOperationFactory

NR_OF_LINES_EXPECTED_NOMINAL_PROFILE = [84, 87]  # depending on wether we run from git checkout or on CI, we have the lines for GIT status or not...
# variable profiles have currently one line less metadata because they were not re-generated with 2.0.0
NR_OF_LINES_EXPECTED_VARIABLE_PROFILE = [83, 86]  # depending on wether we run from git checkout or on CI, we have the lines for GIT status or not...

def test_init():
    config = {}
    ureg = cesarp.common.init_unit_registry()
    sia2024 = SIA2024Facade({1: 'MFH', 2: 'SFH', 3: 'MFH'}, PassiveCoolingOperationFactory(ureg, config), ureg, config)
    assert sia2024.params_manager is not None

def test_mfh_param_set_nominal():
    ureg = cesarp.common.init_unit_registry()
    sia2024 = SIA2024Facade({1: 'MFH'},  PassiveCoolingOperationFactory(ureg, custom_cfg={}), ureg)
    sia2024.load_or_create_parameters([SIA2024BldgTypeKeys.MFH], variability_active=False)
    mfh_params = sia2024.get_building_operation(1, 1).get_operation_for_floor(0)
    activity_prof = mfh_params.occupancy.activity_schedule
    print(f'{activity_prof.schedule_file} column {activity_prof.data_column} header rows {activity_prof.header_rows}')
    assert activity_prof.data_column == 3
    assert activity_prof.header_rows in NR_OF_LINES_EXPECTED_NOMINAL_PROFILE  # header with or without git information
    assert activity_prof.schedule_file == mfh_params.dhw.fraction_schedule.schedule_file

def test_mfh_param_set_variable():
    config = {}
    ureg = cesarp.common.init_unit_registry()
    sia2024 = SIA2024Facade({1: 'MFH'},  PassiveCoolingOperationFactory(ureg, config), ureg, config)
    sia2024.load_or_create_parameters([SIA2024BldgTypeKeys.MFH], variability_active=True)
    mfh_params = sia2024.get_building_operation(1, 1).get_operation_for_floor(0)
    activity_prof = mfh_params.occupancy.activity_schedule
    print(f'{activity_prof.schedule_file} column {activity_prof.data_column} header rows {activity_prof.header_rows}')
    assert activity_prof.data_column == 3
    assert activity_prof.header_rows in NR_OF_LINES_EXPECTED_VARIABLE_PROFILE
    assert activity_prof.schedule_file == mfh_params.dhw.fraction_schedule.schedule_file

def test_office_param_set_nominal():
    """ just test if it is possible to load params for non-residential building type, as some of the values might be zero or empty"""
    config = {}
    ureg = cesarp.common.init_unit_registry()
    sia2024 = SIA2024Facade({1: 'OFFICE'}, PassiveCoolingOperationFactory(ureg, config), ureg, config)
    sia2024.load_or_create_parameters([SIA2024BldgTypeKeys.OFFICE], variability_active=False)
    office_params = sia2024.get_building_operation(1, 1).get_operation_for_floor(0)
    activity_prof = office_params.occupancy.activity_schedule
    print(f'{activity_prof.schedule_file} column {activity_prof.data_column} header rows {activity_prof.header_rows}')
    assert activity_prof.data_column == 3
    assert activity_prof.header_rows in NR_OF_LINES_EXPECTED_NOMINAL_PROFILE
    assert activity_prof.schedule_file == office_params.dhw.fraction_schedule.schedule_file

def test_create_not_enabled():
    config = {}
    # force with an not existing folder that SIA module tries to create new parameter sets
    config["SIA2024"] = {"PARAMSETS_NOMINAL_SAVE_FOLDER": "./dummy", "PARAMSETS_VARIABLE_SAVE_FOLDER": "./dummy"}
    ureg = cesarp.common.init_unit_registry()
    sia2024 = SIA2024Facade({1: 'OFFICE'}, PassiveCoolingOperationFactory(ureg, config), ureg, config)
    with pytest.raises(CesarpException):
        sia2024.load_or_create_parameters([SIA2024BldgTypeKeys.OFFICE], variability_active=False)
    with pytest.raises(CesarpException):
        sia2024.load_or_create_parameters([SIA2024BldgTypeKeys.MFH], variability_active=True)
