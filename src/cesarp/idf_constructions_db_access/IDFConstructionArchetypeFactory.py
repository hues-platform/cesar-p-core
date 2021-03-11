# coding=utf-8
#
# Copyright (c) 2021, Empa, Leonie Fierz, Aaron Bojarski, Ricardo Parreira da Silva, Sven Eggimann.
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
from typing import Dict, Any
import logging

import cesarp.common
from cesarp.model.EnergySource import EnergySource
from cesarp.model.Construction import BuildingElement
from cesarp.construction.ConstructionBasics import ConstructionBasics
from cesarp.idf_constructions_db_access import _default_config_file
import cesarp.idf_constructions_db_access.input_parser as input_parser
from cesarp.idf_constructions_db_access.ArchetypicalConstructionIDFBased import ArchetypicalConstructionIDFBased


class IDFConstructionArchetypeFactory:
    """
    Factory to generate archetypes defining the constructional properties of a building, meaning materials,
    insulation etc.
    The construction database (acutally predefined partial IDF files) used by default is described in the CESAR Tool
    documentation (Matlab version), Appendix 8.1. Excel Standard Construction Database.

    Factory is not multi-threading safe due to self._archetypes_cache
    """

    def __init__(
        self,
        bldg_fid_to_year_of_constr_lookup: Dict[int, int],
        bldg_fid_to_dhw_ecarrier_lookup: Dict[int, EnergySource],
        bldg_fid_to_heating_ecarrier_lookup: Dict[int, EnergySource],
        ureg,
        custom_config: Dict[str, Any] = {},
    ):
        """
        :param custom_config: dictonary with configuration entries overwriting package default config
        """
        # self.age_class_archetype_dict = self.__get_constructional_archetype_per_age_class(custom_config)
        self._cfg = cesarp.common.config_loader.load_config_for_package(_default_config_file, __package__, custom_config)
        self.ureg = ureg
        self._cfg_input_files = self._cfg["INPUT_FILES"]
        self._bldg_fid_to_year_of_constr_lookup: Dict[int, int] = bldg_fid_to_year_of_constr_lookup
        self._bldg_fid_to_dhw_ecarrier_lookup: Dict[int, EnergySource] = bldg_fid_to_dhw_ecarrier_lookup
        self._bldg_fid_to_heating_ecarrier_lookup: Dict[int, EnergySource] = bldg_fid_to_heating_ecarrier_lookup
        self._constructions_per_age_class = input_parser.read_standard_external_constructions_from_dir(self._cfg_input_files["BUILDING_ELEMENTS"]["STANDARD_CONSTRUCTIONS_DIR"])
        self._glazing_ratios = input_parser.read_glazing_ratio(self._cfg_input_files["GLAZING_RATIO_PER_AGE_CLASS"], ureg)
        self._infiltration_rates = input_parser.read_infiltration_rate(self._cfg_input_files["INFILTRATION_PER_AGE_CLASS"], ureg)
        self._archetypes_cache: Dict[cesarp.common.AgeClass, ArchetypicalConstructionIDFBased] = dict()
        self._construction_basics = ConstructionBasics(self.ureg)
        self._logger = logging.getLogger(__name__)

    def get_archetype_for(self, bldg_fid: int) -> ArchetypicalConstructionIDFBased:
        year_of_construction = self._bldg_fid_to_year_of_constr_lookup[bldg_fid]
        age_class = cesarp.common.AgeClass.get_age_class_for(year_of_construction, input_parser.construction_age_classes.values())

        self._logger.debug(f"age_class: {age_class.min_age} to {age_class.max_age}")

        if age_class in self._archetypes_cache.keys():
            archetype = self._archetypes_cache[age_class]
        else:
            constructions_for_age_class = self._constructions_per_age_class.loc[self._constructions_per_age_class["age_class"] == age_class]
            self._logger.debug("constructions per age class\n {}".format(constructions_for_age_class))
            window_glass_options = constructions_for_age_class.loc[constructions_for_age_class.elem_name == BuildingElement.WINDOW]
            roof_options = constructions_for_age_class.loc[constructions_for_age_class.elem_name == BuildingElement.ROOF]
            groundfloor_options = constructions_for_age_class.loc[constructions_for_age_class.elem_name == BuildingElement.GROUNDFLOOR]
            wall_options = constructions_for_age_class.loc[constructions_for_age_class.elem_name == BuildingElement.WALL]

            archetype = ArchetypicalConstructionIDFBased(
                list(window_glass_options["path"]),
                self.__get_bldg_elem_construction_default_for_age_class(age_class, BuildingElement.WINDOW, window_glass_options),
                self._construction_basics.get_fixed_window_frame_construction(),
                self._construction_basics.get_window_shading_constr(year_of_construction),
                list(roof_options["path"]),
                self.__get_bldg_elem_construction_default_for_age_class(age_class, BuildingElement.ROOF, roof_options),
                list(groundfloor_options["path"]),
                self.__get_bldg_elem_construction_default_for_age_class(age_class, BuildingElement.GROUNDFLOOR, groundfloor_options),
                list(wall_options["path"]),
                self.__get_bldg_elem_construction_default_for_age_class(age_class, BuildingElement.WALL, wall_options),
                self._cfg_input_files["BUILDING_ELEMENTS"]["INTERNAL_CEILING_IDF"],
                self._cfg_input_files["BUILDING_ELEMENTS"]["MATERIAL_PER_AGE_CLASS_IDF"],
                self._cfg_input_files["BUILDING_ELEMENTS"]["MATERIAL_INTERNAL_IDF"],
                self._glazing_ratios.loc[age_class, "min"],
                self._glazing_ratios.loc[age_class, "max"],
                self._infiltration_rates.loc[age_class, "ACH_normal_pressure"],
                self._cfg["FIXED_INFILTRATION_PROFILE_VALUE"] * self.ureg.dimensionless,
                self._construction_basics.get_inst_characteristics(
                    e_carrier_dhw=self._bldg_fid_to_dhw_ecarrier_lookup[bldg_fid], e_carrier_heating=self._bldg_fid_to_heating_ecarrier_lookup[bldg_fid],
                ),
            )
            self._archetypes_cache[age_class] = archetype

        return archetype

    def __get_bldg_elem_construction_default_for_age_class(self, age_class, blg_constr_elem_class, element_options):
        """
        :param age_class:
        :type cesarp.construction.AgeClass
        :param constr_elem: type of element
        :type cesarp.ConstructionElemementNames (Enum)
        :param element_options: available options for element
        :type pandas.DataFrame(columns=["nr"])
        :return: one row out of element_options DataFrame passed
        """

        ac = input_parser.construction_age_classes
        construction_defaults_per_age_class = {
            ac[1]: {BuildingElement.WALL: 4, BuildingElement.ROOF: 1, BuildingElement.GROUNDFLOOR: 2, BuildingElement.WINDOW: 1},
            ac[2]: {BuildingElement.WALL: 7, BuildingElement.ROOF: 4, BuildingElement.GROUNDFLOOR: 2, BuildingElement.WINDOW: 1},
            ac[3]: {BuildingElement.WALL: 3, BuildingElement.ROOF: 3, BuildingElement.GROUNDFLOOR: 2, BuildingElement.WINDOW: 2},
            ac[4]: {BuildingElement.WALL: 2, BuildingElement.ROOF: 2, BuildingElement.GROUNDFLOOR: 2, BuildingElement.WINDOW: 1},
            ac[5]: {BuildingElement.WALL: 3, BuildingElement.ROOF: 1, BuildingElement.GROUNDFLOOR: 1, BuildingElement.WINDOW: 3},
            ac[6]: {BuildingElement.WALL: 4, BuildingElement.ROOF: 1, BuildingElement.GROUNDFLOOR: 2, BuildingElement.WINDOW: 3},
            ac[7]: {BuildingElement.WALL: 1, BuildingElement.ROOF: 1, BuildingElement.GROUNDFLOOR: 2, BuildingElement.WINDOW: 2},
            ac[8]: {BuildingElement.WALL: 2, BuildingElement.ROOF: 1, BuildingElement.GROUNDFLOOR: 1, BuildingElement.WINDOW: 1},
            ac[9]: {BuildingElement.WALL: 1, BuildingElement.ROOF: 2, BuildingElement.GROUNDFLOOR: 2, BuildingElement.WINDOW: 2},
        }

        element_nr = construction_defaults_per_age_class[age_class][blg_constr_elem_class]
        default_elem = element_options[element_options["constr_option_nr"] == element_nr]
        if default_elem.empty:
            raise Exception(f"No default found for construction {blg_constr_elem_class} age class {age_class}")
        if len(default_elem.index) > 1:
            raise Exception(f"More than one default defined for construction {blg_constr_elem_class} age class {age_class}")

        return default_elem["path"].values[0]
