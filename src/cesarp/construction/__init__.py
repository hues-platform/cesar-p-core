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
construction
============================

This package includes the parts which are statically defined in the configuration for all buildings, such as
window frame properties. Those parameters are configurable in the config, expect for the properties of
window shading materials, which are hard-coded in :py:class:`cesarp.construction.ConstructionBasics`


Main API

======================================================================================= ===========================================================
class / module                                                                          description
======================================================================================= ===========================================================
:py:class:`cesarp.construction.ConstructionFacade`                                      returns the construction archetype factory

:py:class:`cesarp.construction.NeighbouringBldgConstructionFactory`                     factory to create parameters for a neighbouring building

======================================================================================= ===========================================================

"""

import os
from pathlib import Path

_default_config_file = os.path.dirname(__file__) / Path("default_config.yml")
