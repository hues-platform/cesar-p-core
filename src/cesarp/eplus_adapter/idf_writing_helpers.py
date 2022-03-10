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
import logging
import pint
import cesarp.eplus_adapter.idf_strings as idf_strings
import cesarp.common


def exists_in_idf(idf, obj_type, obj_name):
    bunch = idf.idfobjects[obj_type]
    matching = [entry for entry in bunch if entry.Name.upper() == obj_name.upper()]
    if len(matching) == 1:
        logging.getLogger(__name__).debug(f"{obj_type} with name {obj_name} already in idf, just returning its name")
        return True
    elif len(matching) > 1:
        raise Exception(f"more than one {obj_type} object with name {obj_name}")
    return False


def add_type_limits(idf, type_lim_to_add):
    """Check if given type_limit already exists in the IDF, if not add it.
    :param idf IDF object
    :param type_lim_to_add cesarp.common.ScheduleTypeLimits
    :return: name of type limit idf object;
    """
    name = type_lim_to_add.name
    if not exists_in_idf(idf, idf_strings.IDFObjects.schedule_type_limits, name):
        logging.getLogger(__name__).debug(f"adding schedule type limit {type_lim_to_add.name} to idf")
        # no default values because we do not need to set 'Unit Type' as it is only for IDF Editor
        type_lim_idf_obj = idf.newidfobject(idf_strings.IDFObjects.schedule_type_limits, defaultvalues=False)
        type_lim_idf_obj.Name = name
        if type_lim_to_add.min_value is not None:
            type_lim_idf_obj.Lower_Limit_Value = type_lim_to_add.min_value
        if type_lim_to_add.max_value is not None:
            type_lim_idf_obj.Upper_Limit_Value = type_lim_to_add.max_value
        if type_lim_to_add.value_type is not None:
            type_lim_idf_obj.Numeric_Type = idf_strings.NumericType.get_num_type_for(type_lim_to_add.value_type)

    return name


def add_constant_schedule(idf, constant_value, type_limit):
    name = idf_strings.CustomObjNames.constant_schedule.format(constant_value)
    idf_obj_type = idf_strings.IDFObjects.schedule_const
    if not exists_in_idf(idf, idf_obj_type, name):
        type_idf_obj_name = add_type_limits(idf, type_limit)
        sched_idf_obj = idf.newidfobject(idf_obj_type)
        sched_idf_obj.Name = name
        sched_idf_obj.Schedule_Type_Limits_Name = type_idf_obj_name
        sched_idf_obj.Hourly_Value = constant_value
    return name


def add_schedule(idf, schedule, required_unit: pint.Unit = None, required_type: cesarp.common.ScheduleTypeLimits = None):
    """
    :param idf: IDF
    :param schedule: cesarp.common.ScheduleFile or cesarp.common.ScheduleFixedValue object
    :param ureg: instance of pint unit registry
    :param required_unit: unit the values of the schedule have to be
    :param required_type: required schedule type
    :param name: if no name is provided, by default the file name is used; provide a name if same file contains several profiles
    :return: idf obj name of schedule
    """
    assert required_unit or required_type, "please define required_unit or required_type when calling add_schedule(...)"
    if required_type is not None and schedule.type_limit != required_type:
        raise Exception(f"type {schedule.type_limit.name} does not match required {required_type.name} while writing schedule")
    if isinstance(schedule, cesarp.common.ScheduleFile):
        if required_unit is not None and pint.Unit(schedule.unit_of_values) != required_unit:
            raise Exception(f"unit {schedule.unit_of_values} does not match required unit {str(required_unit)} for schedule {schedule.name}")
        return add_file_schedule(idf, schedule)
    elif isinstance(schedule, cesarp.common.ScheduleFixedValue):
        if required_unit is not None and schedule.value.u != required_unit:
            raise Exception(f"unit {schedule.value.u} does not match required unit {required_unit} for fixed schedule with value {schedule.value.m}")
        return add_constant_schedule(idf, schedule.value.m, schedule.type_limit)
    else:
        raise Exception(f"unknown Schedule type {type(schedule)}")


def add_file_schedule(idf, schedule: cesarp.common.ScheduleFile):
    if not exists_in_idf(idf, idf_strings.IDFObjects.schedule_file, schedule.name):
        schedule_idf_obj = idf.newidfobject(idf_strings.IDFObjects.schedule_file)
        schedule_idf_obj.Name = schedule.name
        type_idf_obj_name = add_type_limits(idf, schedule.type_limit)
        schedule_idf_obj.Schedule_Type_Limits_Name = type_idf_obj_name
        schedule_idf_obj.File_Name = str(schedule.schedule_file)
        schedule_idf_obj.Column_Number = schedule.data_column
        schedule_idf_obj.Rows_to_Skip_at_Top = schedule.header_rows
        schedule_idf_obj.Number_of_Hours_of_Data = schedule.num_hours
        schedule_idf_obj.Column_Separator = idf_strings.Separator.get_for_char(schedule.separator)
    return schedule.name


def add_monthly(epbunch, values, name_pattern):
    for idx, month in enumerate(idf_strings.months):
        var_name = name_pattern.format(month)
        setattr(epbunch, var_name, values[idx])
