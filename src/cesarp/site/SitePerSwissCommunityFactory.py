# coding=utf-8
#
# Copyright (c) 2023, Empa, Leonie Fierz, Aaron Bojarski, Ricardo Parreira da Silva, Sven Eggimann.
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
from typing import Dict, Protocol
from cesarp.model.Site import Site
from cesarp.site.SiteGroundTemperatureFactory import SiteGroundTemperatureFactory
from cesarp.weather.swiss_communities.SwissCommunityWeatherChooser import SwissCommunityWeatherChooser
import cesarp.common
from cesarp.site import _default_config_file


class WeahterChooserProtocol(Protocol):
    def get_weather_file(self, community: str) -> str:
        ...


class SitePerSwissCommunityFactory:
    def __init__(self, bldg_to_community_id_mapping: Dict[int, int], unit_reg, custom_config=None):
        """
        :param bldg_to_community_id_mapping: Dict mapping building fid to a community name
        """
        if custom_config is None:
            custom_config = {}
        self.bldg_to_community_mapping = bldg_to_community_id_mapping
        self.weather_file_chooser = SwissCommunityWeatherChooser(custom_config)
        self.ground_temps = SiteGroundTemperatureFactory(unit_reg, custom_config).get_ground_temperatures()
        cfg = cesarp.common.load_config_for_package(_default_config_file, __package__, custom_config)
        self.simulation_year = cfg["SIMULATION_YEAR"]

    def get_site(self, bldg_fid):
        community_id = self.bldg_to_community_mapping[bldg_fid]
        return Site(self.weather_file_chooser.get_weather_file(community_id), self.ground_temps, self.simulation_year)
