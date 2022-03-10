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
import pandas.testing
import pytest
import copy
from contracts import InputContractException

import cesarp.geometry.building

MAX_GLZ_RATIO_WALL_WIDTH = 0.95

_test_data_floors = [
    pd.DataFrame({"x": [0, 0, 25, 25], "y": [0, 10, 10, 0], "z": [0, 0, 0, 0]}).astype(float),
    pd.DataFrame({"x": [0, 0, 25, 25], "y": [0, 10, 10, 0], "z": [2.5, 2.5, 2.5, 2.5]}).astype(float),
    pd.DataFrame({"x": [0, 0, 25, 25], "y": [0, 10, 10, 0], "z": [5, 5, 5, 5]}).astype(float),
]


# walls resulting from _test_data_floors
_test_data_walls = [
        [
            pd.DataFrame(
                [[0, 10, 0], [0, 0, 0], [0, 0, 2.5], [0, 10, 2.5]], columns=["x", "y", "z"]
            ).astype(float),
            pd.DataFrame(
                [[25, 10, 0], [0, 10, 0], [0, 10, 2.5], [25, 10, 2.5]], columns=["x", "y", "z"]
            ).astype(float),
            pd.DataFrame(
                [[25, 0, 0], [25, 10, 0], [25, 10, 2.5], [25, 0, 2.5]], columns=["x", "y", "z"]
            ).astype(float),
            pd.DataFrame(
                [[0, 0, 0], [25, 0, 0], [25, 0, 2.5], [0, 0, 2.5]], columns=["x", "y", "z"]
            ).astype(float),
        ],
        [
            pd.DataFrame(
                [[0, 10, 2.5], [0, 0, 2.5], [0, 0, 5], [0, 10, 5]], columns=["x", "y", "z"]
            ).astype(float),
            pd.DataFrame(
                [[25, 10, 2.5], [0, 10, 2.5], [0, 10, 5], [25, 10, 5]], columns=["x", "y", "z"]
            ).astype(float),
            pd.DataFrame(
                [[25, 0, 2.5], [25, 10, 2.5], [25, 10, 5], [25, 0, 5]], columns=["x", "y", "z"]
            ).astype(float),
            pd.DataFrame(
                [[0, 0, 2.5], [25, 0, 2.5], [25, 0, 5], [0, 0, 5]], columns=["x", "y", "z"]
            ).astype(float),
        ]
]

_test_data_walls_adjacency = [[False, True, False, True], [False, True, False, True]]


_test_data_walls_three_point_wall = copy.deepcopy(_test_data_walls)
_test_data_walls_three_point_wall[0][1] = pd.DataFrame([[25, 10, 0], [12, 5, 0], [12, 5, 2.5], [25, 10, 2.5]], columns=["x", "y", "z"]).astype(float)
_test_data_walls_three_point_wall[1][1] = pd.DataFrame([[25, 10, 2.5], [12, 5, 2.5], [12, 5, 5], [25, 10, 5]], columns=["x", "y", "z"]).astype(float)
_test_data_walls_three_point_wall[0].insert(2, pd.DataFrame([[12, 5, 0], [0, 10, 0], [0, 10, 2.5], [12, 5, 2.5]], columns=["x", "y", "z"]).astype(float))
_test_data_walls_three_point_wall[1].insert(2, pd.DataFrame([[12, 5, 2.5], [0, 10, 2.5], [0, 10, 5], [12, 5, 5]], columns=["x", "y", "z"]).astype(float))

_test_data_walls_three_adjacencies = [[False, True, True, False, True], [False, True, True, False, True]]

_test_bldg_input_data = dict()
_test_bldg_input_data["footprint_shape"] = pd.DataFrame({"x": [0, 0, 25, 25], "y": [0, 10, 10, 0]})
_test_bldg_input_data["height"] = 12.6

def stub_get_adjacent_footprint_vertices_for_test_bldg(main_bldg, neighbours, max_distance_adjacency):
    return [pd.DataFrame({"x": [0, 25], "y": [10, 10]})]

def stub_get_adjacent_footprint_vertices_no_adjacencies(main_bldg, neighbours, max_distance_adjacency):
    return [pd.DataFrame()]

