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
import cesarp.common

_default_config_file = os.path.dirname(__file__) / Path("default_config.yml")

# currently not used, a random building age out of assigned age class is chosen and writen to BuildingInformation.csv outside cesar
gwr_age_classes = [
    cesarp.common.AgeClass(max_age=1918),
    cesarp.common.AgeClass(1919, 1945),
    cesarp.common.AgeClass(1946, 1960),
    cesarp.common.AgeClass(1961, 1970),
    cesarp.common.AgeClass(1971, 1980),
    cesarp.common.AgeClass(1981, 1985),
    cesarp.common.AgeClass(1986, 1990),
    cesarp.common.AgeClass(1991, 1995),
    cesarp.common.AgeClass(1996, 2000),
    cesarp.common.AgeClass(2001, 2005),
    cesarp.common.AgeClass(2006, 2010),
    cesarp.common.AgeClass(2011, 2015),
    cesarp.common.AgeClass(min_age=2016),
]
