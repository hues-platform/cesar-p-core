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

from pathlib import Path
import logging
import pandas as pd
from typing import Dict, Any, Optional
from cesarp.weather.swiss_communities import _default_config_file
import cesarp.common


class SwissCommunityWeatherChooser:
    """
    The class provides assignment of weather files for Switzerland based on the community name.
    There are 53 weather stations in Switzerland, for which weather data is available from Meteonorm.
    Based on a lookup table mapping each community to one of those weather stations the assignment of the weather file is made.
    """

    def __init__(self, custom_config: Optional[Dict[str, Any]] = None):
        """
        Create an instance of SwissCommunityWeatherChooser

        :param custom_config: dict with custom configuration entries, for options see swiss_communities_weather.yml
        """
        self.cfg = cesarp.common.load_config_for_package(_default_config_file, __package__, custom_config)
        self.communityID_to_stationID = self.__read_community_station_mapping(self.cfg["COMMUNITY_TO_STATION"])

    def get_weather_file(self, community_id: int):
        try:
            weather_station = self.communityID_to_stationID.loc[community_id]["station_name"]
        except KeyError:
            raise Exception(f"no weather station found for community: {community_id}")

        weather_file_name = weather_station + "." + self.cfg["WEATHER_FILES"]["EXTENSION"]
        weather_station_file_as_path = self.cfg["WEATHER_FILES"]["PATH"] / Path(weather_file_name)
        if not weather_station_file_as_path.is_file():
            raise Exception(f"for community {community_id} assigned weather file {str(weather_station_file_as_path)} not found on disk")
        logging.getLogger(__name__).info(f"{community_id} weather file {str(weather_station_file_as_path)} was assigned")
        return str(weather_station_file_as_path)

    @staticmethod
    def __read_community_station_mapping(cfg_com_to_station: Dict[str, Any]) -> pd.DataFrame:
        """
        :param cfg_com_to_station: configuration dict for community_to_station file
        :return: Dataframe with content of file, column "community_id" with community BFS nr and "station_id" with numeric station-id
        """
        return cesarp.common.read_csvy(
            cfg_com_to_station["PATH"],
            ["community_id", "station_name"],
            cfg_com_to_station["LABELS"],
            cfg_com_to_station["SEPARATOR"],
            index_column_name="community_id",
        )
