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
from operator import xor

import cesarp.common
from cesarp.model.EnergySource import EnergySource
from cesarp.graphdb_access import _default_config_file
from cesarp.graphdb_access.GraphDBReader import GraphDBReader
from cesarp.graphdb_access.LocalFileReader import LocalFileReader
from cesarp.graphdb_access.GraphDBArchetypicalConstructionFactory import GraphReaderProtocol
from cesarp.graphdb_access.ConstructionRetrofitter import ConstructionRetrofitter
from cesarp.graphdb_access.BldgElementConstructionReader import BldgElementConstructionReader


class GraphDBFacade:
    """
    This facade creates for you the main API classes. It does initialize a remote or local DB instance (for more details see package description).
    You can use a custom factory to create the constructional archetypes by setting the configuration parameter ARCHETYPE_CONSTRUCTION_FACTORY_CLASS.
    """

    def __init__(self, ureg: pint.UnitRegistry, custom_config: Optional[Dict[str, Any]] = None):
        self._ureg = ureg
        if custom_config is None:
            custom_config = {}  # to be save as we initialize unkown constr factory class
        self._custom_config = custom_config
        self._cfg = cesarp.common.load_config_for_package(_default_config_file, __package__, custom_config)
        cfg_local_active = self._cfg["LOCAL"]["ACTIVE"]
        cfg_remote_active = self._cfg["REMOTE"]["ACTIVE"]
        assert xor(cfg_local_active, cfg_remote_active), f"in {_default_config_file} both, LOCAL and REMOTE is active, but only one can be active"
        self._graph_reader: GraphReaderProtocol
        if self._cfg["LOCAL"]["ACTIVE"]:
            self._graph_reader = LocalFileReader(custom_config=self._custom_config)
        elif self._cfg["REMOTE"]["ACTIVE"]:
            self._graph_reader = GraphDBReader(custom_config=self._custom_config)

    def get_graph_construction_archetype_factory(
        self,
        bldg_fid_to_year_of_constr_lookup: Dict[int, int],
        bldg_fid_to_dhw_ecarrier_lookup: Dict[int, EnergySource],
        bldg_fid_to_heating_ecarrier_lookup: Dict[int, EnergySource],
    ) -> cesarp.construction.construction_protocols.ArchetypicalConstructionFactoryProtocol:
        constr_fact_class_name: str = self._cfg["ARCHETYPE_CONSTRUCTION_FACTORY_CLASS"]
        constr_fact_class: type = cesarp.common.get_class_from_str(constr_fact_class_name)
        return constr_fact_class(
            bldg_fid_to_year_of_constr_lookup,
            bldg_fid_to_dhw_ecarrier_lookup,
            bldg_fid_to_heating_ecarrier_lookup,
            self._graph_reader,
            self._ureg,
            self._custom_config,
        )

    def get_graph_construction_retrofitter(self) -> ConstructionRetrofitter:
        bldg_elem_reader = BldgElementConstructionReader(self._graph_reader, self._ureg, self._custom_config)
        return ConstructionRetrofitter(bldg_elem_reader, self._ureg, self._custom_config)
