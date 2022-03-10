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
import pytest
import os
from pathlib import Path
import cesarp.common
from cesarp.weather.swiss_communities.SwissCommunityWeatherChooser import SwissCommunityWeatherChooser
from cesarp.site.SitePerSwissCommunityFactory import SitePerSwissCommunityFactory

__SITE_DEEP_TEMP = 14
__SITE_GROUND_TEMP_NOV = 9.8

def get_testfixture_config():
    community_to_station_file = os.path.dirname(__file__) / Path("./testfixture/Testfixture_Gemeinde_to_WeatherStation.csv")
    weather_files_folder = os.path.dirname(__file__) / Path("./testfixture/weather_files")
    weather_confg = {
        'WEATHER':
            {
                'SWISS_COMMUNITIES':
                    {
                        'COMMUNITY_TO_STATION':
                            {'PATH': community_to_station_file,
                             'LABELS':
                                 {'community_id': "BFS Gde-nummer",
                                  'station_name': "WeatherStationName"}
                             },
                        'WEATHER_FILES':
                            {'PATH': weather_files_folder}
                    }
            },
        'SITE':
            {
                'GROUND_TEMPERATURES':
                    {
                        'DEEP': f'{__SITE_DEEP_TEMP} degC',
                        'GROUND_TEMP_PER_MONTH': [1.6, 0.7, 2.3, 4.8, 11.2, 16.2, 19.6, 20.6, 18.9, 15, __SITE_GROUND_TEMP_NOV, 5],
                        'GROUND_TEMP_PER_MONTH_UNIT': 'degC'
                    }

            }
    }
    return weather_confg

@pytest.fixture
def weather_chooser():
    return SwissCommunityWeatherChooser(get_testfixture_config())


def test_weather_file_chooser(weather_chooser):
    weather_file_duebendorf = weather_chooser.get_weather_file(191)
    assert "Zürich-SMA" in weather_file_duebendorf
    assert os.path.exists(weather_file_duebendorf)


def test_weather_chooser_community_not_found(weather_chooser):
    with pytest.raises(Exception) as e_info:
        weather_chooser.get_weather_file("NotExistingCommunity")


def test_weather_pointing_to_nonexisting_file(weather_chooser):
    with pytest.raises(Exception) as e_info:
        weather_chooser.get_weather_file("TestOrt")


def test_ch_site_factory():
    ureg = cesarp.common.init_unit_registry()
    fid_to_community = {1: 191, # Dübendorf
                        2: 152, # Herrliberg
                        3: 3681, # Avers
                        4: 751} # Täuffelen
    myfact = SitePerSwissCommunityFactory(fid_to_community, ureg, get_testfixture_config())
    assert "Davos" in myfact.get_site(3).weather_file_path
    assert "Bern" in myfact.get_site(4).weather_file_path
    duebi = myfact.get_site(1)
    assert duebi.site_ground_temperatures.deep == ureg.Quantity(__SITE_DEEP_TEMP, ureg.degC)
    assert duebi.site_ground_temperatures.ground_temp_per_month[10] == ureg.Quantity(__SITE_GROUND_TEMP_NOV, ureg.degC)

def test_default_package_config():
    weather_chooser = SwissCommunityWeatherChooser()
    assert "Zuerich-SMA.epw" in weather_chooser.get_weather_file(69)



