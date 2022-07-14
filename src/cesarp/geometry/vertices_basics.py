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
Basic operations on 2d/3d vertices and shapes
"""
import numpy as np
import pandas as pd
from typing import Dict
from contracts import ic
from shapely.geometry import Polygon
import math

import cesarp.common
from cesarp.geometry.custom_contracts import coords_3d_raw, coords_2d_raw


def set_first_corner_as_origin(footprint_shape):
    """
    Use the first vertex defined in footprint_shape as new origin, means first vertex will be at position x=0, y=0 and all others are
    relocated accordingly in order to keep the relation between the vertices

    :param footprint_shape: pandas DataFrame defining a number of vertices as its rows
    :return: pandas DataFrame with same columns as input, first vertex beeing origin for the others
    """
    return translate_to_origin(footprint_shape.iloc[0], footprint_shape)


def translate_to_origin(new_origin, footprint_shape):
    """
    :param footprint_shape: pandas DataFrame defining a number of vertices as its rows
    :return: pandas DataFrame with same columns as input, each vertex's origin beeing translated so that new_origin
             is the origin
    """
    if footprint_shape is None:
        return None
    return footprint_shape.sub(new_origin)


def calc_distance_between_vertices(vertices_a, vertices_b):
    """
    Calculate distance between the two vertices

    :param vertices_a: DataFrame defining a vertex per row
    :param vertices_b: DataFrame defining a vertex per row
    :return: distance
    """
    return np.linalg.norm(vertices_a.sub(vertices_b).values)


def calc_proj_area_of_polygon(polygon_vertices: pd.DataFrame) -> float:
    """calculate the area projected on x-y plane of a polygon. Attention, does not work for windows and walls as projected area on x-y is 0!

    :param polygon_vertices: columns x, y, z
    :type polygon_vertices: pd.DataFrame
    :return: area (without unit)
    :rtype: floats
    """
    assert coords_3d_raw(polygon_vertices) or coords_2d_raw(polygon_vertices), "please pass a dataframe defining 2d or 3d vertices"
    vertices_as_list: np.ndarray = np.array(polygon_vertices.to_records(index=False).tolist())
    return Polygon(vertices_as_list).area


def calc_area_of_rectangle(rectangle_vertices):
    """
    Calculate the area of a rectangle given by its four corner vertices.

    :param rectangle_vertices: pandas.DataFrame with either 2d or 3d vertices
    :return: area
    """
    assert coords_3d_raw(rectangle_vertices) or coords_2d_raw(rectangle_vertices), "please pass a dataframe defining 2d or 3d vertices"
    side_a = calc_distance_between_vertices(rectangle_vertices.loc[0], rectangle_vertices.loc[1])
    side_b = calc_distance_between_vertices(rectangle_vertices.loc[1], rectangle_vertices.loc[2])
    assert math.isclose(
        abs(round(side_a, 5)), abs(round(calc_distance_between_vertices(rectangle_vertices.loc[2], rectangle_vertices.loc[3]), 5)), abs_tol=0.0001
    ), "passed vertices do not define a rectangle"
    assert math.isclose(
        abs(round(side_b, 5)), abs(round(calc_distance_between_vertices(rectangle_vertices.loc[3], rectangle_vertices.loc[0]), 5)), abs_tol=0.0001
    ), "passed vertices do not define a rectangle"
    return side_a * side_b


def calc_circumference_of_polygon(polygon_vertices):
    assert coords_3d_raw(polygon_vertices) or coords_2d_raw(polygon_vertices), "please pass a dataframe defining 2d or 3d vertices"
    return sum(
        [calc_distance_between_vertices(polygon_vertices.iloc[idx], polygon_vertices.iloc[idx + 1]) for idx in range(0, len(polygon_vertices) - 1)]
    ) + calc_distance_between_vertices(
        polygon_vertices.iloc[-1], polygon_vertices.iloc[0]
    )  # last to
    # first vertex


@ic(square_vertices=coords_3d_raw)
def calc_center_of_rectangle(rectangle_vertices) -> Dict[str, cesarp.common.NUMERIC]:
    """
    Calculate the center of a rectangle given by its four corner vertices.

    :param rectangle_vertices: pandas.DataFrame[columns=x,y,z]
    :return: center point as dict {x,y,z}
    """
    center_x = rectangle_vertices.x.mean()
    center_y = rectangle_vertices.y.mean()
    center_z = rectangle_vertices.z.mean()
    return {"x": center_x, "y": center_y, "z": center_z}


def convert_flat_site_vertices_to_per_bldg_footprint(flat_entries: pd.DataFrame):
    """
    converts flat site vertices list to pandas DataFrame with one row per FID
    "gis_fid" expected to be numeric
    :param flat_entries: pd.DataFrame with columns "gis_fid", "height", "x", "y"
    :return: pd.DataFrame with columns "gis_fid", "hight", "footprint_shape", "main_vertex_x", "main_vertex_y" where footprint_shape is a nested DataFrame
    """
    all_fid = flat_entries["gis_fid"].unique()
    all_buildings = pd.DataFrame(columns=["gis_fid", "height", "footprint_shape"])
    for fid in all_fid:
        entries_for_fid = flat_entries.loc[flat_entries["gis_fid"] == fid, ["x", "y", "height"]]
        height = entries_for_fid["height"].unique()
        assert len(height) == 1  # make sure there was the same height entry for all vertices of the current building
        entries_for_fid = entries_for_fid.drop_duplicates()  # remove duplicate vertex at end if one is present
        entries_for_fid = entries_for_fid.reset_index(drop=True)
        entries_for_fid = entries_for_fid.astype(float)
        this_building = pd.DataFrame(
            {
                "gis_fid": [fid],
                "height": [float(height[0])],
                "footprint_shape": [entries_for_fid[["x", "y"]]],
                "main_vertex_x": [entries_for_fid.loc[0, "x"]],
                "main_vertex_y": [entries_for_fid.loc[0, "y"]],
            }
        )
        all_buildings = pd.concat([all_buildings, this_building], ignore_index=True)
    all_buildings = all_buildings.astype({"gis_fid": "int"})
    all_buildings = all_buildings.set_index("gis_fid", drop=False)
    return all_buildings
