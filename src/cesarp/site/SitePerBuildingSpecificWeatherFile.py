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
from typing import Dict
import os
import logging
from pathlib import Path
from cesarp.model.Site import Site
from cesarp.site.SiteGroundTemperatureFactory import SiteGroundTemperatureFactory
import cesarp.common
from cesarp.site import _default_config_file


class SitePerBuildingSpecificWeatherFile:
    def __init__(self, bldg_to_weather_file_mapping: Dict[int, str], weather_files_folder_path, unit_reg, custom_config=None):
        """
        :param bldg_to_weather_file_mapping: Dict mapping building fid to a weather file name
        """
        if custom_config is None:
            custom_config = {}
        self.bldg_to_weather_file_mapping = bldg_to_weather_file_mapping
        self.weather_files_folder_path = weather_files_folder_path
        self.ground_temps = SiteGroundTemperatureFactory(unit_reg, custom_config).get_ground_temperatures()
        cfg = cesarp.common.load_config_for_package(_default_config_file, __package__, custom_config)
        self.simulation_year = cfg["SIMULATION_YEAR"]
        self._logger = logging.getLogger(__name__)

    def get_site(self, bldg_fid):
        weather_file_path = str(self.weather_files_folder_path / Path(self.bldg_to_weather_file_mapping[bldg_fid]))
        if not os.path.exists(weather_file_path):
            raise FileNotFoundError(f"{weather_file_path} does not exist. please provide an existing file for bldg_fid {bldg_fid} in the WEATHER_FILE_PER_BLDG_FILE")
        return Site(weather_file_path, self.ground_temps, self.simulation_year)
