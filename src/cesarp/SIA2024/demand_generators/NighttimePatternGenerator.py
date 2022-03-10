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
from typing import Protocol

from cesarp.common.profiles import DAYS_PER_YEAR, HOURS_PER_DAY, HOURS_PER_YEAR, MIN_HOUR_OF_DAY, MAX_HOUR_OF_DAY
from cesarp.common.profiles import profile_variability


class BaseDataForNighttimePatternProtocol(Protocol):
    def get_wakeup_hour(self) -> int:
        ...

    def get_sleeptime_hour(self) -> int:
        ...


class NighttimePatternGenerator:
    """
    Generate nighttime pattern (True for night, False for day) year profile with hourly entries.
    Base is wakeup and sleeptime hour. So each day has same pattern when variability of wakeup/sleeptime hour is not active.

    The object is specific for one building. If variability is activated, values are cached, so repeated calls to
    get_nighttime_year_profile_hourly() returns always the same pattern.
    """

    def __init__(self, base_data: BaseDataForNighttimePatternProtocol):
        """
        :param base_data: data source object, e.g. SIA2024DataAccessor
        """
        self.wakeup_hour_nominal = base_data.get_wakeup_hour()
        self.sleeptime_hour_nominal = base_data.get_sleeptime_hour()

        assert (
            self.wakeup_hour_nominal < self.sleeptime_hour_nominal
        ), f"sleep time hour {self.sleeptime_hour_nominal} before wakeup {self.wakeup_hour_nominal}, please check initialization of {__name__}. sleep time must be before or at 23h"

        self.wakeup_hour_daily = self.__get_wakeup_year_prof_daily_nom()
        self.sleeptime_hour_daily = self.__get_sleeptime_year_prof_daily_nom()

    def activate_variability(self, variability_band: int):
        """
        Use variable wakeup and sleeptime hour per day.

        :param variability_band: defining range of hours +/-; resulting hour is trimmed to 0...23h
        :return: nothing, values per day are cached
        """
        self.wakeup_hour_daily = profile_variability.randomize_vertical(
            values=self.__get_wakeup_year_prof_daily_nom(),
            band=variability_band,
            min_value=MIN_HOUR_OF_DAY,
            max_value=MAX_HOUR_OF_DAY,
        )
        self.wakeup_hour_daily = [round(x, 0) for x in self.wakeup_hour_daily]
        self.sleeptime_hour_daily = profile_variability.randomize_vertical(
            values=self.__get_sleeptime_year_prof_daily_nom(),
            band=variability_band,
            min_value=MIN_HOUR_OF_DAY,
            max_value=MAX_HOUR_OF_DAY,
        )
        self.sleeptime_hour_daily = [round(x, 0) for x in self.sleeptime_hour_daily]
        assert all(
            wake < sleep for wake, sleep in zip(self.wakeup_hour_daily, self.sleeptime_hour_daily)
        ), "variability band too big, wakeup is after sleep time for some days... please adjust variability_band for activate_variability()"

    def get_nighttime_year_profile_hourly(self):
        """
        Whetere each day of the year has the same pattern or not depends on wakeup/sleeptime hour variability, which can be set by calling activate_variability()

        :return: year profile with hourly entries, True if it is nighttime, False for day
        """

        def is_nighttime(hour_of_year_idx):
            day_index = (hour_of_year_idx) // HOURS_PER_DAY  # floor division
            hour_of_day = (hour_of_year_idx) % HOURS_PER_DAY  # modulo division, day hours start at 00 (midnight) and end at 23
            return hour_of_day < self.wakeup_hour_daily[day_index] or hour_of_day >= self.sleeptime_hour_daily[day_index]

        nighttime_hourly = [is_nighttime(h) for h in range(0, HOURS_PER_YEAR)]
        return nighttime_hourly

    def __get_wakeup_year_prof_daily_nom(self):
        return [self.wakeup_hour_nominal] * DAYS_PER_YEAR

    def __get_sleeptime_year_prof_daily_nom(self):
        return [self.sleeptime_hour_nominal] * DAYS_PER_YEAR
