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
from typing import Any, Callable
import cesarp.common
from cesarp.model.BuildingConstruction import BuildingConstruction
from cesarp.construction.construction_protocols import ArchetypicalBuildingConstruction


class LookupForBldgProtocol:
    def get_for_bldg_fid(self, bldg_fid) -> Any:
        ...


class ConstructionBuilder:
    def __init__(self, bldg_fid, archetypical_bldg_constr: ArchetypicalBuildingConstruction):
        self.bldg_fid = bldg_fid
        self.do_randomize = False
        self.archetype: ArchetypicalBuildingConstruction = archetypical_bldg_constr
        self.archetype.set_construction_selection_strategy(random_selection=False)
        self.__get_glazing_ratio_method = lambda bldg_fid: self.archetype.get_glazing_ratio()
        self.__get_infiltration_rate_method = lambda bldg_fid: self.archetype.get_infiltration_rate()
        self.__get_infiltration_profile_method = lambda bldg_fid: self.archetype.get_infiltration_profile()

    def activate_randomization(self):
        self.do_randomize = True
        return self

    def set_external_glazing_ratio(self, get_glazing_ratio_method: Callable[[int], cesarp.common.NUMERIC]):
        self.__get_glazing_ratio_method = get_glazing_ratio_method
        return self

    def set_external_infiltration_rate(self, get_infiltration_rate_method: Callable[[int], cesarp.common.NUMERIC]):
        self.__get_infiltration_rate_method = get_infiltration_rate_method
        return self

    def set_external_infiltration_profile(self, get_infiltration_profile_method: Callable[[int], Any]):
        self.__get_infiltration_profile_method = get_infiltration_profile_method
        return self

    def build(self) -> BuildingConstruction:
        """
        Returns dictonary with archetypical construction properties for given year_of_construction
        """
        self.archetype.set_construction_selection_strategy(random_selection=self.do_randomize)
        return BuildingConstruction(
            self.archetype.get_window_construction(),
            self.archetype.get_roof_construction(),
            self.archetype.get_groundfloor_construction(),
            self.archetype.get_wall_construction(),
            self.archetype.get_internal_ceiling_construction(),
            self.__get_glazing_ratio_method(self.bldg_fid),
            self.__get_infiltration_rate_method(self.bldg_fid),
            self.__get_infiltration_profile_method(self.bldg_fid),
            self.archetype.get_installation_characteristics(),
        )
