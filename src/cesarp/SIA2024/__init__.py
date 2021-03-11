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
"""
Details about demand values and profile generation please see cesarp.SIA2024.SIA2024ParametersFactory, data source see cesarp.SIA2024.SIA2024DataAccessor
Main Interface to the package is SIA2024Facade.
"""
import os
from pathlib import Path

COL_STD = "STD"
COL_MIN = "MIN"
COL_MAX = "MAX"

_default_config_file = os.path.dirname(__file__) / Path("sia2024_default_config.yml")
