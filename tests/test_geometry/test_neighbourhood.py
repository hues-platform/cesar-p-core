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
import os
from pathlib import Path

import pandas as pd
import pandas.util.testing
import pytest

import cesarp.geometry.csv_input_parser as cesar_parser
from cesarp.geometry import vertices_basics
import cesarp.geometry.neighbourhood as cesar_nh

__sitevertices_labels = {"gis_fid": "TARGET_FID", "height": "HEIGHT", "x": "POINT_X", "y": "POINT_Y"}

def test_distance():
    assert (cesar_nh.calc_distance_between_vertices(pd.DataFrame([0, 5]), pd.DataFrame([0, 22])) == 17)
    assert (cesar_nh.calc_distance_between_vertices(pd.DataFrame([9, 0]), pd.DataFrame([-7, 0])) == 16)
    assert (cesar_nh.calc_distance_between_vertices(pd.DataFrame([16, 1]), pd.DataFrame([20, -2])) == 5)
    assert cesar_nh.calc_distance_between_vertices(pd.DataFrame([0, 0]), pd.DataFrame([-20, 10])) == \
        pytest.approx(22.36, 0.01)
    assert cesar_nh.calc_distance_between_vertices(pd.DataFrame([-20, 10]), pd.DataFrame([0, 0])) == \
        pytest.approx(22.36, 0.01)
    assert cesar_nh.calc_distance_between_vertices(pd.DataFrame([-20, 10]), pd.DataFrame([20, 20])) == \
        pytest.approx(41.23, 0.01)


def test_search_neighbouring_buildings_for():
    expected_neighbours_radius25 = [11, 55]
    expected_neighbours_radius20 = []
    expected_neighbours_radius100 = [11, 22, 33, 55]
    sitevertices_fullfile = os.path.dirname(__file__) / Path("./testfixture/SiteVertices_complex.csv")
    sitevertices_flat = cesar_parser.read_sitevertices_from_csv(sitevertices_fullfile, __sitevertices_labels)
    sitevertices = vertices_basics.convert_flat_site_vertices_to_per_bldg_footprint(sitevertices_flat)
    neighbours = cesar_nh.search_neighbouring_buildings_for(sitevertices.loc[44], sitevertices, radius=25)
    assert [neigh["gis_fid"] for neigh in neighbours] == expected_neighbours_radius25
    neighbours = cesar_nh.search_neighbouring_buildings_for(sitevertices.loc[44], sitevertices, radius=20)
    assert [neigh["gis_fid"] for neigh in neighbours] == expected_neighbours_radius20
    neighbours = cesar_nh.search_neighbouring_buildings_for(sitevertices.loc[44], sitevertices, radius=100)
    assert [neigh["gis_fid"] for neigh in neighbours] == expected_neighbours_radius100


def test_get_adjacent_buildings():
    sitevertices_fullfile = os.path.dirname(__file__) / Path("./testfixture/SiteVertices_complex.csv")
    sitevertices_flat = cesar_parser.read_sitevertices_from_csv(sitevertices_fullfile, __sitevertices_labels)
    sitevertices = vertices_basics.convert_flat_site_vertices_to_per_bldg_footprint(sitevertices_flat)
    result_adjacency = cesar_nh.find_adjacent_footprint_vertices_for(sitevertices.loc[44], sitevertices.to_dict(orient="records"), 0.1)
    expected_adjacency = pd.DataFrame([[-20, 10], [-20, 20]], index=[0, 1], columns=["x", "y"])
    pandas.util.testing.assert_frame_equal(
        result_adjacency[0],
        expected_adjacency,
        check_index_type=False,
        check_names=False,
        check_dtype=False,
    )
