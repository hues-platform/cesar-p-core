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
"""
Create building shape data such as floors, walls and windows
"""
import logging
import math

import pandas as pd
from contracts import ic
from contracts import positive_number
from typing import List, Callable, Dict, Any, Optional

from cesarp.model.BldgShape import BldgShapeEnvelope, BldgShapeDetailed
from cesarp.common import config_loader
from cesarp.geometry import _default_config_file
from cesarp.common.CesarpException import CesarpException

from cesarp.geometry.custom_contracts import (
    coords_2d,
    coords_3d_square,
    list2d_coords_3d_square,
    iterable_coords_2d,
    list_coords_3d,
    percentage,
)
from cesarp.geometry.vertices_basics import (
    calc_center_of_rectangle,
    calc_area_of_rectangle,
    calc_distance_between_vertices,
)


@ic(footprint_shape=coords_2d, total_height=positive_number, min_story_height=positive_number)
def define_bldg_floors(footprint_shape: pd.DataFrame, total_height, min_story_height):
    """
    Define floors, including groundfloor and roof, having the shape of the building footprint.
    Number of floors is derived from the total_height and min_story_height.

    :param footprint_shape: DataFrame[columns=['x', 'y']]
    :param total_height: height of building
    :param min_story_height: optional, default is MINIMAL_STORY_HEIGHT from config
    :return: list with an entry per floor as DataFrame[columns=['x','y','z']]

    """
    num_stories = max(1, math.floor(total_height / min_story_height))
    story_height = total_height / num_stories

    floors = list()
    for floor_nr in range(0, num_stories + 1, 1):
        z_coordinates = [floor_nr * story_height] * (len(footprint_shape.index))
        floors.append(footprint_shape.assign(z=z_coordinates))

    return floors


@ic(floors=list_coords_3d)
def define_bldg_walls_per_floor(floors: List[pd.DataFrame]) -> List[List[pd.DataFrame]]:
    """
    Define walls for the building. For each story and each vertex pair of the floor shape a wall is created.

    :param floors: list(pd.DataFrame[x,y,z]); The shape of the floors on x-y plane must be the same for all floors.
                   Includes groundfloor and roof.
    :return: List[List[pd.DataFrame]] first list are the floors, then for each floor there is a list of walls as DataFrame[columns=['x','y','z']]
    """

    walls_per_floor: List[List[pd.DataFrame]] = []

    height_first_floor = floors[1].z.iloc[0]

    walls_per_floor.insert(0, [])

    # loop trough vertex for groundfloor footprint and create walls for first story
    for vertex_position in range(len(floors[0].index)):
        next_vertex_position = vertex_position + 1
        if next_vertex_position >= len(floors[0].index):
            next_vertex_position = 0  # wrap around if needed
        v1 = floors[0].iloc[next_vertex_position]
        v2 = floors[0].iloc[vertex_position]
        v3 = v2.copy()
        v3.z = height_first_floor
        v4 = v1.copy()
        v4.z = height_first_floor
        wall = pd.DataFrame([v1, v2, v3, v4]).reset_index(drop=True)
        wall = wall.astype(float)
        walls_per_floor[0].append(wall)

    # create walls for remaining stories using same footprint as the groundfloor
    for floor in range(1, len(floors) - 1):  # -1 because last floor is the roof
        story_height = floors[floor].z.iloc[0] - floors[floor - 1].z.iloc[0]
        walls_per_floor.insert(floor, [])
        for wall in walls_per_floor[floor - 1]:
            new_wall = wall.copy(deep=True)
            new_wall.z = new_wall.z + story_height
            walls_per_floor[floor].append(new_wall)

    return walls_per_floor


