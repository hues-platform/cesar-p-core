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
from typing import Any, Mapping, Dict, Optional
import pint
import cesarp.common
from cesarp.model.WindowConstruction import WindowGlassConstruction
from cesarp.model.Construction import BuildingElement as bec
from cesarp.model.ShadingObjectConstruction import ShadingObjectConstruction
from cesarp.construction import _default_config_file


class NeighbouringBldgConstructionFactory:
    """
    Access to material properties (reflectenc ect) to be used for neighbouring buildings.
    For the glass material, the same material is usually used for the neighbouring buildings as the glass of the main building,
    thus the glass construction to be used is passed in. All other parameters are constant and configurable in the config of
    this package.
    """

    def __init__(self, unit_reg: pint.UnitRegistry, custom_config: Optional[Dict[str, Any]] = None):
        """
        :param custom_config: dictonary with configuration entries overwriting package default config
        """
        cfg = cesarp.common.config_loader.load_config_for_package(_default_config_file, __package__, custom_config)
        self._fixed_params = cfg["FIXED_NEIGHBOUR_BLDG_PARAMETERS"]
        self.unit_reg = unit_reg

    def get_neighbours_construction_props(self, window_glass_construction: WindowGlassConstruction) -> Mapping[str, ShadingObjectConstruction]:
        """
        return a dict with the shading properties for the wall and roof of neighbouring buildings
        """
        props_wall = ShadingObjectConstruction.init_from_dict(self._fixed_params["SHADING_OBJ_WALL"], window_glass_construction, self.unit_reg)
        props_roof = ShadingObjectConstruction.init_from_dict(self._fixed_params["SHADING_OBJ_ROOF"], window_glass_construction, self.unit_reg)
        # Do not use the BuildingElement directly as a key, as this dict is jsonpickled, and multiple dicts with same BuildingElement instances as keys give a mess...
        # cesarp.model.BuildingConstruction also has a dict with BuildingElement keys...
        return {bec.WALL.name: props_wall, bec.ROOF.name: props_roof}
