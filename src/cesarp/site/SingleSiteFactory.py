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
from cesarp.model.Site import Site
from cesarp.site.SiteGroundTemperatureFactory import SiteGroundTemperatureFactory
import cesarp.common
from cesarp.site import _default_config_file


class SingleSiteFactory:
    def __init__(self, weather_file_path, unit_reg, custom_config=None):
        if custom_config is None:
            custom_config = {}
        cfg = cesarp.common.load_config_for_package(_default_config_file, __package__, custom_config)
        if not os.path.isfile(weather_file_path):
            raise Exception(f"{weather_file_path} does not exist. please provide an existing file when initializing SingleSiteFactory")
        self.the_site = Site(
            weather_file_path,
            SiteGroundTemperatureFactory(unit_reg, custom_config).get_ground_temperatures(),
            cfg["SIMULATION_YEAR"],
        )

    def get_site(self, bldg_fid):
        return self.the_site