@ic(
    wall=coords_3d_square,
    glazing_ratio=percentage,
    window_height=positive_number,
    min_wall_width=positive_number,
    min_window_width=positive_number,
    max_glz_ratio_wall_width=percentage,
)
def define_window_in_wall(wall: pd.DataFrame, glazing_ratio, win_height, min_wall_width, min_window_width, max_glz_ratio_wall_width) -> pd.DataFrame:
    """
    Defines a window in the center of the wall
    If wall is smaller than MINIMAL_WALL_WIDTH_FOR_WINDOW or
    resulting window width is smaller than MINIMAL_WINDOW_WIDTH None is returned

    :param wall: DataFrame[columns=['x','y','z']], square parallel to z-axis with 4 corner vertices, where the first 2 are on x-y plane
    :param glazing_ratio: window to wall ratio in percentage [0...1]
    :param win_height: in meter
    :return: DataFrame[columns=['x','y','z']] defining the 4 corner vertices of the window
    """
    logger = logging.getLogger(__name__)
    wall_width = calc_distance_between_vertices(wall.loc[0], wall.loc[1])
    if wall_width < min_wall_width:
        logger.info(
            "no window modeled as wall is only %.2fm which is smaller than minimum of %fm",
            wall_width,
            min_wall_width,
        )
        return None

    wall_height = abs(wall.loc[2, "z"] - wall.loc[1, "z"])
    wall_ctr = calc_center_of_rectangle(wall)

    # glazing_ratio = window_surface/wall_surface = (window_width*window_height)/(wall_width*wall_height)
    # ratio_width = window_width/wall_width = glazing_ratio * height_wall/height_window
    gl_ratio_width = glazing_ratio * wall_height / win_height
    if gl_ratio_width >= max_glz_ratio_wall_width:
        logger.info(
            f"glazing ratio {glazing_ratio} cannot be reached. Wall width: {wall_width}, height: {wall_height} and window heigth: {win_height} would need a wall width to window width ratio of {gl_ratio_width}. Reducing to 0.95."
        )
        gl_ratio_width = max_glz_ratio_wall_width
    # Note: check that window height is smaller than wall height is implemented in create_bldg_shape_detailed()
    ctr_to_win_edge_d_x = gl_ratio_width * 0.5 * (wall.loc[1, "x"] - wall.loc[0, "x"])
    ctr_to_win_edge_d_y = gl_ratio_width * 0.5 * (wall.loc[1, "y"] - wall.loc[0, "y"])

    window = pd.DataFrame(
        [
            [wall_ctr["x"] - ctr_to_win_edge_d_x, wall_ctr["y"] - ctr_to_win_edge_d_y, wall_ctr["z"] - win_height / 2],
            [wall_ctr["x"] + ctr_to_win_edge_d_x, wall_ctr["y"] + ctr_to_win_edge_d_y, wall_ctr["z"] - win_height / 2],
            [wall_ctr["x"] + ctr_to_win_edge_d_x, wall_ctr["y"] + ctr_to_win_edge_d_y, wall_ctr["z"] + win_height / 2],
            [wall_ctr["x"] - ctr_to_win_edge_d_x, wall_ctr["y"] - ctr_to_win_edge_d_y, wall_ctr["z"] + win_height / 2],
        ],
        columns=["x", "y", "z"],
    )

    window_width = calc_distance_between_vertices(window.loc[0], window.loc[1])
    if window_width < min_window_width:
        logger.info(
            "no window modeled as it is only %f m which is smaller than minimum of %f",
            window_width,
            min_window_width,
        )
        return None

    return window


@ic(
    wall=list2d_coords_3d_square,
    glazing_ratio=percentage,
    window_height=positive_number,
    min_wall_width=positive_number,
    min_window_width=positive_number,
    max_glz_ratio_wall_width=percentage,
)
def define_windows_for_walls(walls_per_floor: List[List[pd.DataFrame]], glazing_ratio: float, win_height, min_wall_width, min_window_width, max_glz_ratio_wall_width):
    def get_window(wall):
        return define_window_in_wall(wall, glazing_ratio, win_height, min_wall_width, min_window_width, max_glz_ratio_wall_width)

    return list(map(lambda floor: list(map(lambda wall: get_window(wall), floor)), walls_per_floor))


@ic(walls=list2d_coords_3d_square, adjacent_footprint_vertices=iterable_coords_2d)
def find_adjacent_walls(walls: List[List[pd.DataFrame]], adjacent_footprint_vertices_per_neighbour: Dict[int, pd.DataFrame]) -> pd.DataFrame:
    """
    Checks for each wall if it is adjacent to another building, where the adjacency is defined by vertex pairs

    :param walls: List[List[pd.DataFrame]] list of floors, each containing list of walls as DataFrame[columns=[x,y,z]]
    :param adjacent_footprint_vertices_per_neighbour: pd.Series with an entry for each neighbour with adjacencies, containing adjacent vertex to this neighbour of main footprint shape as DataFrame [x,y]
    :return: DataFrame[index=floor_nr, columns=wall_nr] containing True if wall is adjacent, False otherwise
    """

    def check_adjacent(wall):
        if not adjacent_footprint_vertices_per_neighbour:
            return False
        is_adjacent = False
        for adjacent_footprint_vertices in adjacent_footprint_vertices_per_neighbour:
            # if all vertices of wall on 2d plane match one of the adjacent footprint vertices it is an adjacent wall
            is_adjacent |= all(
                any(set(wall_vertex_2d) == set(adj_vertex_2d) for adj_vertex_2d in adjacent_footprint_vertices.values) for wall_vertex_2d in wall.loc[:, ["x", "y"]].values
            )
        return is_adjacent

    adj_info = list(map(lambda floor: list(map(lambda wall: check_adjacent(wall), floor)), walls))
    return adj_info


