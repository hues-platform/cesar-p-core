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

Main pipelining code and main API classes for CESAR-P.

Note that for retrofit there are the manager classes in :py:class:`cesarp.retrofit`.


Main API classes

============================================================================ ===========================================================
class                                                                        description
============================================================================ ===========================================================
:py:class:`cesarp.manager.SimulationManager`                                 Provides basic pipeline to run simulations for many buildings in one site vertices file.

:py:class:`cesarp.manager.ProjectManager`                                    As the SimulationManager, but allows to run different scenarios.

:py:class:`cesarp.manager.ProjectSaver`                                      Stores your project containing all input files to a ZIP (to transfer or as a long-term save).
                                                                             Note that you must create the ProjectSaver within your main script, as it is not included in the Manager classes above.

:py:mod:`cesarp.manager.debug_method`                                     If something goes wrong and you do not see why, this module is useful to be able to process just one building (without multiprocessing)

============================================================================ ===========================================================


Classes to interface with if you create your own pipeline. A own pipeline makes sense if you have only one building per site vertices file
or you need to run the same IDF files with different weather files.

============================================================================ ===========================================================
class                                                                        description
============================================================================ ===========================================================
:py:class:`cesarp.manager.BldgModelFactory`                                  This is the main point for assemblind the :py:class:`cesarp.model.BuildingModel` for
                                                                             each building on your site. It hooks all the different factories creating part of the building model.
                                                                             It is here where the input files with per building information and the site vertices are read.
                                                                             Also here the decisions e.g. whether we use SIA2024 package or fixed properties for the operational parameters
                                                                             are implemented.

:py:class:`cesarp.manager.BuildingContainer`                                 This is a data class, holding all information for one building, from the BuildingModel to the SimulationResults.
                                                                             The class can be pickled to a json file, so you can store your simulation and reload them for later use.

:py:class:`cesarp.manager.FileStorageHandler`                                Does manage file pathes for all the files that are created during the pipeline, might or might not be useful if you create your own pipeline

:py:mod:`cesarp.manager.json_pickling`                                       Saving a BuildingContainer or BuildingModel to disk (actually any object, but tested and used for those two)

============================================================================ ===========================================================


"""


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