def test_define_bldg_floors():
    input_bldg = _test_bldg_input_data

    input_story_height = 2
    expected_floor_z = [0.0, 2.1, 4.2, 6.3, 8.4, 10.5, 12.6]  # including ground floor and roof

    floors_result = cesarp.geometry.building.define_bldg_floors(input_bldg["footprint_shape"], input_bldg["height"], min_story_height=input_story_height)

    assert len(expected_floor_z) == len(floors_result)
    i = 0
    for floor in floors_result:
        pandas.testing.assert_frame_equal(floor[["x", "y"]], input_bldg["footprint_shape"])
        expected_z_dim = pd.Series([expected_floor_z[i]] * len(input_bldg["footprint_shape"].index))
        expected_z_dim.name = "z"
        pandas.testing.assert_series_equal(floor.z, expected_z_dim)
        i += 1


def test_define_bldg_walls_per_floor():
    result_wall_surfaces = cesarp.geometry.building.define_bldg_walls_per_floor(_test_data_floors)
    expected_wall_surfaces = _test_data_walls

    # .....frame_equal does not work for whole dataframe with nested dataframes as it seems, thus compare each entry...
    pandas.testing.assert_frame_equal(result_wall_surfaces[0][0], expected_wall_surfaces[0][0])
    pandas.testing.assert_frame_equal(result_wall_surfaces[0][1], expected_wall_surfaces[0][1])
    pandas.testing.assert_frame_equal(result_wall_surfaces[0][2], expected_wall_surfaces[0][2])
    pandas.testing.assert_frame_equal(result_wall_surfaces[0][3], expected_wall_surfaces[0][3])
    pandas.testing.assert_frame_equal(result_wall_surfaces[1][0], expected_wall_surfaces[1][0])
    pandas.testing.assert_frame_equal(result_wall_surfaces[1][1], expected_wall_surfaces[1][1])
    pandas.testing.assert_frame_equal(result_wall_surfaces[1][2], expected_wall_surfaces[1][2])
    pandas.testing.assert_frame_equal(result_wall_surfaces[1][3], expected_wall_surfaces[1][3])


def test_define_window_in_wall_preconditions():
    # test with wall having vertex 1 and 2 not on same z-position
    wall = pd.DataFrame([[0, 10, 0], [0, 10, 2.5], [0, 20, 2.5], [0, 20, 0]], columns=["x", "y", "z"]).astype(float)
    with pytest.raises(InputContractException):
        cesarp.geometry.building.define_window_in_wall(wall, 0.13, 1.5, 0.1, 0.04, MAX_GLZ_RATIO_WALL_WIDTH)


def test_define_window_in_wall_parallel_to_y():
    wall = pd.DataFrame([[0, 10, 0], [0, 0, 0], [0, 0, 2.5], [0, 10, 2.5]], columns=["x", "y", "z"]).astype(float)
    expected_window = pd.DataFrame([[0, 6.0833, 0.5], [0, 3.9167, 0.5], [0, 3.9167, 2.0], [0, 6.0833, 2]], columns=["x", "y", "z"],).astype(float)
    result_window = cesarp.geometry.building.define_window_in_wall(wall, 0.13, 1.5, 0.1, 0.04, MAX_GLZ_RATIO_WALL_WIDTH)
    pandas.testing.assert_frame_equal(result_window, expected_window, check_exact=False)


def test_define_window_in_wall_parallel_to_y_counterclock():
    wall = pd.DataFrame([[0, 0, 0], [0, 10, 0], [0, 10, 2.5], [0, 0, 2.5]], columns=["x", "y", "z"]).astype(float)
    expected_window = pd.DataFrame([[0, 3.9167, 0.5], [0, 6.0833, 0.5], [0, 6.0833, 2], [0, 3.9167, 2.0]], columns=["x", "y", "z"]).astype(float)
    result_window = cesarp.geometry.building.define_window_in_wall(wall, 0.13, 1.5, 0.1, 0.04, MAX_GLZ_RATIO_WALL_WIDTH)
    pandas.testing.assert_frame_equal(result_window, expected_window, check_exact=False)


def test_define_window_in_wall_parallel_to_x():
    wall = pd.DataFrame(
        [[25, 10, 0], [0, 10, 0], [0, 10, 2.5], [25, 10, 2.5]], columns=["x", "y", "z"]
    ).astype(float)
    expected_window = pd.DataFrame(
        [[15.2083, 10, 0.5], [9.7917, 10, 0.5], [9.7917, 10, 2], [15.2083, 10, 2.0]],
        columns=["x", "y", "z"],
    ).astype(float)
    result_window = cesarp.geometry.building.define_window_in_wall(wall, 0.13, 1.5, 0.1, 0.04, MAX_GLZ_RATIO_WALL_WIDTH)
    pandas.testing.assert_frame_equal(result_window, expected_window, check_exact=False)


