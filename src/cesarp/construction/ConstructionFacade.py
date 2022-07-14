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
from enum import Enum
import pint

import cesarp.common
from cesarp.common.CesarpException import CesarpException
from cesarp.model.EnergySource import EnergySource
from cesarp.construction import _default_config_file
from cesarp.construction.construction_protocols import ArchetypicalConstructionFactoryProtocol
from cesarp.graphdb_access.GraphDBFacade import GraphDBFacade


class ConstructionFacade:
    @staticmethod
    def get_constructional_archetype_factory(
        bldg_fid_to_year_of_constr_lookup: Dict[int, int],
        bldg_fid_to_dhw_ecarrier_lookup: Dict[int, EnergySource],
        bldg_fid_to_heating_ecarrier_lookup: Dict[int, EnergySource],
        ureg: pint.UnitRegistry,
        custom_config: Optional[Dict[str, Any]],
    ) -> ArchetypicalConstructionFactoryProtocol:
        """
        Returns a GraphDB based construction factory according to package configuration (parameter CONSTRUCTION_DB).

        :param bldg_fid_to_year_of_constr_lookup: list of all buildings along with their construction year
        :type bldg_fid_to_year_of_constr_lookup: Dict[int, int]
        :param bldg_fid_to_dhw_ecarrier_lookup: list of all buildings along with their EnergySource used for domestic hot water
        :type bldg_fid_to_dhw_ecarrier_lookup: Dict[int, EnergySource]
        :param bldg_fid_to_heating_ecarrier_lookup: list of all buildings along with their EnergySource used for heating
        :type bldg_fid_to_heating_ecarrier_lookup: Dict[int, EnergySource]
        :param ureg: unit registry application instance
        :type ureg: pint.UnitRegistry
        :param custom_config: dict with main/custom configuration parameters, overwriting the package defaults
        :type custom_config: Dict[str, Any], optional
        :raises CesarpException: in case CONSTRUCTION_DB parameter is set to invalid value
        :return: factory to query for constructional archetypes for each of your buildings
        :rtype: ArchetypicalConstructionFactoryProtocol
        """
        cfg = cesarp.common.load_config_for_package(_default_config_file, __package__, custom_config)
        db_selection = ConstrDBOptions[cfg["CONSTRUCTION_DB"]]
        if db_selection in [ConstrDBOptions.GRAPH_DB]:
            graph_db_facade = GraphDBFacade(ureg, custom_config)
            return graph_db_facade.get_graph_construction_archetype_factory(bldg_fid_to_year_of_constr_lookup, bldg_fid_to_dhw_ecarrier_lookup, bldg_fid_to_heating_ecarrier_lookup)
        raise CesarpException(f"Unsupported Construction DB Type {db_selection}. Check configuration for entry MANAGER - CONSTRUCTION_DB")


class ConstrDBOptions(Enum):
    GRAPH_DB = 1
