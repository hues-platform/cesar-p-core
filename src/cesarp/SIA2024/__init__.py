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
SIA2024
============

Package providing functionality for creating operational parameters and profiles based on SIA2024.
As the raw SIA2024 data used as an input cannot be released OpenSource, there are pre-generated profiles included.
The code for generating new profiles is included as well, as it might be useful to know how the profiles are built up
or reuse part of it in case you want to use another data source to generate your profiles.

The SIA2024 data is stored at UES Lab/Empa as a separate GIT project.


The classes/modules built to be used from outside (API of package):

======================================================================= ===========================================================
class/module                                                            description
======================================================================= ===========================================================
:py:mod:`cesarp.SIA2024.SIA2024Facade`                                  main interface for accessing operatinal parameters based on SIA2024
                                                                        This class can be set as "BUILDING_OPERATION_FACTORY_CLASS" in the config of :py:class:`cesarp.manager`

:py:class:`cesarp.SIA2024.SIA2024BuildingType.SIA2024BldgTypeKeys`      the building types available (for lookup, you pass them as strings)

======================================================================= ===========================================================

"""

import os
from pathlib import Path

COL_STD = "STD"
COL_MIN = "MIN"
COL_MAX = "MAX"

_default_config_file = os.path.dirname(__file__) / Path("sia2024_default_config.yml")
