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
import pandas as pd
import os
import logging
from pathlib import Path
import cesarp.geometry.building
from cesarp.geometry.GeometryBuilder import GeometryBuilder
from cesarp.common.CesarpException import CesarpException
from cesarp.geometry import csv_input_parser
from cesarp.geometry import vertices_basics

__sitevertices_labels = {"gis_fid": "TARGET_FID", "height": "HEIGHT", "x": "POINT_X", "y": "POINT_Y"}

_test_bldg_input_data = dict()
_test_bldg_input_data["footprint_shape"] = pd.DataFrame({"x": [0, 0, 25, 25], "y": [0, 10, 10, 0]})
_test_bldg_input_data["height"] = 12.6

_test_bldg_small_walls_input_data = dict()
_test_bldg_small_walls_input_data["footprint_shape"] = pd.DataFrame({"x": [0, 0, 25, 25.4, 25.8, 25, -0.4, -0.8, -1.2, -1.6, -2], "y": [0, 10, 10, 10, 10, 0, 0, 0, 0, 0, 0]})
_test_bldg_small_walls_input_data["height"] = 12.6

_set_glz_ratio = 0.16

def stub_get_adjacent_footprint_vertices_for_test_bldg(main_bldg, neighbours):
    return [pd.DataFrame({"x": [0, 25], "y": [10, 10]})]

def stub_no_adjacencies(main_bldg, neighbours):
    return [pd.DataFrame()]

@pytest.fixture
def bldg_shape():
    return cesarp.geometry.building.create_bldg_shape_detailed(
            _test_bldg_input_data,
            _set_glz_ratio,
            stub_get_adjacent_footprint_vertices_for_test_bldg,
            [],
            custom_config={}
            )


@pytest.fixture
def flat_site_vertices():
    sitevertices_fullfile = os.path.dirname(__file__) / Path("./testfixture/SiteVertices.csv")
    return csv_input_parser.read_sitevertices_from_csv(sitevertices_fullfile, __sitevertices_labels)


def test_glazing_ratio_check_exception(bldg_shape, flat_site_vertices):
    custom_cfg = {"GEOMETRY":
                    {"MAIN_BLDG_SHAPE":
                        {"GLAZING_RATIO_CHECK":
                            {
                                "ALLOWED_GLZ_RATIO_DEV": 0.01,
                                "EXCEPTION_ON_MISMATCH": True,
                                "DO_CHECK_BLD_WITH_ADJACENCIES": True
                            }}}}
    site_bldgs = vertices_basics.convert_flat_site_vertices_to_per_bldg_footprint(flat_site_vertices)
    geom_builder = GeometryBuilder(2, site_bldgs, _set_glz_ratio, custom_cfg)
    with pytest.raises(CesarpException):
        geom_builder._check_glz_ratio(bldg_shape)


def test_glz_ratio_check_logging(bldg_shape, flat_site_vertices, caplog):
    custom_cfg = {"GEOMETRY":
                    {"MAIN_BLDG_SHAPE":
                        {"GLAZING_RATIO_CHECK":
                            {
                                "ALLOWED_GLZ_RATIO_DEV": 0.01,
                                "EXCEPTION_ON_MISMATCH": True,
                                "DO_CHECK_BLD_WITH_ADJACENCIES": False
                            }}}}
    site_bldgs = vertices_basics.convert_flat_site_vertices_to_per_bldg_footprint(flat_site_vertices)
    geom_builder = GeometryBuilder(2, site_bldgs, _set_glz_ratio, custom_cfg)

    with caplog.at_level(logging.WARNING):
        geom_builder._check_glz_ratio(bldg_shape)


def test_glz_ratio_check_ignore_adjacent_bldg(bldg_shape, flat_site_vertices):
    custom_cfg = {"GEOMETRY":
                    {"MAIN_BLDG_SHAPE":
                        {"GLAZING_RATIO_CHECK":
                            {
                                "ALLOWED_GLZ_RATIO_DEV": 0.01,
                                "EXCEPTION_ON_MISMATCH": True,
                                "DO_CHECK_BLD_WITH_ADJACENCIES": False
                            }}}}
    site_bldgs = vertices_basics.convert_flat_site_vertices_to_per_bldg_footprint(flat_site_vertices)
    geom_builder = GeometryBuilder(2, site_bldgs, _set_glz_ratio, custom_cfg)

    # adjacent walls without window, thus glz ratio smaller but no exception
    assert _set_glz_ratio > geom_builder._check_glz_ratio(bldg_shape)


def test_glz_ratio_check_walls_too_small(flat_site_vertices, caplog):
    custom_cfg = {"GEOMETRY":
                    {"MAIN_BLDG_SHAPE":
                        {"GLAZING_RATIO_CHECK":
                            {
                                "ALLOWED_GLZ_RATIO_DEV": 0.005,
                                "EXCEPTION_ON_MISMATCH": False,
                                "DO_CHECK_BLD_WITH_ADJACENCIES": False
                            },
                        "WINDOW":
                            {
                                "MIN_WALL_WIDTH_FOR_WINDOW":  0.5,  # meter
                                "MIN_WINDOW_WIDTH":           0.08 # meter
                            }
                        }}}

    bldg_shape_small_walls = cesarp.geometry.building.create_bldg_shape_detailed(
            _test_bldg_small_walls_input_data,
            _set_glz_ratio,
            stub_no_adjacencies,
            [],
            custom_config=custom_cfg
            )

    site_bldgs = vertices_basics.convert_flat_site_vertices_to_per_bldg_footprint(flat_site_vertices)
    geom_builder = GeometryBuilder(2, site_bldgs, _set_glz_ratio, custom_cfg)
    with caplog.at_level(logging.WARNING):
        overall_glz_ratio = geom_builder._check_glz_ratio(bldg_shape_small_walls)

    assert pytest.approx(0.1548, abs=0.001) == overall_glz_ratio
