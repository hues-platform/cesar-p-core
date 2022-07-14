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
graphdb_access
============================

Interface to the information stored in the graph database. The data can be either locally in a TTL file (included under ressources) or queried
from a database running on a GraphDB Server (or locally on your machine).

If you use a remote GraphDB, you are responsible to save or track the data used in your project, as in a common database it could be overwritten or corrected
which means after some time you wont be able to reproduce the exact same results when querying data from the same remote DB.

The package is not a strict data access, as there is some business logic included.

Main API classes

===================================================================================== ===========================================================
class                                                                                 description
===================================================================================== ===========================================================
:py:class:`cesarp.graphdb_access.GraphDBFacade`                                       This is your entry point to the package, instantiating a local (file) or remote
                                                                                      connection according to the configuration (by default local file)

:py:class:`cesarp.graphdb_access.GraphDBArchetypicalConstrctionFactory`               Create constructional archetypes based on the infromation from the GraphDB

:py:class:`cesarp.graphdb_access.ConstructionRetrofitter`                             Interface to get retrofit constructions
===================================================================================== ===========================================================
"""

import os
from pathlib import Path

_default_config_file = os.path.dirname(__file__) / Path("graph_default_config.yml")
