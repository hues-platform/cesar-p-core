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
from typing import Protocol
import cesarp.model.BuildingOperationMapping
import cesarp.model.Site
from cesarp.model.BldgShape import BldgShapeDetailed


class GeometryBuilderProtocol(Protocol):
    def get_bldg_shape_detailed(self) -> BldgShapeDetailed:
        ...

    def get_bldg_shape_of_neighbours(self) -> pd.Series:
        ...  # pd.Series[BldgShapeEnvelope]

    overall_glazing_ratio: float


class GeometryBuilderFactoryProtocol(Protocol):
    def get_geometry_builder(self, bldg_fid: int, glazing_ratio: float) -> GeometryBuilderProtocol:
        ...


class GlazingRatioProviderProtocol(Protocol):
    def get_glazing_ratio(self, bldg_fid: int):
        ...


class BuildingOperationFactoryProtocol(Protocol):
    def get_building_operation(self, bldg_fid: int, nr_of_floors: int) -> cesarp.model.BuildingOperationMapping.BuildingOperationMapping:
        ...


class SiteFactoryProtocol(Protocol):
    def get_site(self, bldg_fid: int) -> cesarp.model.Site.Site:
        ...
