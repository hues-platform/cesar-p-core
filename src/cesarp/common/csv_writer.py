#
# Copyright (c) 2021, Empa, Leonie Fierz, Aaron Bojarski, Ricardo Parreira da Silva, Sven Eggimann.
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
from typing import List, Dict, Any

import pandas as pd
import yaml

from cesarp.common.typing import NUMERIC


def write_profile_to_csv(profile: List[NUMERIC], file_name: str, format_spec=".2g", comment: str = None):
    """
    Writes profile with one data column of a number type to csv file

    :param profile: list containing profile values
    :param file_name: file name including path to write profile to
    :param format_spec: to be used for writing the numbers (no rounding)
    :param comment: string to be added as a comment line at the top of the file
    :return: nothing, profile is written to file
    """
    with open(file_name, "w") as file_handel:
        if comment:
            file_handel.write(f"# {comment}")
        for value in profile:
            file_handel.write(f"{value:{format_spec}}\n")


# def write_multiple_profiles_to_csv(profiles: Dict[int, List[cesarp.common.NUMERIC]], file_name, format_spec='.2g', comment:str=None, separator=','):
#     """ Writes profile with one data column of a number type to csv file
#
#     :param profile: list containing profile values
#     :param file_name: file name including path to write profile to
#     :param precision to be used for writing the numbers (no rounding)
#     :return: nothing, profile is written to file
#     """
#     header_row = separator.join(profiles.keys())
#     with open(file_name, "w") as file_handel:
#         if comment:
#             file_handel.write(f'# {comment}')
#         file_handel.write(header_row)
#         for value in profile:
#             file_handel.write(f'{value:{format_spec}}\n')

_CSVY_FILEFORMAT_COMMENT = "# this is a csvy file with a header block formatted as YAML followed by csv data, see csvy.org\n"
_YAML_SEPARATOR = "---\n"
_KEY_SOURCE = "METADATA"
_KEY_DATA = "DATA"


def write_csv_with_header(header_data: Dict[Any, Any], csv_data: pd.DataFrame, filepath, csv_separator=";", float_format="%.4f"):
    with open(filepath, "w") as file_handle:
        file_handle.write(_YAML_SEPARATOR)
        file_handle.write(_CSVY_FILEFORMAT_COMMENT)
        yaml.dump(header_data, file_handle)
        file_handle.write(_YAML_SEPARATOR)
        csv_data.to_csv(file_handle, index=True, sep=csv_separator, float_format=float_format, line_terminator="\n")
        logging.getLogger(__name__).debug(f"saved to {file_handle.name} successfully")
