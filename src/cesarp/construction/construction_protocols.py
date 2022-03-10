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
import pint
from typing import Protocol, Union, Mapping
from cesarp.model.BuildingConstruction import InstallationsCharacteristics
from cesarp.model.Construction import Construction
from cesarp.common.ScheduleFile import ScheduleFile
from cesarp.common.ScheduleFixedValue import ScheduleFixedValue
from cesarp.model.WindowConstruction import WindowConstruction, WindowGlassConstruction
from cesarp.model.ShadingObjectConstruction import ShadingObjectConstruction


class ArchetypicalBuildingConstruction(Protocol):
    def set_construction_selection_strategy(self, random_selection: bool):
        ...

    def get_window_construction(self) -> WindowConstruction:
        ...

    def get_roof_construction(self) -> Construction:
        ...

    def get_groundfloor_construction(self) -> Construction:
        ...

    def get_wall_construction(self) -> Construction:
        ...

    def get_glazing_ratio(self) -> pint.Quantity:
        ...

    def get_infiltration_rate(self) -> pint.Quantity:
        ...

    def get_infiltration_profile(self) -> Union[ScheduleFile, ScheduleFixedValue]:
        ...

    def get_internal_ceiling_construction(self) -> Construction:
        ...

    def get_installation_characteristics(self) -> InstallationsCharacteristics:
        ...


class ArchetypicalConstructionFactoryProtocol(Protocol):
    def get_archetype_for(self, bldg_fid: int) -> ArchetypicalBuildingConstruction:
        ...


class NeighbouringConstructionFactoryProtocol(Protocol):
    "where key of mapping should be name of cesarp.common.BuildingElement Enum member"

    def get_neighbours_construction_props(self, window_glass_construction: WindowGlassConstruction) -> Mapping[str, ShadingObjectConstruction]:
        ...
