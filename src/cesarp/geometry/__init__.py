# -*- coding: utf-8 -*-
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
geometry
============

Package providing functionality for importing building shape data and
identifying neighbour and adjacent buildings for a certain center building.

The classes/modules built to be used from outside (API of package):

=============================================================== ===========================================================
class/module                                                    description
=============================================================== ===========================================================
:py:mod:`cesarp.geometry.area_calculator`                       calculate different areas of a model.BldgShapeDetailed

:py:class:`cesarp.geometry.GeometryBuilderFactory`              create GeometryBuilder instance for different building on same site

:py:class:`cesarp.geometry.GeometryBuilder`                     this is the main class of this package, which
                                                                creates a full building geometry from footprint and height, for the main
                                                                building to be simulated and the more simple geometries for its neighbours

:py:mod:`cesarp.geometry.csv_input_parser`                      For reading the site vertices form file, the dataframe returned
:py:mod:`cesarp.geometry.shp_input_parser`                      can be fed into .. py:class:: name cesarp.geometry.GeometryBuilderFactory

:py:mod:`cesarp.geometry.verticse_basics`                       use the convert_flat_site_vertices_to_per_bldg_footprint method
                                                                to convert the site vertices read from an input to the structure
                                                                reuqired by GeometryBuilder
=============================================================== ===========================================================

"""

import os
from pathlib import Path

_default_config_file = os.path.dirname(__file__) / Path("default_config.yml")
_REQUIRED_SITEVERTICES_PD_COLUMNS = ["gis_fid", "height", "x", "y"]
