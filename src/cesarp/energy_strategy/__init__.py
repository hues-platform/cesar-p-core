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
"""
energy_strategy
============================

There are two energy strategies implemented, business as usual (WWB) and New Energy Policy (NEP). You can switch between
them by setting the configuration parameter ENERGY_STRATEGY_SELECTION (default is WWB).

The package handles data access for the two strategies, but has no buisness logic implemented.

The input files are all Excel files, as there are quite many files and they did exist already, the format was not changed to YAML or CSV.
Data seems also to be fairly stable, if changes occure more frequent you could think of changing the data format. If you do so, just keep
the interface of the classes as it is now, so that the other packages accessing data do not need to be changed.

The energy strategy is used in two places:

- For operational emissions and costs :py:class:`cesarp.emissions_costs.OperationalEmissionsAndCosts`
- For defining which buildings should be retrofitted (retrofit rates) :py:class:`cesarp.retrofit.energy_strategy_2050.EnergyPerspective2050BldgElementsRetrofitter`


Main API

======================================================================================= ===========================================================
class / module                                                                          description
======================================================================================= ===========================================================
:py:class:`cesarp.energy_strategy.EnergyStrategy`                                       interface to access emission and cost data of the set energy strategy (parent of subsequent three data query classes)

:py:class:`cesarp.energy_strategy.EnergyMix`                                            query data about the energy mix data, e.g. wood mix, gas mix etc

:py:class:`cesarp.energy_strategy.FuelCosts`                                            query fuel cost data

:py:class:`cesarp.energy_strategy.SystemEfficiencies`                                   query efficiency of system installations (for dhw, heating)

:py:class:`cesarp.energy_strategy.RetrofitRates`                                        query retrofit rates
======================================================================================= ===========================================================

"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from cesarp.common import load_config_for_package

_default_config_file = os.path.dirname(__file__) / Path("energy_strategy_config.yml")


def get_selected_energy_strategy_cfg(custom_config: Optional[Dict[str, Any]] = None):
    full_cfg = load_config_for_package(_default_config_file, __package__, custom_config)
    es_selection = full_cfg["ENERGY_STRATEGY_SELECTION"]
    try:
        es_cfg = full_cfg[es_selection]
    except KeyError:
        raise Exception(f"for ENERGY_STRATEGY_SELECTION {es_selection} there is no configuration available!")
    return es_cfg
