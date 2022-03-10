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
from enum import Enum


class BuildingElement(Enum):
    """
    Defines the construction elements of a building.
    """

    WINDOW = 1
    WALL = 4
    GROUNDFLOOR = 5
    ROOF = 6
    # internal ceiling is story separation, for lower story zone; must be mirrored construction to INTERNAL_FLOOR
    INTERNAL_FLOOR = 7
    # internal ceiling is story separation, for lower story zone; must be mirrored construction to INTERNAL_FLOOR
    INTERNAL_CEILING = 8

    @classmethod
    def _missing_(cls, elem_class_name):
        """
        Maps a string to an member of this enum

        :param elem_class_name: string representation of building element name
        :return: BuildingElementName
        """
        if "Wall" in elem_class_name:
            return BuildingElement.WALL
        if "Window" in elem_class_name or "Win" in elem_class_name:
            return BuildingElement.WINDOW
        if "Roof" in elem_class_name:
            return BuildingElement.ROOF
        if "Ground" in elem_class_name:
            return BuildingElement.GROUNDFLOOR
        if "Internal Floor" in elem_class_name:
            return BuildingElement.INTERNAL_FLOOR
        if "InternalFloor" in elem_class_name:
            return BuildingElement.INTERNAL_FLOOR
        if "Internal Ceiling" in elem_class_name:
            return BuildingElement.INTERNAL_CEILING
        if "InternalCeiling" in elem_class_name:
            return BuildingElement.INTERNAL_CEILING
        raise ValueError(f"{elem_class_name} is not a valid BuildingElement")
