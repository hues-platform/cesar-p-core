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
from cesarp.model.BldgShape import BldgShapeDetailed
from cesarp.geometry.vertices_basics import calc_circumference_of_polygon, calc_proj_area_of_polygon, calc_area_of_rectangle
from cesarp.geometry.CesarGeometryException import CesarGeometryException


def calc_wall_area_including_windows(bldg_detailed: BldgShapeDetailed):
    try:
        total_wall_area = sum(calc_area_of_rectangle(wall) for walls_per_floor in bldg_detailed.walls for wall in walls_per_floor)
    except AssertionError:
        raise CesarGeometryException("could not calculate wall area because not all walls build a rectangle")
    return total_wall_area


def calc_wall_area_without_window_glass_area(bldg_detailed: BldgShapeDetailed):
    return calc_wall_area_including_windows(bldg_detailed) - calc_window_glass_area(bldg_detailed)


def calc_window_glass_area(bldg_detailed: BldgShapeDetailed):
    try:
        total_window_area = sum(calc_area_of_rectangle(win) for wins_per_floor in bldg_detailed.windows for win in wins_per_floor if win is not None)
    except AssertionError:
        raise CesarGeometryException("could not calculate windows area because not all windows build a rectangle")
    return total_window_area


def calc_window_frame_area(bldg_detailed: BldgShapeDetailed):
    win_frame_width = bldg_detailed.window_frame["WIDTH"]
    area_corner = win_frame_width * win_frame_width
    return sum(calc_circumference_of_polygon(win) * win_frame_width + 4 * area_corner for wins_per_floor in bldg_detailed.windows for win in wins_per_floor if win is not None)


def calc_roof_area(bldg_detailed: BldgShapeDetailed):
    return calc_proj_area_of_polygon(bldg_detailed.roof)


def calc_groundfloor_area(bldg_detailed: BldgShapeDetailed):
    return calc_proj_area_of_polygon(bldg_detailed.groundfloor)


def calc_total_floor_area(bldg_detailed: BldgShapeDetailed):
    groundfloor_area = calc_groundfloor_area(bldg_detailed)
    internal_floors_area = sum(calc_proj_area_of_polygon(floor) for floor in bldg_detailed.internal_floors)
    return groundfloor_area + internal_floors_area
