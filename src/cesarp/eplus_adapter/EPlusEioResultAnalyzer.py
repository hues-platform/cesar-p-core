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
import pandas as pd
import pint
from typing import Dict, Any, Optional
from pathlib import Path

import cesarp.common
from cesarp.eplus_adapter import _default_config_file


class EPlusEioResultAnalyzer:
    """
    Reads information out of the "eio" energy plus output file for a single building.
    Building element areas (walls, windows,...) are also calculated from geometry data in cesar-p.
    """

    _EIO_FILE_NAME = "eplusout.eio"

    def __init__(self, result_folder_path: str, ureg: pint.UnitRegistry, custom_config: Optional[Dict[str, Any]] = None):
        """
        Initialization

        :param result_folder_path: folder containing the "eplusout.eio" (see _EIO_FILE_NAME) to be read
        :param ureg: unit registry
        :param custom_config: customized configuration, can override the default config for formatting and positions of the data in the eio file
        """
        self.ureg = ureg
        self._cfg_eio_reader = cesarp.common.config_loader.load_config_for_package(_default_config_file, __package__, custom_config)["EIO_READER"]
        self.zone_info = self._read_zone_information(result_folder_path)
        self.area_unit = self.ureg(self._cfg_eio_reader["AREA_UNIT"])
        self.floor_area_header_key = self._cfg_eio_reader["FLOOR_AREA_HEADER"]

    def get_total_floor_area(self) -> pint.Quantity:
        """

        :return: Total floor area of all zones of the building
        """
        return sum(self.zone_info[self.floor_area_header_key]) * self.area_unit

    def _read_zone_information(self, result_folder_path):
        zone_summary_start_tag = self._cfg_eio_reader["ZONE_SUMMARY_START_TAG"]
        zone_info_offset_cnt = self._cfg_eio_reader["ZONE_INFO_TO_SUMMARY_OFFSET"]
        sep = self._cfg_eio_reader["SEPARATOR"]

        with open(result_folder_path / Path(self._EIO_FILE_NAME)) as fh:
            line = fh.readline()
            while line and line.find(zone_summary_start_tag) != 0:  # tag must be at the beginning of the line
                line = fh.readline()  # skip any unexpected header lines before the YAML block is starting
            summary_line = fh.readline()
            nr_of_zones = summary_line.split(sep)[self._cfg_eio_reader["IDX_NR_OF_ZONES"]]
            while zone_info_offset_cnt != 0:
                line = fh.readline()
            zone_info = pd.read_csv(fh, nrows=int(nr_of_zones), sep=sep)

        zone_info.rename(columns=lambda x: x.strip(), inplace=True)
        return zone_info
