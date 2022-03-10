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
import logging
import pytest
from cesarp.common.profiles import profile_variability

def test_randomize_vertical():
    variable_vals = profile_variability.randomize_vertical([0.8]*12, 0.15)
    assert len(variable_vals) == 12
    for val in variable_vals:
        assert 0.8-0.15 <= val and 0.8+0.15 > val


def test_randomize_vertical_limit_max():
    max = 0.95
    variable_vals = profile_variability.randomize_vertical([0.9] * 100, 0.3, max_value=max)
    for val in variable_vals:
        assert val <= max


def test_horizontal_variability():
    profile = [h for h in range(1,25)] * 365
    assert len(profile) == 8760
    breaks = [8, 17, 24]
    profile_shuffled = profile_variability.horizontal_variability(profile, breaks)
    assert len(profile_shuffled) == len(profile)
    assert profile_shuffled != profile
    break_start_hour = 1
    for break_hour in breaks:
        profile_block = profile_shuffled[break_start_hour - 1:break_hour]
        print(profile_block)
        print(f'unshuffled would be {[i for i in range(break_start_hour,break_hour+1)]}')
        assert profile_block != [i for i in range(break_start_hour,break_hour+1)]
        assert max(profile_block) == break_hour
        assert min(profile_block) == break_start_hour
        break_start_hour = break_hour+1


def test_horizontal_variability_span_overnight():
    profile = [h for h in range(1,25)] * 365
    assert len(profile) == 8760
    breaks = [8, 21]
    profile_shuffled = profile_variability.horizontal_variability(profile, breaks)

    assert len(profile_shuffled) == len(profile)
    assert profile_shuffled != profile

    very_first_block_expected = list(range(1,9))
    very_last_block_expected = list(range(21,25))
    overnight_values_expected = very_first_block_expected + very_last_block_expected
    middle_block_expected = list(range(9,22))
    logging.debug(f'very first block {profile_shuffled[0:8]}')
    logging.debug(f'first overnight block {profile_shuffled[21:24 + 8]}, {len(profile_shuffled[21:24 + 8])}')
    logging.debug(f'first middle block {profile_shuffled[24 + 9:24 + 22]}, {len(profile_shuffled[24 + 9:24 + 22])}')
    logging.debug(f'third or so overnight block {profile_shuffled[69:79]}, {len(profile_shuffled[69:79])}')
    logging.debug(f'third or so middle block {profile_shuffled[80:93]}, {len(profile_shuffled[80:93])}')
    logging.debug(f'forth or so overnight block {profile_shuffled[94:94 + 11]}, {len(profile_shuffled[94:94 + 11])}')
    logging.debug(f'very last block {profile_shuffled[-3:len(profile_shuffled)]}')

    assert all(item in very_first_block_expected for item in profile_shuffled[0:8])
    assert all(item in overnight_values_expected for item in profile_shuffled[21:24+8])
    assert all(item in middle_block_expected for item in profile_shuffled[24+9:24+21])
    assert all(item in overnight_values_expected for item in profile_shuffled[69:79])
    assert all(item in middle_block_expected for item in profile_shuffled[80:93])
    assert all(item in middle_block_expected for item in profile_shuffled[80:93])
    assert all(item in very_last_block_expected for item in profile_shuffled[-3:len(profile_shuffled)])


def test_triang_dist():   
    orig_min = 30
    orig_max = 70
    peak = 40
    x = profile_variability.triang_dist_limits(orig_min, orig_max, peak)
    assert x[0] == pytest.approx(22.980869, abs=0.00001)
    assert x[1] == pytest.approx(80.8783009, abs=0.00001)

    # MATLAB call & solution 
    # x0 = [30 - 1, 70 + 1]
    # [x, z, exitflag]=fsolve(@(x)my_triang(x, 30, 70, 40), x0)
    # x = 22.9809   80.8792
    # z = 1.0e-05 *
    # -0.0609
    # 0.6598
    # exitflag =  1

    # function F = my_triang( x, p05, p95, c )
    # F = [((p05 - x(1))^2)/(x(2)-x(1))/(c-x(1)) - 0.05;
    # ((x(2) - p95)^2)/(x(2)-x(1))/(x(2)-c) - 0.05];
    # end