def test_define_window_wall_too_small():
    wall = pd.DataFrame(
        [[25, 10, 0], [24.91, 10, 0], [24.91, 10, 2.5], [25, 10, 2.5]], columns=["x", "y", "z"]
    ).astype(float)
    result_window = cesarp.geometry.building.define_window_in_wall(wall, 0.13, 1.5, 0.1, 0.04, MAX_GLZ_RATIO_WALL_WIDTH)
    assert result_window is None


def test_define_window_window_too_small():
    wall = pd.DataFrame(
        [[25, 10, 0], [21.01, 10, 0], [21.01, 10, 2.5], [25, 10, 2.5]], columns=["x", "y", "z"]
    ).astype(float)
    result_window = cesarp.geometry.building.define_window_in_wall(wall, 0.001, 0.25, 0.1, 0.04, MAX_GLZ_RATIO_WALL_WIDTH)
    assert result_window is None


def test_define_bldg_windows():
    input_walls_per_floor = [
            # groundfloor
            [
                pd.DataFrame(
                    [[0, 10, 0], [0, 0, 0], [0, 0, 2.5], [0, 10, 2.5]], columns=["x", "y", "z"]
                ).astype(float),
                pd.DataFrame(
                    [[25, 10, 0], [0, 10, 0], [0, 10, 2.5], [25, 10, 2.5]], columns=["x", "y", "z"]
                ).astype(float),
            ],
            # firstfloor
            [
                pd.DataFrame(
                    [[0, 10, 2.5], [0, 0, 2.5], [0, 0, 5], [0, 10, 5]], columns=["x", "y", "z"]
                ).astype(float),
                pd.DataFrame(
                    [[25, 10, 2.5], [0, 10, 2.5], [0, 10, 5], [25, 10, 5]], columns=["x", "y", "z"]
                ).astype(float),
            ],
        ]


    expected_windows = [
            # groundfloor
            [
                pd.DataFrame(
                    [[0, 6.0833, 0.5], [0, 3.9167, 0.5], [0, 3.9167, 2.0], [0, 6.0833, 2]],
                    columns=["x", "y", "z"],
                ).astype(float),
                pd.DataFrame(
                    [[15.2083, 10, 0.5], [9.7917, 10, 0.5], [9.7917, 10, 2], [15.2083, 10, 2.0]],
                    columns=["x", "y", "z"],
                ).astype(float),
            ],
            # firstfloor
            [
                pd.DataFrame(
                    [[0, 6.0833, 3], [0, 3.9167, 3], [0, 3.9167, 4.5], [0, 6.0833, 4.5]],
                    columns=["x", "y", "z"],
                ).astype(float),
                pd.DataFrame(
                    [[15.2083, 10, 3], [9.7917, 10, 3], [9.7917, 10, 4.5], [15.2083, 10, 4.5]],
                    columns=["x", "y", "z"],
                ).astype(float),
            ],
        ]

    result_windows = cesarp.geometry.building.define_windows_for_walls(input_walls_per_floor, 0.13, 1.5, 0.1, 0.04, MAX_GLZ_RATIO_WALL_WIDTH)

    # .....frame_equal does not work for whole dataframe with nested dataframes as it seems, thus compare each entry...
    pandas.testing.assert_frame_equal(
        result_windows[0][0], expected_windows[0][0], check_exact=False
    )
    pandas.testing.assert_frame_equal(
        result_windows[0][1], expected_windows[0][1], check_exact=False
    )
    pandas.testing.assert_frame_equal(
        result_windows[1][0], expected_windows[1][0], check_exact=False
    )
    pandas.testing.assert_frame_equal(
        result_windows[1][1], expected_windows[1][1], check_exact=False
    )


def test_define_bldg_shape_neighbour():
    input_bldg = dict()
    input_bldg["footprint_shape"] = pd.DataFrame({"x": [0, 0, 25, 25], "y": [0, 10, 10, 0]}).astype(float)
    input_bldg["height"] = 12.6

    expected_groundfloor = pd.DataFrame({"x": [0, 0, 25, 25], "y": [0, 10, 10, 0], "z": [0, 0, 0, 0]}).astype(float)
    expected_roof = pd.DataFrame({"x": [0, 0, 25, 25], "y": [0, 10, 10, 0], "z": [12.6, 12.6, 12.6, 12.6]}).astype(float)

    expected_wall_0_0 = pd.DataFrame([[0, 10, 0], [0, 0, 0], [0, 0, 12.6], [0, 10, 12.6]], columns=["x", "y", "z"]).astype(float)

    result_bldg_shape = cesarp.geometry.building.create_bldg_shape_envelope(input_bldg)

    assert len(result_bldg_shape.walls) == 1
    assert len(result_bldg_shape.walls[0]) == 4
    pandas.testing.assert_frame_equal(
        result_bldg_shape.walls[0][0], expected_wall_0_0, check_names=False
    )

    pandas.testing.assert_frame_equal(result_bldg_shape.groundfloor, expected_groundfloor, check_names=False)
    pandas.testing.assert_frame_equal(result_bldg_shape.roof, expected_roof, check_names=False)


