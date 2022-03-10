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
common
============================

Everything shared by several packages and overall concepts.

Actually all classes or modules are expected to be used from outside,
so please go through the classes and modules directly.

"""

import os
import pint
import logging
import warnings
from datetime import datetime
from pathlib import Path
from cesarp.common.typing import NUMERIC  # noqa: F401, E402
from cesarp.common.AgeClass import AgeClass  # noqa: F401, E402
from cesarp.common.config_loader import load_config_full  # noqa: F401, E402
from cesarp.common.config_loader import load_config_for_package  # noqa: F401, E402
from cesarp.common.config_loader import merge_config_recursive  # noqa: F401, E402
from cesarp.common.config_loader import abs_path  # noqa: F401, E402
from cesarp.common.csv_reader import read_csvy  # noqa: F401, E402
from cesarp.common.csv_writer import write_profile_to_csv  # noqa: F401, E402
from cesarp.common.ScheduleFile import ScheduleFile  # noqa: F401, E402
from cesarp.common.ScheduleFixedValue import ScheduleFixedValue  # noqa: F401, E402
from cesarp.common.ScheduleTypeLimits import ScheduleTypeLimits  # noqa: F401, E402
from cesarp.common.ScheduleValues import ScheduleValues  # noqa: F401, E402
import cesarp.common.version_info as version_info  # noqa: F401, E402

TIMESTAMP_FORMAT = "%d/%m/%Y %H:%M:%S"
_CESAR_PINT_DEFS = str(os.path.dirname(__file__) / Path("myPintDefs.txt"))


def init_unit_registry() -> pint.UnitRegistry:
    ureg = pint.UnitRegistry()
    logging.getLogger(__name__).debug(f"loading cesar specific unit for pint from {_CESAR_PINT_DEFS}, registry is {ureg}")
    tmp_log_level = pint.util.logger.getEffectiveLevel()
    # TODO check if we can avoid pint Redefine of d, W, h ... for now just suppress the warnings
    pint.util.logger.setLevel(logging.ERROR)
    ureg.load_definitions(_CESAR_PINT_DEFS)
    pint.util.logger.setLevel(tmp_log_level)
    # deactive some pint version changes output
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        pint.Quantity([])
    # allow to read a temperature like 14 degC from configuration
    ureg.autoconvert_offset_to_baseunit = True
    pint.set_application_registry(ureg)  # needed for pickle / unpickle with jsonpickle
    return ureg


def get_class_from_str(class_str: str) -> type:
    from importlib import import_module

    try:
        module_path, class_name = class_str.rsplit(".", 1)
        module = import_module(module_path)
        class_type = getattr(module, class_name)
    except (ImportError, AttributeError) as e:
        raise ImportError(class_str, e)
    return class_type


def get_current_timestamp():
    return format_datetime(datetime.now())


def format_datetime(the_date: datetime):
    return the_date.strftime(TIMESTAMP_FORMAT)


def get_fully_qualified_classname(obj):
    return obj.__class__.__module__ + "." + obj.__class__.__name__
