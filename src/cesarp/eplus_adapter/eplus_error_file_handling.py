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
Module providing functions to parse energyplus error file.
"""
import mmap
from enum import Enum
import re
from typing import Union
from pathlib import Path


EPLUS_ERROR_FILE_NAME = "eplusout.err"


class EplusErrorLevel(Enum):
    IP_NOTE = 4
    WARNING = 3
    SEVERE = 2
    FATAL = 1
    NO_ERRORS = 99
    UNKNOWN = 999  # used for backward compatibility, if containers are loaded which do not have that entry defined


eplusout_err_identifiers = {
    EplusErrorLevel.IP_NOTE: "** Warning ** IP: Note --",
    EplusErrorLevel.WARNING: "** Warning **",
    EplusErrorLevel.SEVERE: "** Severe **",
    EplusErrorLevel.FATAL: "**  Fatal  **",
}

eplusout_ignored_warnings = ["** Warning ** IP: Note -- Some missing fields have been filled with defaults. See the audit output file for details."]


def check_eplus_error_level(eplus_err_file: Union[str, Path]) -> EplusErrorLevel:
    """
    Returns the most severe error level found in the given energyplus error log file

    :param eplus_err_file ([str]): full path to energyplus error file (usually named eplusout.err)

    :return EplusErrorLevel stating the most critical error found in the log file, EplusErrorLevel.NO_ERRORS if all is good
    """
    with open(eplus_err_file, "rb", 0) as err_file, mmap.mmap(err_file.fileno(), 0, access=mmap.ACCESS_READ) as err_file_content:
        err_levels_sorted = sorted(list(eplusout_err_identifiers.keys()), key=lambda err_lev: err_lev.value)
        for err_level_key in err_levels_sorted:
            identifier_to_search = bytearray(map(ord, eplusout_err_identifiers[err_level_key]))
            if err_level_key == EplusErrorLevel.WARNING:
                # match ** Warning **, but not ** Warning ** -- IP Note
                the_regex = re.compile(br"(?!\s*\*\*\sWarning\s\*\*\s+.*IP:\sNote\s+--.*)(?=\s*\*\*\sWarning\s\*\*\.*).*")
                if re.search(the_regex, err_file_content):  # type: ignore
                    return EplusErrorLevel.WARNING
            elif err_file_content.find(identifier_to_search) != -1:
                return err_level_key
    return EplusErrorLevel.NO_ERRORS