def test_filter_adjacent_walls():
    input_adjacency = [
                        pd.DataFrame([[25, 10], [0, 10]], index=[0, 1], columns=["x", "y"]),
                        pd.DataFrame([[0, 0], [25, 0]], index=[0, 1], columns=["x", "y"]),
                      ]

    result_adjacencies = cesarp.geometry.building.find_adjacent_walls(_test_data_walls, input_adjacency)
    assert result_adjacencies == _test_data_walls_adjacency


def test_filter_adjacent_walls_with_three_adjacent_vertices():
    input_adjacency = [
            pd.DataFrame([[25, 10], [12, 5], [0, 10]], index=[0, 1, 2], columns=["x", "y"]),
            pd.DataFrame([[0, 0], [25, 0]], index=[0, 1], columns=["x", "y"]),
        ]

    result_adjacencies = cesarp.geometry.building.find_adjacent_walls(_test_data_walls_three_point_wall, input_adjacency)
    assert result_adjacencies == _test_data_walls_three_adjacencies


def test_remove_windows_in_adjacent_walls():
    windows = cesarp.geometry.building.define_windows_for_walls(_test_data_walls,  0.13, 1.5, 0.1, 0.04, MAX_GLZ_RATIO_WALL_WIDTH)
    windows_without_adjacencies = cesarp.geometry.building.remove_windows_in_adjacent_walls(windows, _test_data_walls_adjacency)
    assert windows_without_adjacencies[0][0] is not None
    assert windows_without_adjacencies[0][1] is None

def test_create_building_shape_detailed():
    # no checking in details, but make sure creating the integration method to create a building geometry works...
    bldg_shape = cesarp.geometry.building.create_bldg_shape_detailed(
            _test_bldg_input_data,
            0.16,
            stub_get_adjacent_footprint_vertices_for_test_bldg,
            [],
            {}
    )
    assert isinstance(bldg_shape.walls, list)
    assert not bldg_shape.walls[0][0].empty
    assert isinstance(bldg_shape.windows, list)
    assert not bldg_shape.windows[0][0].empty
    assert isinstance(bldg_shape.groundfloor, pd.DataFrame)
    assert not bldg_shape.groundfloor.empty
    assert isinstance(bldg_shape.roof, pd.DataFrame)
    assert not bldg_shape.roof.empty
    assert isinstance(bldg_shape.internal_floors, list)
    assert not bldg_shape.internal_floors[0].empty
    assert isinstance(bldg_shape.adjacent_walls_bool, list)
    assert bldg_shape.adjacent_walls_bool[0][1]  # 2nd wall is adjacent
    assert isinstance(bldg_shape.window_frame, dict)

def test_check_overall_glazing_ratio_matching():
    bldg_shape = cesarp.geometry.building.create_bldg_shape_detailed(
            _test_bldg_input_data,
            0.16,
            stub_get_adjacent_footprint_vertices_no_adjacencies,
            [],
            {}
    )
    overall_bldg_glz_ratio = cesarp.geometry.building.calc_glz_ratio_for_bldg(bldg_shape)
    assert 0.16 == overall_bldg_glz_ratio  # glazing ratio matches exaclty if all walls get a window

def test_check_overall_glazing_ratio_not_matching():
    # when there are adjacent buildings, those walls get no window and thus resulting overall glazing ratio is smaller than value set
    bldg_shape = cesarp.geometry.building.create_bldg_shape_detailed(
            _test_bldg_input_data,
            0.16,
            stub_get_adjacent_footprint_vertices_for_test_bldg,
            [],
            {}
    )
    overall_bldg_glz_ratio = cesarp.geometry.building.calc_glz_ratio_for_bldg(bldg_shape)
    assert pytest.approx(0.10, abs=0.005) == overall_bldg_glz_ratio  # glazing ratio matches exaclty if all walls get a window
