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
import logging
from cesarp.common.profiles import profile_generation
from cesarp.SIA2024.demand_generators.NighttimePatternGenerator import NighttimePatternGenerator

class mock_base_data_for_nighttime_prof:
    def __init__(self, wakeup_h, bedtime_h):
        self.wakeup_h = wakeup_h
        self.bedtime_h = bedtime_h

    def get_wakeup_hour(self):
        return self.wakeup_h

    def get_sleeptime_hour(self):
        return self.bedtime_h

def test_expand_to_yearly():
    year_profile_monthly = [0.7]*12
    day_profile_hourly = [0, 0, 0, 0, 0, 0, 0.5, 0.7, 1, 1, 1, 1, 1, 1, 1, 1, 0.8, 0.6, 0.3, 0.2, 0.2, 0, 0, 0]
    year_profile_hourly = profile_generation.expand_year_profile_monthly_to_hourly(year_profile_monthly,
                                                                                day_profile_hourly)
    assert len(year_profile_hourly) == 8760


def test_correct_weekends():
    profile = list()
    for i in range(1, 366):
        profile.extend([i]*24)

    sundays_in_jan_2020 = [5, 12, 19, 26]
    saturdays_in_jan_2020 = [4, 11, 18, 25]

    corrected_prof_one_rest_day = profile_generation.correct_weekends(profile, 1, start_date='20200101', weekend_value=0)
    assert all(rest_day not in corrected_prof_one_rest_day[0:30*24] for rest_day in sundays_in_jan_2020)
    corrected_prof_two_rest_day = profile_generation.correct_weekends(profile, 2, start_date='20200101', weekend_value=0)
    assert all(rest_day not in corrected_prof_two_rest_day[0:30*24] for rest_day in saturdays_in_jan_2020+sundays_in_jan_2020)


def test_combine_day_and_nighttime_profiles_wrong_nighttimes():
    with pytest.raises(AssertionError):
        profile_generation.combine_day_and_nighttime_profiles([1]*8760, [2]*8760, [3]*8000)
    with pytest.raises(AssertionError):
        profile_generation.combine_day_and_nighttime_profiles([1] * 8000, [2] * 8760, [3] * 8760)
    with pytest.raises(AssertionError):
        profile_generation.combine_day_and_nighttime_profiles([1] * 8760, [2] * 8000, [3] * 8760)


def test_combine_day_and_nighttime_profiles():
    logging_level_bak = logging.getLogger().level
    logging.getLogger().setLevel(logging.DEBUG)

    wakeup_h = 8
    bedtime_h = 22
    day_val = 5
    night_val = 3
    day_values = [day_val] * 8760
    night_values = [night_val] * 8760

    nighttime_pattern_gen = NighttimePatternGenerator(mock_base_data_for_nighttime_prof(wakeup_h, bedtime_h))
    nighttime_pattern = nighttime_pattern_gen.get_nighttime_year_profile_hourly()
    combined_profile = profile_generation.combine_day_and_nighttime_profiles(day_values, night_values, nighttime_pattern)
    logging.debug(f'idx 0:24, first day ({len(combined_profile[0:24])}) hours, {combined_profile[0:24]}')
    logging.debug(f'idx 0:48, first two days ({len(combined_profile[0:48])}) hours, {combined_profile[0:48]}')
    very_first_night = combined_profile[0:8]
    logging.debug(f'hour 00 to 07 (idx range 0:8), should be night ({night_val}), {very_first_night}')
    first_day = combined_profile[8:22]
    logging.debug(f'hour 08 to 21 (idx range 7:22) should be day ({day_val}), {first_day}')
    first_spanned_night = combined_profile[22:32]
    logging.debug(f'hour 22 to next day 07 (idx range 22:31) should be night ({night_val}), {len(first_spanned_night)} hours, {first_spanned_night}')
    assert all(x == night_val for x in very_first_night)
    assert all(x == day_val for x in first_day)
    assert all(x == night_val for x in first_spanned_night)
    # lets test a day somewhere in the middle, take day 10 as start hour is 10*24, thus at index 240
    logging.debug(f'230:250 {combined_profile[230:250]}')
    night_10 = combined_profile[238:248]
    day_10 = combined_profile[248:262]
    night_11 = combined_profile[262:272]
    logging.debug(f'idx range 238:248 should be night ({night_val}), {night_10}')
    logging.debug(f'idx range 248:262 should be day ({day_val}), {day_10}')
    logging.debug(f'idx range 262:272 should be night ({night_val}), {night_11}')
    assert all(x == night_val for x in night_10)
    assert all(x == day_val for x in day_10)
    assert all(x == night_val for x in night_11)
    logging.getLogger().setLevel(logging_level_bak)
