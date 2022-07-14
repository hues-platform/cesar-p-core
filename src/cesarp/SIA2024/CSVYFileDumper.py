# coding utf-8
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
Writes SIA2024 Parameters to a csvy file (see https://csvy.org/).
Metadata about the data source and Parameters are included in YAML header, profiles are in csv format
"""
import pandas as pd
import yaml
import os
from pydoc import locate
from collections.abc import Iterable

import cesarp.common
from cesarp.common.csv_writer import _YAML_SEPARATOR, _KEY_SOURCE, _KEY_DATA, write_csv_with_header
from cesarp.common.profiles import HOURS_PER_YEAR
from cesarp.SIA2024.SIA2024Parameters import SIA2024Parameters
import cesarp.common.csv_writer

_KEY_SCHED_UNIT = "unit"
_KEY_SCHED_TYPE = "schedule_type"
_KEY_SCHED_COL = "sched_column_name"
_KEY_SCHED_LENGTH = "length"
_KEY_PARAMS = "parameters"
_KEY_CLASS = "class"
_KEY_HOUR_OF_YEAR = "hour_of_year"
_full_qualified_siaparams_classname = "cesarp.SIA2024.SIA2024Parameters.SIA2024Parameters"
_full_qualified_datadescr_classname = "cesarp.common.DatasetMetadata.DatasetMetadata"


def save_sia_param_set_to_file(filepath, sia_params: SIA2024Parameters, csv_separator=";", float_format="%.4f"):
    (parameters_of_obj, profiles_of_obj) = _convert_obj_to_dict(sia_params, skip_attributes=["data_descr"])
    profiles_frame_to_write = profiles_of_obj.set_index([list(range(1, HOURS_PER_YEAR + 1))])
    profiles_frame_to_write.index.name = _KEY_HOUR_OF_YEAR

    header_data = {
        _KEY_SOURCE: sia_params.data_descr.__dict__,
        _KEY_DATA: {_full_qualified_siaparams_classname: parameters_of_obj},
    }
    write_csv_with_header(header_data, profiles_frame_to_write, filepath, csv_separator, float_format)


def read_sia_param_set_from_file(filepath, unit_registry, csv_separator=";"):
    with open(filepath, "r") as fh:
        yaml_lines = list()
        line = fh.readline()
        yaml_header_lines = 1
        while line != _YAML_SEPARATOR:
            line = fh.readline()  # skip any unexpected header lines before the YAML block is starting
            yaml_header_lines += 1
        line = fh.readline()
        yaml_header_lines += 1
        while line != _YAML_SEPARATOR:
            yaml_lines.append(line)
            line = fh.readline()
            yaml_header_lines += 1
        schedule_file_template = cesarp.common.ScheduleFile(filepath, None, yaml_header_lines + 1, csv_separator, None, None, None)
        yaml_properties = yaml.safe_load("".join(yaml_lines))
        profile_header = pd.read_csv(fh, nrows=1, sep=csv_separator)
        parameters = yaml_properties[_KEY_DATA][_full_qualified_siaparams_classname]
        # handling of version < 2
        if "name" not in parameters.keys():
            parameters["name"] = os.path.splitext(os.path.basename(filepath))[0]
        sia_params = _init_params_from_dict(
            parameters,
            profile_header,
            _full_qualified_siaparams_classname,
            schedule_file_template,
            parameters["name"],
            unit_registry,
            skip_attributes=["data_descr"],
        )
        sia_params.data_descr = _init_params_from_dict(yaml_properties[_KEY_SOURCE], None, _full_qualified_datadescr_classname, None, None, unit_registry)
    return sia_params


def _init_params_from_dict(
    parameters,
    profiles,
    class_name,
    schedule_file_template: cesarp.common.ScheduleFile,
    schedule_name_prefix: str,
    unit_registry,
    skip_attributes=None,
):
    """
    Sub-classes are supported. The main class ("class_name") and all sub-classes have to provide an "emptyObj()" class method which returns an empty object.
    If a subclass has no members expect profiles, an entry in the YAML section with "class_name" and empty "parameters" is necessary
    :param parameters:
    :param profiles:
    :param class_name:
    :return:
    """
    if skip_attributes is None:
        skip_attributes = []
    obj_to_init = locate(class_name).emptyObj()  # type: ignore

    for attr_name in vars(obj_to_init).keys():
        if attr_name == "CLASS_VERSION":
            continue  # for the moment ignore if CLASS_VERSION, might even be not present in loaded dump
        if attr_name in skip_attributes:
            continue
        if attr_name in parameters:
            # if parameter is a sub-object, we expect class_name and parameters as entries
            if isinstance(parameters[attr_name], str):
                try:
                    val = unit_registry(parameters[attr_name])
                except Exception:
                    val = parameters[attr_name]
                setattr(obj_to_init, attr_name, val)
            if isinstance(parameters[attr_name], Iterable):
                if _KEY_CLASS in parameters[attr_name]:
                    sub_obj = _init_params_from_dict(
                        parameters[attr_name][_KEY_PARAMS],
                        profiles,
                        parameters[attr_name][_KEY_CLASS],
                        schedule_file_template,
                        schedule_name_prefix,
                        unit_registry,
                    )
                    setattr(obj_to_init, attr_name, sub_obj)
                elif _KEY_SCHED_COL in parameters[attr_name]:
                    sched = cesarp.common.ScheduleFile.from_template(schedule_file_template)
                    sched.num_hours = parameters[attr_name][_KEY_SCHED_LENGTH]
                    sched.type_limit = cesarp.common.ScheduleTypeLimits.get_limits_by_name(parameters[attr_name][_KEY_SCHED_TYPE])
                    sched.data_column = profiles.columns.get_loc(parameters[attr_name][_KEY_SCHED_COL]) + 1
                    sched.unit_of_values = unit_registry(parameters[attr_name][_KEY_SCHED_UNIT]).u
                    sched.name = f"{schedule_name_prefix}_{attr_name}"
                    setattr(obj_to_init, attr_name, sched)
            else:
                setattr(obj_to_init, attr_name, parameters[attr_name])
        else:
            raise Exception(f"could not load {class_name} from dict, attribute {attr_name} missing.")
    return obj_to_init


def _convert_obj_to_dict(obj, skip_attributes=None):
    if skip_attributes is None:
        skip_attributes = []
    parameters = {}
    profiles = pd.DataFrame()
    for attr_name, attr_value in vars(obj).items():
        if attr_name in skip_attributes:
            continue
        if isinstance(attr_value, cesarp.common.ScheduleValues):
            try:  # expecting pint Quantity
                unit = attr_value.values[0].u
                values_as_str = [val.m for val in attr_value.values]
            except Exception:
                unit = ""
                values_as_str = attr_value.values
            profiles[attr_name] = values_as_str
            parameters[attr_name] = {
                _KEY_SCHED_COL: attr_name,
                _KEY_SCHED_UNIT: str(unit),
                _KEY_SCHED_LENGTH: len(attr_value.values),
                _KEY_SCHED_TYPE: attr_value.type_limit.name,
            }
        else:
            parameters[attr_name] = str(attr_value)

    return (parameters, profiles)
