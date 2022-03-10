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

from tests.test_helpers.mock_objects_generator import bldg_shape_detailed_test_site_fid2, bldg_shape_detailed_non_rect_footprint
from cesarp.geometry import area_calculator


def test_win_glass_area(bldg_shape_detailed_test_site_fid2):
    assert area_calculator.calc_window_glass_area(bldg_shape_detailed_test_site_fid2) == pytest.approx(140)

def test_wall_area_with_win(bldg_shape_detailed_test_site_fid2):
    assert area_calculator.calc_wall_area_including_windows(bldg_shape_detailed_test_site_fid2) == \
           pytest.approx(725.005+140+9.9946)

def test_wall_area_without_win(bldg_shape_detailed_test_site_fid2):
    assert area_calculator.calc_wall_area_without_window_glass_area(bldg_shape_detailed_test_site_fid2) == \
           pytest.approx(725.005+9.9946)

def test_groundfloor_area(bldg_shape_detailed_test_site_fid2):
    assert area_calculator.calc_groundfloor_area(bldg_shape_detailed_test_site_fid2) == pytest.approx(250)

def test_roof_area(bldg_shape_detailed_test_site_fid2):
    assert area_calculator.calc_roof_area(bldg_shape_detailed_test_site_fid2) == pytest.approx(250)

def test_total_floor_area(bldg_shape_detailed_test_site_fid2):
    assert area_calculator.calc_total_floor_area(bldg_shape_detailed_test_site_fid2) == pytest.approx(1250)

def test_window_frame_area(bldg_shape_detailed_test_site_fid2):
    assert area_calculator.calc_window_frame_area(bldg_shape_detailed_test_site_fid2) == pytest.approx(9.9946, 0.0001)

def test_groundfloor_area_nonrect(bldg_shape_detailed_non_rect_footprint):
    assert area_calculator.calc_groundfloor_area(bldg_shape_detailed_non_rect_footprint) == pytest.approx(250+25)

def test_roof_area_nonrect(bldg_shape_detailed_non_rect_footprint):
    assert area_calculator.calc_roof_area(bldg_shape_detailed_non_rect_footprint) == pytest.approx(250+25)

def test_total_floor_area_nonrect(bldg_shape_detailed_non_rect_footprint):
    assert area_calculator.calc_total_floor_area(bldg_shape_detailed_non_rect_footprint) == pytest.approx((250+25)*5)