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
eplus_adapter
============================

Responsible for everything regarding EnergyPlus, from IDF creation to result extraction.
The implementation is based on the eppy library, see https://pypi.org/project/eppy/

For custom IDF creation, create an instance of IDF (with eppy) and call the methods writing the parts of the IDF you want, either
use the functions in CesarIDFWriter or call directly methods form idf_writer_xxx.

Main API

======================================================================================= ===========================================================
class / module                                                                          description
======================================================================================= ===========================================================
:py:class:`cesarp.eplus_adapter.CesarIDFWriter`                                         creates an IDF file based on :py:class:`cesarp.model.BuildingModel`
                                                                                        connection according to the configuration (by default local file)

:py:mod:`cesarp.eplus_adapter.eplus_sim_runner`                                         run energyplus simulation for exisitng IDF file

:py:mod:`cesarp.eplus_adapter.eplus_eso_results_handling`                               extracts main results from EnergyPlus eso results file

:py:class:`cesarp.eplus_adapter.EPlusEioResultAnalyzer`                                 extracts results from EnergyPlus eio results file, e.g. floor area

:py:mod:`cesarp.eplus_adapter.eplus_error_file_handling`                                extract error level from EnergyPlus err log file

======================================================================================= ===========================================================


"""

import os
from pathlib import Path

_default_config_file = os.path.dirname(__file__) / Path("default_config.yml")
