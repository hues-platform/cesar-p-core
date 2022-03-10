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
import logging
import pint
from typing import Any

import cesarp.common
from cesarp.construction.ListWithDefault import ListWithDefault
from cesarp.model.BuildingConstruction import InstallationsCharacteristics
from cesarp.model.WindowConstruction import WindowConstruction


class ArchetypicalConstructionGraphDBBased:
    def __init__(
        self,
        window_glass_constr_options,
        window_glass_constr_default,
        window_frame_construction,
        window_shade_constr,
        roof_constr_options,
        roof_constr_default,
        groundfloor_constr_options,
        groundfloor_constr_default,
        wall_constr_options,
        wall_constr_default,
        internal_ceiling_options,
        internal_ceiling_default,
        glazing_ratio,
        infiltration_rate,
        infiltration_fraction_profile_value,
        installations_characteristics: InstallationsCharacteristics,
    ):
        self.__check_is_fraction(infiltration_fraction_profile_value, "infiltration_fraction_profile_value")
        self.window_glass_constr = ListWithDefault(window_glass_constr_options, window_glass_constr_default)
        self.window_frame_construction = window_frame_construction
        self.window_shade_constr = window_shade_constr
        self.roof_constr = ListWithDefault(roof_constr_options, roof_constr_default)
        self.groundfloor_constr = ListWithDefault(groundfloor_constr_options, groundfloor_constr_default)
        self.wall_constr = ListWithDefault(wall_constr_options, wall_constr_default)
        self.internal_ceiling_constr = ListWithDefault(internal_ceiling_options, internal_ceiling_default)
        self.glazing_ratio = glazing_ratio
        self.infiltration_rate = infiltration_rate
        self.infiltration_fraction_profile_value = infiltration_fraction_profile_value
        self.installations_characteristics = installations_characteristics
        self.__random_selection = False

    @staticmethod
    def __check_is_fraction(value, val_name):
        assert value >= 0 and value <= 1, f"{val_name} {value} should be in range [0..1]"

    def set_construction_selection_strategy(self, random_selection: bool):
        """
        Args:
            random_selection: if True, use random selection of construction element where available
                      if False, the default values are used
        """
        self.__random_selection = random_selection

    def get_window_construction(self):
        return WindowConstruction(frame=self.window_frame_construction, glass=self.__get_window_glass_construction(), shade=self.window_shade_constr)

    def __get_window_glass_construction(self):
        """
        :return: object defining construction for the window glass
        """
        return self.window_glass_constr.get_value(self.__random_selection)

    def get_roof_construction(self):
        """
        :return: one roof construction element
        """
        return self.roof_constr.get_value(self.__random_selection)

    def get_groundfloor_construction(self):
        """
        :return: one groundfloor construction element
        """
        return self.groundfloor_constr.get_value(self.__random_selection)

    def get_wall_construction(self):
        """
        :return: one wall construction element
        """
        return self.wall_constr.get_value(self.__random_selection)

    def get_glazing_ratio(self) -> pint.Quantity:
        """
        The glazing ratio value is per wall, not for the whole building. For more details about the modelling of windows see cesarp.geometry.building
        :return: glazing ratio
        """
        return self.glazing_ratio.get_value(self.__random_selection)

    def get_infiltration_rate(self) -> pint.Quantity:
        return self.infiltration_rate

    def get_infiltration_profile(self) -> Any:
        """
        :return: object representing the profile/schedule for infiltration; e.g. of type cesarp.common.ScheduleFixedValue or ScheduleFile
        """
        return cesarp.common.ScheduleFixedValue(self.infiltration_fraction_profile_value, cesarp.common.ScheduleTypeLimits.FRACTION())

    def get_internal_ceiling_construction(self):
        return self.internal_ceiling_constr.get_value(self.__random_selection)

    def get_installation_characteristics(self) -> InstallationsCharacteristics:
        return self.installations_characteristics

    def __eq__(self, other):
        logger = logging.getLogger(__name__)
        if self.window_glass_constr != other.window_glass_constr:
            logger.debug("window_glass_constr not equal")
            return False
        if self.window_frame_construction != other.window_frame_construction:
            logger.debug("window_frame_construction not equal")
            return False
        if self.window_shade_constr != other.window_shade_constr:
            logger.debug("window_shade_constr not equal")
            return False
        if self.roof_constr != other.roof_constr:
            logger.debug("roof_constr not equal")
            return False
        if self.groundfloor_constr != other.groundfloor_constr:
            logger.debug("groundfloor_constr not equal")
            return False
        if self.wall_constr != other.wall_constr:
            logger.debug("wall_constr not equal")
            return False
        if self.internal_ceiling_constr != other.internal_ceiling_constr:
            logger.debug("internal_ceiling_constr not equal")
            return False
        if self.glazing_ratio != other.glazing_ratio:
            logger.debug("glazing_ratio not equal")
            return False
        if self.infiltration_rate != other.infiltration_rate:
            logger.debug("infiltration_rate not equal")
            return False
        if self.infiltration_fraction_profile_value != other.infiltration_fraction_profile_value:
            logger.debug("infiltration_fraction_profile_value not equal")
            return False
        if self.window_frame_construction != other.window_frame_construction:
            logger.debug("window_frame_construction not equal")
            return False
        if self.installations_characteristics != other.installations_characteristics:
            logger.debug("installations_characteristics not equal")
            return False

        return True