def create_bldg_shape_detailed(
    bldg: pd.DataFrame,
    glazing_ratio: float,
    get_adjacent_footprint_vertices: Callable[..., pd.DataFrame],
    *args_to_get_adjacent_footprint_vertices,
    custom_config: Optional[Dict[str, Any]] = None,  # make sure to pass as a named parameter, otherwise the previous param consumes it...
) -> BldgShapeDetailed:
    """
    Define building shape as cesarp.manager.manager_protocols.BldgShapeDetailed
    Glazing ratio is applied per wall. This means, if a building has walls adjacent to the next building or walls that are too small for windows,
    those walls will be modeled without a window, resulting in a overall building glazing ratio lower than the specified one.

    :param bldg: one row defining the building for which to create the shape data
    :type bldg: DataFrame[columns=['footprint_shape', 'height']] - footprint vertices in counter-clockwise order
    :param glazing_ratio: glazing ratio per wall
    :param get_adjacent_footprint_vertices: function with at least
        1 positional parameter bldg DataFrame[columns=['footprint_shape']]  and
        returning a Series[columns=main_vertices]] with zero to many adjacent vertices as DataFrame[columns=[x,y]]
    :param args_to_get_adjacent_footprint_vertices: additional parameters for function get_adjacent_footprint_vertices
    :param custom_config: dict with custom configuration entries overwriting values from package default config
    :return: dict with keys:


    """

    cfg = config_loader.load_config_for_package(_default_config_file, __package__, custom_config)

    floors = define_bldg_floors(bldg["footprint_shape"], bldg["height"], min_story_height=cfg["MAIN_BLDG_SHAPE"]["MINIMAL_STORY_HEIGHT"])

    walls = define_bldg_walls_per_floor(floors)
    adj_footprint_vertices = get_adjacent_footprint_vertices(*((bldg,) + args_to_get_adjacent_footprint_vertices))
    adjacent_walls = find_adjacent_walls(walls, adj_footprint_vertices)

    cfg_window = cfg["MAIN_BLDG_SHAPE"]["WINDOW"]

    if cfg["MAIN_BLDG_SHAPE"]["MINIMAL_STORY_HEIGHT"] < cfg_window["HEIGHT"]:
        raise CesarpException(
            f"inconsistent configuration: minimal story height MINIMAL_STORY_HEIGHT {cfg['MAIN_BLDG_SHAPE']['MINIMAL_STORY_HEIGHT']} is smaller than window height WINDOW: HEIGHT {cfg_window['HEIGHT']}"
        )

    all_windows = define_windows_for_walls(
        walls, glazing_ratio, cfg_window["HEIGHT"], cfg_window["MIN_WALL_WIDTH_FOR_WINDOW"], cfg_window["MIN_WINDOW_WIDTH"], cfg_window["MAX_GLZ_RATIO_WALL_WIDTH"]
    )
    windows = remove_windows_in_adjacent_walls(all_windows, adjacent_walls)

    return BldgShapeDetailed(
        groundfloor=floors[0],
        roof=floors[-1],
        internal_floors=floors[1:-1],
        walls=walls,
        windows=windows,
        adjacent_walls_bool=adjacent_walls,
        window_frame=cfg_window["WINDOW_FRAME"],
    )


def calc_glz_ratio_for_bldg(bldg_shape: BldgShapeDetailed):
    wall_area = sum(map(lambda floor: sum(map(lambda wall: calc_area_of_rectangle(wall), floor)), bldg_shape.walls))

    def area_win_func(win):
        return calc_area_of_rectangle(win) if win is not None else 0

    windows_area = sum(map(lambda floor: sum(map(area_win_func, floor)), bldg_shape.windows))
    return 1 / wall_area * windows_area


def remove_windows_in_adjacent_walls(all_windows: List[List[pd.DataFrame]], adjacent_walls: List[List[bool]]):
    return [
        [win if not is_adjacent else None for (win, is_adjacent) in zip(windows_on_floor, adjacent_walls_of_floor)]
        for windows_on_floor, adjacent_walls_of_floor in zip(all_windows, adjacent_walls)
    ]


def create_bldg_shape_envelope(bldg: pd.DataFrame) -> BldgShapeEnvelope:
    """
    Define building outer envelope, with ground floor, roof and one wall per footprint-vertices pair and a glazing
    ratio for the walls.

    :param bldg: one row defining the building for which to create the shape data
    :type bldg: DataFrame[columns=['footprint_shape', 'height']]
    :return: dict according to cesarp.manager.manager_protocols.BldgShapeEnvelope

    """
    floors = define_bldg_floors(bldg["footprint_shape"], bldg["height"], min_story_height=bldg["height"])
    walls = define_bldg_walls_per_floor(floors)

    return BldgShapeEnvelope(groundfloor=floors[0], roof=floors[1], walls=walls)
