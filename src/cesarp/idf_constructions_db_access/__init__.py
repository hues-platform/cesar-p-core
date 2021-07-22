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
idf_constructions_db_access
============================

Accessing the pre-generated partial construction IDF files. It is not really a database, but just a collection of those IDF files.
The construction definitions do NOT include the infromation necessary to perform retrofit actions.

The definitions included here were transfered the a GraphDB, which is accessible over :py:mod:`cesarp.graphdb_access`.


Main API classes

===================================================================================== ===========================================================
class                                                                                 description
===================================================================================== ===========================================================
:py:class:`cesarp.idf_construction_db_access.IDFConstructionArchetypeFactory`         Create a construction archetype.
                                                                                      Is used if config param CONSTRUCTION_DB is set to IDF_FILES_DB in config of :py:mod:`cesarp.construction`
===================================================================================== ===========================================================

"""

import os
from pathlib import Path

_default_config_file = os.path.dirname(__file__) / Path("default_config.yml")
