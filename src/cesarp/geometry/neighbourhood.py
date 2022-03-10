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
This module includes functions to define neighbouring and adjacent buildings.
A building is represented as a DataFrame row or pd.Series with following entries:
* 'bld_id' - unique id
* 'gis_fid' - id as assigned by external gis program
* 'height' - height of building in meter
* 'footprint_shape' - footprint of building as a pandas.DataFrame[columns=[x,y]] defining the corner vertices of the building, coordinates in meter
"""
import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, List, Iterable, Mapping
from contracts import ic

from cesarp.geometry.custom_contracts import coords_2d
from cesarp.geometry.vertices_basics import calc_distance_between_vertices


@ic(footprint_shape_a=coords_2d, footprint_shape_b=coords_2d)
def calc_distance_between_bld(footprint_shape_a, footprint_shape_b):
    """
    Returns distance between the first vertices of the two given buildings

    :param footprint_shape_a: DataFrame[columns=[x,y]] representing a footprint of a building
    :param footprint_shape_b: DataFrame[columns=[x,y]] representing a footprint of a building
    :return: distance
    """
    return calc_distance_between_vertices(footprint_shape_a.iloc[0], footprint_shape_b.iloc[0])


def search_neighbouring_buildings_for(main: Dict[str, Any], all_sitebld: pd.DataFrame, radius) -> List[Dict[str, Any]]:
    """
    Searches within the list of buildings for the buildings that are within a certain radius of the given main building.
    For the distance between the buildings the distance between their first vertex entry is used

    For building description please see module description.

    :param main: Dict defining main building
    :param radius: radius of neighbourhood
    :param all_sitebld: DataFrame defining all buildings on site
    :return: List with all neighbour buildings, each entry a dict defining teh neighbour building with entries "gis_fid", "footprint_shape", "height", "main_vertex_x", "main_vertex_y"
    """
    distance_to_neighbours = np.linalg.norm(all_sitebld[["main_vertex_x", "main_vertex_y"]].sub([main["main_vertex_x"], main["main_vertex_y"]]), axis=1)
    within_radius = all_sitebld.loc[distance_to_neighbours < radius]
    neighbours = within_radius.loc[within_radius["gis_fid"] != main["gis_fid"]]
    return neighbours.to_dict(orient="records")


def find_adjacent_footprint_vertices_for(main: Mapping[str, Any], neighbours: List[Mapping[str, Any]], max_distance_adjacency) -> Iterable[pd.DataFrame]:
    """
    Get vertices of main building which form an adjacent wall to one of the other buildings on the site

    :param main: pd.Series defining main building
    :param neighbours: neighbouring buildings which should be checked for adjacency
    :param max_distance_adjacency: maximum distance to the neighbouring building for a footprint to be considered adjacent
    :return: pd.Series of pandas.DataFrame[columns=[x,y]] with adjacent vertices from main, one entry in series per neighbour
    """
    adjacent_vertices = [get_adjacency_between(main["footprint_shape"], neigh["footprint_shape"], max_distance_adjacency) for neigh in neighbours]

    if adjacent_vertices:
        adjacent_vertices = [adjacent for adjacent in adjacent_vertices if not adjacent.empty]
    return adjacent_vertices


@ic(main_footprint=coords_2d, neighbour_footprint=coords_2d)
def get_adjacency_between(main_footprint: pd.DataFrame, footprint_to_check_for_adjacency: pd.DataFrame, max_distance_adjacency) -> pd.DataFrame:
    """
    Get vertices of main building which form an adjacent wall to neighbour building. There could be more than one wall adjacent.

    :param main: DataFrame[columns=[x,y]] representing the footprint of the main building
    :param neighbour: DataFrame[columns=[x,y]] representing a footprint of a potential adjacent building
    :return: pd.DataFrame[columns=[x,y]] with vertices of main building adjacent to neighbour. 0 to many vetices can be returned.
    """
    is_vertices_adjacent = [False] * len(main_footprint)
    for i_main_vertex, main_vertex in main_footprint.iterrows():
        is_vertices_adjacent[i_main_vertex] = any(np.linalg.norm(footprint_to_check_for_adjacency.sub(main_vertex, axis=1), axis=1) <= max_distance_adjacency)

    if all(is_vertices_adjacent):
        logging.getLogger(__name__).debug(f"checked adjacency for main building with itself, footprints are identical {main_footprint}. not returning itself as adjacent.")
        is_vertices_adjacent = [False] * len(is_vertices_adjacent)
    return main_footprint[is_vertices_adjacent]
