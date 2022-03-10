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
from typing import List, Sequence

from cesarp.common.profiles import DAYS_PER_MONTH, HOURS_PER_DAY, HOURS_PER_YEAR


def correct_weekends(year_profile_hourly, nr_of_weekend_days, weekend_value, start_date):
    """
    Sets profile values on weekend to passed value.
    :param year_profile_hourly: profile for one year with hourly values
    :param nr_of_weekend_days: 0, 1 (sunday) or 2 (saturday/sunday) rest days; defines "weekend days"
    :param weekend_value: value to be set in profile for all hours on weekend days
    :param start_date: Start date of profile. Used to define which profile hours are on a weekend day
    :return: year profile with hourly values, original value on non-weekend days, weekend_Value on weekend days
    """

    if nr_of_weekend_days == 0:
        return year_profile_hourly
    elif nr_of_weekend_days == 1:
        rest_days = [6]  # sunday
    elif nr_of_weekend_days == 2:
        rest_days = [5, 6]  # saturday/sunday
    else:
        raise Exception(f"only zero, one or two weekend/rest days supported, given {nr_of_weekend_days}")

    weekday_per_hour = pd.date_range(start_date, periods=HOURS_PER_YEAR, freq="H").dayofweek
    assert len(weekday_per_hour) == len(
        year_profile_hourly
    ), f"make sure passed start_date {start_date} giving year with {len(weekday_per_hour)} hours matches profile year with {len(year_profile_hourly)} hours (attention to leap years)"

    return [weekend_value if weekday in rest_days else prof_val for prof_val, weekday in zip(year_profile_hourly, weekday_per_hour)]


def define_fix_nighttime_value(daytime_year_profile_hourly, fixed_nighttime_value, nighttime_pattern_year_profile_hourly: List[bool]):
    return combine_day_and_nighttime_profiles(daytime_year_profile_hourly, [fixed_nighttime_value] * HOURS_PER_YEAR, nighttime_pattern_year_profile_hourly)


def combine_day_and_nighttime_profiles(daytime_year_profile_hourly, nighttime_year_profile_hourly, nighttime_pattern_year_profile_hourly: Sequence[bool]):
    """
    Combine a profile defining values during day with one defining values during nighttime with given wakeup and bedtime hours per day

    :param daytime_year_profile_hourly: profile for one year with hourly values
                                        profile values during nighttime are not used (they will be overwritten), but profile has to have every hour of the year defined
    :param nighttime_year_profile_hourly: profile for one year with hourly values which should replace the original ones during nighttime (between bedtime and wakeup)
                                          profile values during daytime are not used (they are left on the original values from year_profile_hourly), but profile has to have every hour of the year defined
    :param nighttime_pattern_year_profile_hourly: profile for one year with hourly entries, True if it is night, False otherwise
    :return: year profile with hourly values, the values from year_profile_hourly during day and values from nighttime_year_profile_hourly during night

    """
    daytime_prof_length = len(daytime_year_profile_hourly)
    assert len(nighttime_year_profile_hourly) == daytime_prof_length and len(nighttime_pattern_year_profile_hourly) == daytime_prof_length, (
        f"daytime ({len(daytime_year_profile_hourly)}), "
        f"nighttime ({len(nighttime_year_profile_hourly)}) and "
        f"nighttime pattern ({len(nighttime_pattern_year_profile_hourly)}) profiles must have same length"
    )

    corrected_profile = [
        night_val if is_night else day_val
        for day_val, night_val, is_night in zip(daytime_year_profile_hourly, nighttime_year_profile_hourly, nighttime_pattern_year_profile_hourly)
    ]

    return corrected_profile


def expand_year_profile_monthly_to_hourly(year_profile_monthly, day_profile_hourly):
    """
    Expands a profile with monthly values to a profile for one year with hourly values overlaying an daily profile.
    This means, each day of the same month will have the same 24h profile.
    No variability or randomization is introduced within this method.

    :param year_profile_monthly: profile for one year with monthly values (12 values)
    :param day_profile_hourly: profile for one day with hourly values (24 values), used for each day of the year
    :return: profile for one year with hourly values

    """
    assert len(year_profile_monthly) == 12, f"year_profile_monthly should have 12 values, but has {len(year_profile_monthly)}"
    assert len(day_profile_hourly) == HOURS_PER_DAY, f"day_profile_hourly should have {HOURS_PER_DAY} values, but has {len(day_profile_hourly)}"
    year_profile_hourly_nested = [
        [monthly_value * hourly_value for hourly_value in day_profile_hourly] * DAYS_PER_MONTH[idx] for idx, monthly_value in enumerate(year_profile_monthly)
    ]

    year_profile_hourly = [item for sublist in year_profile_hourly_nested for item in sublist]
    return year_profile_hourly
