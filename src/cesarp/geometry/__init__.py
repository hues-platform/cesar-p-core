# -*- coding: utf-8 -*-
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

"""Package providing functionality for importing building shape data and
identifying neighbour and adjacent buildings for a certain center building."""

__author__ = """Leonie Fierz"""
__email__ = "leonie.fierz@empa.ch"
__version__ = "0.1.0"

import os
from pathlib import Path

_default_config_file = os.path.dirname(__file__) / Path("default_config.yml")
_REQUIRED_SITEVERTICES_PD_COLUMNS = ["gis_fid", "height", "x", "y"]
