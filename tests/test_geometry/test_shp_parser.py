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
import pytest
from pathlib import Path

from cesarp.geometry import _REQUIRED_SITEVERTICES_PD_COLUMNS
import cesarp.geometry.shp_input_parser

from tests.test_helpers.test_helpers import are_files_equal


def test_shp_sitevertices_parser():
    """ just a simple test if reading works... not really testing if data is read correctly """

    try:
        import geopandas
    except ModuleNotFoundError:
        pytest.skip("geopandas not available")

    sitevertices_fullfile = os.path.dirname(__file__) / Path("./testfixture/shp/test_shp_buildings.shp")
    sitevertices = cesarp.geometry.shp_input_parser.read_sitevertices_from_shp(sitevertices_fullfile)
    # required columns available?
    assert set(sitevertices.columns) == set(_REQUIRED_SITEVERTICES_PD_COLUMNS)
    # minimum is 5 vertices per building, as the startpoint must be repeated at the end
    assert sitevertices['gis_fid'].value_counts().min() >= 5
    # check if the height is always the same for the same building fid
    assert all(len(set(sitevertices[sitevertices['gis_fid']==fid]['height'])) == 1 for fid in set(sitevertices['gis_fid']))
    temp_vertices_from_shp_file = "./temp_vertices_from_shp.csv"
    sitevertices.to_csv(temp_vertices_from_shp_file, index=False)
    expected_sitevertices_file =  os.path.dirname(__file__) / Path("./expected_results/shp/SiteVerticesReadFromShp.csv")
    assert are_files_equal(temp_vertices_from_shp_file, expected_sitevertices_file), "SiteVertices generated from shp file not as expected."
    os.remove(temp_vertices_from_shp_file)


