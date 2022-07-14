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
import pandas as pd
import pint
from typing import Dict, Any, Optional
from cesarp.geometry.GeometryBuilder import GeometryBuilder
from cesarp.manager.manager_protocols import GeometryBuilderProtocol
from cesarp.geometry import vertices_basics


class GeometryBuilderFactory:
    """
    Factory class to create GeometryBuilder instances.
    This reason for this class is to hold the _site_bldgs dataframe to avoid reading the same site vertices file
    several times if simulating several buildings on the same site (which is the CESAR-P default workflow).
    """

    def __init__(self, flat_site_vertices_list: pd.DataFrame, ureg: pint.UnitRegistry, custom_config: Optional[Dict[str, Any]] = None):
        self._site_bldgs = vertices_basics.convert_flat_site_vertices_to_per_bldg_footprint(flat_site_vertices_list)
        self._custom_config = custom_config
        self.ureg = ureg

    def get_geometry_builder(self, bldg_fid, glazing_ratio) -> GeometryBuilderProtocol:
        if isinstance(glazing_ratio, pint.Quantity):
            glazing_ratio = glazing_ratio.to(self.ureg.dimensionless).m
        return GeometryBuilder(bldg_fid, self._site_bldgs, glazing_ratio, self._custom_config)
