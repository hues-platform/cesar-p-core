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
import re
from pathlib import Path


def scan_directory(dir_path, name_with_number_pattern, placeholder_regexp=r"(\d+)", key_is_int=True):
    """
    :param dir_path: directory which schould be scanned
    :param name_with_number_pattern: a name pattern containing one placeholder {} where a integer (e.g. the fid) is expected
    :return: dict with all directory entries matching, key beeing the number from the filename (e.g. the fid)
    """
    entry_regexp = name_with_number_pattern.format(placeholder_regexp)
    matching_entries = dict()
    for dir_entry in os.listdir(dir_path):
        match = re.search(entry_regexp, dir_entry)
        if match:
            id = match.group(1)
            if key_is_int:
                id = int(id)
            matching_entries[id] = dir_path / Path(dir_entry)
    return matching_entries
