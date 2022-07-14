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
import copy
from typing import Dict, Any, Protocol, Optional

import cesarp.common
from cesarp.model.Construction import Construction
from cesarp.model.WindowConstruction import WindowConstruction, WindowGlassConstruction
from cesarp.graphdb_access import _default_config_file


class GraphReaderRetrofitProtocol(Protocol):
    def get_retrofitted_construction(self, construction: Construction) -> Construction:
        """
        raises LookupError if no retrofit construction was linked to the given construction

        :param construction: construction for which to get retrofitted construction
        :return: retrofitted construction of given construction object
        """
        ...

    def get_retrofitted_window_glass(self, win_glass: WindowGlassConstruction) -> WindowGlassConstruction:
        """
        raises LookupError if no retrofit option was linked to the given window glass

        :param win_glass: window glass for which to get retrofitted glass
        :return: new WindowGlassConstruction object
        """
        ...

    def get_retrofit_target_info(self) -> str:
        """
        :return: description of retrofit target.
        :rtype: str
        """


class ConstructionRetrofitter:
    def __init__(self, graph_access: GraphReaderRetrofitProtocol, ureg: pint.UnitRegistry, custom_config: Optional[Dict[str, Any]] = None):
        self._ureg = ureg
        self._graph_access = graph_access
        self._cfg = cesarp.common.load_config_for_package(_default_config_file, __package__, custom_config)

    def get_retrofitted_construction(self, base_constr: Construction) -> Construction:
        """
        To define retrofit construction the retrofit regulation and target set in the configuration-YML under
        RETROFIT are used.

        raises LookupError if no retrofit construction was found
        :param base_constr: construction for which to get retrofitted construction
        :return: new Construction object which can be used as retrofit for the passed one.
        """
        assert isinstance(base_constr, Construction), (
            f"Cannot retrofit construction of type {type(base_constr)}. Only Construction support retrofitting. Try "
            f"changing data source of constructions to GraphDB in manager."
        )

        return self._graph_access.get_retrofitted_construction(base_constr)

    def get_retrofitted_window(self, base_win_constr: WindowConstruction) -> WindowConstruction:
        """
        To define retrofit construction the retrofit regulation and target set in the configuration-YML under
        RETROFIT are used.

        raises LookupError if no retrofit construction was found
        :param base_win_constr: window for which to get retrofitted window construction
        :return: new WindowConstruction object which can be used as retrofit for the passed one.
        """

        assert isinstance(base_win_constr.glass, WindowGlassConstruction), (
            f"Retrofit can only handle fully specified "
            f"window glasses of type WindowGlassConstruction"
            f", but {type(base_win_constr)} was passed."
            f"Try changing data source to GraphDB in manager "
            f"config."
        )
        retrofitted_glass = self._graph_access.get_retrofitted_window_glass(base_win_constr.glass)
        retrofitted_win = WindowConstruction(glass=retrofitted_glass, frame=copy.deepcopy(base_win_constr.frame), shade=copy.deepcopy(base_win_constr.shade))

        return retrofitted_win

    def get_retrofit_target_info(self):
        return self._graph_access.get_retrofit_target_info()
