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

import pandas as pd
import pandas.util.testing

from cesarp.geometry import vertices_basics
import cesarp.geometry.csv_input_parser as cesar_parser

__sitevertices_labels = {"gis_fid": "TARGET_FID", "height": "HEIGHT", "x": "POINT_X", "y": "POINT_Y"}

def test_sitevertices_parser():
    sitevertices_fullfile = os.path.dirname(__file__) / Path("./testfixture/SiteVertices.csv")
    flat_site_vertices = cesar_parser.read_sitevertices_from_csv(sitevertices_fullfile, __sitevertices_labels)
    sitevertices = vertices_basics.convert_flat_site_vertices_to_per_bldg_footprint(flat_site_vertices)
    for gis_fid, row in sitevertices.iterrows():
        expected_wall_vertices = pd.read_csv(
            os.path.dirname(__file__) / Path("./expected_results/building" + str(gis_fid) + ".txt"),
            header=None,
            names=["x", "y", "height"],
            index_col=None,
        )
        expected_wall_vertices.reset_index()
        expected_wall_vertices = expected_wall_vertices.astype(float)
        pandas.util.testing.assert_frame_equal(
            row["footprint_shape"], expected_wall_vertices.drop("height", axis=1)
        )

def test_sitevertices_parser_csv_heading_wrong():
    sitevertices_fullfile = os.path.dirname(__file__) / Path("./testfixture/SiteVertices.csv")
    with pytest.raises(KeyError) as e_info:
        sitevertices = cesar_parser.read_sitevertices_from_csv(
            sitevertices_fullfile,
            {"gis_fid": "TTARGET_FID", "height": "HEIGHT", "x": "POINT_X", "y": "POINT_Y"}
        )

def test_sitevertices_parser_label_keys_wrong():
    sitevertices_fullfile = os.path.dirname(__file__) / Path("./testfixture/SiteVertices.csv")
    with pytest.raises(AssertionError) as e_info:
       sitevertices = cesar_parser.read_sitevertices_from_csv(sitevertices_fullfile,
                                                              {"giss_fid": "TARGET_FID", "height": "HEIGHT", "x": "POINT_X", "y": "POINT_Y"})

