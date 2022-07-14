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

import cesarp.common
from cesarp.site import _default_config_file
from cesarp.model.SiteGroundTemperatures import SiteGroundTemperatures


class SiteGroundTemperatureFactory:
    def __init__(self, ureg, custom_config=None):
        """
        Create an instance of SiteGroundTemperatureFactory

        :param custom_config: dict with custom configuration entries, for options see site_config.yml, key GROUND_TEMPERATURES
        """
        cfg = cesarp.common.load_config_for_package(_default_config_file, __package__, custom_config)
        cfg_ground_temps = cfg["GROUND_TEMPERATURES"]
        self.fixed_ground_temperatures = SiteGroundTemperatures(
            building_surface=ureg(cfg_ground_temps["BUILDING_SURFACE"]),
            shallow=ureg(cfg_ground_temps["SHALLOW"]),
            deep=ureg(cfg_ground_temps["DEEP"]),
            ground_temp_per_month=cfg_ground_temps["GROUND_TEMP_PER_MONTH"] * ureg(cfg_ground_temps["GROUND_TEMP_PER_MONTH_UNIT"]),
        )

    def get_ground_temperatures(self):
        return self.fixed_ground_temperatures
