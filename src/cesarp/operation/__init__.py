# -*- coding: utf-8 -*-
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
operation
============

Package providing functionality for defining internal conditions such as occupancy, appliances, lighting.
As well for passive cooling with night ventilation and window shading.

For the main part of the operational properties including profiles, there is either the variant to assign a fixed set identical
for all buildings (cesarp.operation.fixed) or using the parameters defined according to SIA2024 (see cesarp.SIA2014).

For passive cooling there is a separate factory, cesarp.operation.PassiveCoolingOperationFacotry, used in both above caseses and is passed
to them as an argument in :py:class:`cesarp.manager.BldgModelFactory`

============================================================================ ===========================================================
class                                                                        description
============================================================================ ===========================================================
:py:class:`cesarp.operation.FixedBuildingOperationFactory`                   Main class used in case of using the same operational parameters for all buildings.
                                                                             This class can be set as "BUILDING_OPERATION_FACTORY_CLASS" in the config of :py:class:`cesarp.manager`
                                                                             Use this as a starting point if you want to create your own factory for building operation properties.

:py:class:`cesarp.operation.PassiveCoolingOperationFacotry`                  Generation of passive cooling night ventilation and window shading operational properties.
                                                                             Both are initialized from configuration parameters and are the same for all buildings.

============================================================================ ===========================================================
"""

from pathlib import Path
import os

__author__ = """Leonie Fierz"""
__email__ = "leonie.fierz@empa.ch"
__version__ = "0.1.0"


_default_config_file = os.path.dirname(__file__) / Path("operation_default_config.yml")
