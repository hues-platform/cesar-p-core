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

import os
from pathlib import Path
from typing import Dict, Any
from cesarp.common import load_config_for_package

_default_config_file = os.path.dirname(__file__) / Path("energy_strategy_config.yml")


def get_selected_energy_strategy_cfg(custom_config: Dict[str, Any] = {}):
    full_cfg = load_config_for_package(_default_config_file, __package__, custom_config)
    es_selection = full_cfg["ENERGY_STRATEGY_SELECTION"]
    try:
        es_cfg = full_cfg[es_selection]
    except KeyError:
        raise Exception(f"for ENERGY_STRATEGY_SELECTION {es_selection} there is no configuration available!")
    return es_cfg
