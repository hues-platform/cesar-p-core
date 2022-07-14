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
from typing import Dict, Any, Optional
import pint
import logging
import cesarp.common
from cesarp.common.AgeClass import AgeClass
from cesarp.construction.construction_protocols import ArchetypicalBuildingConstruction
from cesarp.construction.ConstructionBasics import ConstructionBasics
from cesarp.model.EnergySource import EnergySource

from cesarp.graphdb_access.BldgElementConstructionReader import BldgElementConstructionReader, GraphReaderProtocol, BuildingElementConstrcutionsArchetype
from cesarp.graphdb_access.ArchetypicalConstructionGraphDBBased import ArchetypicalConstructionGraphDBBased
from cesarp.graphdb_access import _default_config_file


class GraphDBArchetypicalConstructionFactory:
    """
    Manages the constructional archetype.
    In the initialization you have to pass the information per building needed to get the appropriate archetype.
    After initialization, you call get_archetype_for(bldg_fid) for each of your buildings.
    Note that archetypes are cached, if several buildings use the same archetype they are not re-constructed.
    """

    def __init__(
        self,
        bldg_fid_to_year_of_constr_lookup: Dict[int, int],
        bldg_fid_to_dhw_ecarrier_lookup: Dict[int, EnergySource],
        bldg_fid_to_heating_ecarrier_lookup: Dict[int, EnergySource],
        graph_data_reader: GraphReaderProtocol,
        ureg: pint.UnitRegistry,
        custom_config: Optional[Dict[str, Any]] = None,
    ):
        self._ureg = ureg
        self._cfg = cesarp.common.config_loader.load_config_for_package(_default_config_file, __package__, custom_config)
        self._bldg_fid_to_year_of_constr_lookup = bldg_fid_to_year_of_constr_lookup
        self._bldg_fid_to_dhw_ecarrier_lookup = bldg_fid_to_dhw_ecarrier_lookup
        self._bldg_fid_to_heating_ecarrier_lookup = bldg_fid_to_heating_ecarrier_lookup
        self._constr_reader = BldgElementConstructionReader(graph_data_reader, ureg, custom_config)
        self._construction_basics = ConstructionBasics(self._ureg, custom_config)
        self._ageclass_archetype = self._init_age_class_lookup()
        self._construction_cache: Dict[str, BuildingElementConstrcutionsArchetype] = dict()  # key is archetype URI

    def _init_age_class_lookup(self) -> Dict[AgeClass, str]:
        ageclass_archetype = {}
        for archetype_shortname, archetype_cfg in self._cfg["ARCHETYPES"].items():
            arch_uri = archetype_cfg["URI"]
            age_class = self._constr_reader.get_age_class_of_archetype(arch_uri)
            ageclass_archetype[age_class] = arch_uri

        if not AgeClass.are_age_classes_consecutive(list(ageclass_archetype.keys())):
            logging.error("age classes retrieved from database are not consecutive. check min/max age of the used age classes so that there are neighter gaps nor overlaps.")

        return ageclass_archetype

    def get_archetype_for(self, bldg_fid: int) -> ArchetypicalBuildingConstruction:
        year_of_construction = self._bldg_fid_to_year_of_constr_lookup[bldg_fid]
        try:
            archetype_uri = self._get_archetype_uri_for(year_of_construction)
        except Exception:
            logging.error(f"no archetype found for building with fid {bldg_fid} and year of construction {year_of_construction}")

        if archetype_uri in self._construction_cache.keys():
            constr_from_graph_db = self._construction_cache[archetype_uri]
        else:
            constr_from_graph_db = self._constr_reader.get_bldg_elem_construction_archetype(archetype_uri)
            self._construction_cache[archetype_uri] = constr_from_graph_db

        archetype = ArchetypicalConstructionGraphDBBased(
            window_glass_constr_options=constr_from_graph_db.windows,
            window_glass_constr_default=self._constr_reader.get_default_construction(constr_from_graph_db.windows, constr_from_graph_db.short_name),
            window_frame_construction=self._construction_basics.get_fixed_window_frame_construction(),
            window_shade_constr=self._constr_reader.get_window_shading_constr(archetype_uri),
            roof_constr_options=constr_from_graph_db.roofs,
            roof_constr_default=self._constr_reader.get_default_construction(constr_from_graph_db.roofs, constr_from_graph_db.short_name),
            groundfloor_constr_options=constr_from_graph_db.grounds,
            groundfloor_constr_default=self._constr_reader.get_default_construction(constr_from_graph_db.grounds, constr_from_graph_db.short_name),
            wall_constr_options=constr_from_graph_db.walls,
            wall_constr_default=self._constr_reader.get_default_construction(constr_from_graph_db.walls, constr_from_graph_db.short_name),
            internal_ceiling_options=constr_from_graph_db.internal_ceilings,
            internal_ceiling_default=self._constr_reader.get_default_construction(constr_from_graph_db.internal_ceilings, constr_from_graph_db.short_name),
            glazing_ratio=self._constr_reader.get_glazing_ratio(constr_from_graph_db.name),
            infiltration_rate=self._constr_reader.get_infiltration_rate(constr_from_graph_db.name),
            infiltration_fraction_profile_value=self._cfg["FIXED_INFILTRATION_PROFILE_VALUE"] * self._ureg.dimensionless,
            installations_characteristics=self._construction_basics.get_inst_characteristics(
                self._bldg_fid_to_dhw_ecarrier_lookup[bldg_fid],
                self._bldg_fid_to_heating_ecarrier_lookup[bldg_fid],
            ),
        )

        return archetype

    def _get_archetype_uri_for(self, year_of_construction):
        """
        :param year_of_construction: [description]
        :type year_of_construction: [type]
        :return: [description]
        :rtype: [type]
        :raises: Exception if no archetype for given year_of_construction was found
        """
        age_class = AgeClass.get_age_class_for(year_of_construction, self._ageclass_archetype.keys())
        return self._ageclass_archetype[age_class]
