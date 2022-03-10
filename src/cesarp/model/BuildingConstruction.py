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
from typing import Optional
from dataclasses import dataclass
from cesarp.model.Construction import BuildingElement, Construction
from cesarp.model.WindowConstruction import WindowConstruction
from cesarp.model.EnergySource import EnergySource


@dataclass
class LightingCharacteristics:
    """
    Defines properties of lighting installation. those properties are independent of actual usage,
    the latter is defined in operational part of the building model"""

    return_air_fraction: pint.Quantity  # dimensionless
    fraction_radiant: pint.Quantity  # dimensionless
    fraction_visible: pint.Quantity  # dimensionless

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


@dataclass
class InstallationsCharacteristics:
    """defining properties such as efficiencies of installed appliances and such, which are not depending on the usage"""

    fraction_radiant_from_activity: pint.Quantity  # dimensionless
    lighting_characteristics: LightingCharacteristics
    dhw_fraction_lost: pint.Quantity  # dimensionless
    electric_appliances_fraction_radiant: pint.Quantity  # dimensionless
    e_carrier_dhw: Optional[EnergySource]
    e_carrier_heating: Optional[EnergySource]

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


class BuildingConstruction:
    def __init__(
        self,
        window_construction: WindowConstruction,
        roof_constr: Construction,
        groundfloor_constr: Construction,
        wall_constr: Construction,
        internal_ceiling_constr: Construction,
        glazing_ratio: pint.Quantity,
        infiltration_rate: pint.Quantity,
        infiltration_profile,  # any schedule class from cesarp.common
        installation_characteristics: InstallationsCharacteristics,
    ):
        """
        :param window_construction: object defining construction properties of windows
        :param roof_constr: object defining construction of roof
        :param groundfloor_constr: object defining construction of ground / groundfloor
        :param wall_constr:  object defining construction of walls
        :param internal_ceiling_constr: object defining construction of internal ceiling, first layer is the one facing the lower story, thus the one visible as ceiling, the last layer is the floor visible on the upper story
        :param glazing_ratio: wall to window ratio to; applies to all walls of the building;
        :param infiltration_rate: infiltratino rate, either in ACH or m3/sec/m2
        :param infiltration_profile: year profile with hourly values defining the profile (fraction profile reducing the given infiltration rate) for ventilation
        :param installation_characteristics: object defining properties such as efficiencies of installed appliances and such, which are not depending on the usage
        """

        # Do not use the BuildingElement directly as keys as this dict is jsonpickled, and multiple dicts with same BuildingElement instances as keys give a mess...
        self.__constr_elems = {
            BuildingElement.WINDOW.name: window_construction,  # type: ignore
            BuildingElement.WALL.name: wall_constr,  # type: ignore
            BuildingElement.GROUNDFLOOR.name: groundfloor_constr,  # type: ignore
            BuildingElement.ROOF.name: roof_constr,  # type: ignore
            BuildingElement.INTERNAL_CEILING.name: internal_ceiling_constr,  # type: ignore
        }

        self.glazing_ratio = glazing_ratio
        self.infiltration_rate = infiltration_rate
        self.infiltration_profile = infiltration_profile
        self.installation_characteristics = installation_characteristics

    def get_construction_for_bldg_elem(self, bldg_element: BuildingElement):
        return self.__constr_elems[bldg_element.name]

    def set_construction_for_bldg_elem(self, bldg_elem: BuildingElement, construction) -> None:
        """
        :param bldg_elem: BuildingElement to set construction for
        :param construction: for BuildingElement.Window a WindowConstruction object, for all others either
                              ConstructionAsIDF or Construction object
        :return: None
        """
        assert (bldg_elem == BuildingElement.WINDOW and isinstance(construction, WindowConstruction)) or (
            bldg_elem != BuildingElement.WINDOW and (isinstance(construction, Construction))
        ), f"please check type of passed construction object, {type(construction)} not ok for {bldg_elem}"
        self.__constr_elems[bldg_elem.name] = construction

    @property
    def window_constr(self):
        return self.get_construction_for_bldg_elem(BuildingElement.WINDOW)

    @property
    def wall_constr(self):
        return self.get_construction_for_bldg_elem(BuildingElement.WALL)

    @property
    def groundfloor_constr(self):
        return self.get_construction_for_bldg_elem(BuildingElement.GROUNDFLOOR)

    @property
    def roof_constr(self):
        return self.get_construction_for_bldg_elem(BuildingElement.ROOF)

    @property
    def internal_ceiling_constr(self):
        return self.get_construction_for_bldg_elem(BuildingElement.INTERNAL_CEILING)

    def __eq__(self, other):
        logger = logging.getLogger(__name__)
        if self.window_constr != other.window_constr:
            logger.debug("window_constr not equal")
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
        if self.infiltration_profile != other.infiltration_profile:
            logger.debug("infiltration_profile not equal")
            return False
        if self.installation_characteristics != other.installation_characteristics:
            logger.debug("installation_characteristics not equal")
            return False
        return True

    def upgrade_model_remove_floor(self):
        try:
            del self.__constr_elems["INTERNAL_FLOOR"]
        except KeyError:
            pass
