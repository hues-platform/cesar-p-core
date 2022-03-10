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

Package to manage retrofit of a site.


There are two retrofit strategies included, which build the main API of that package.
Both are based on :py:class:`cesarp.manager.ProjectManager` to allow for a base run and several scenarios.

============================================================================================== ===========================================================
class                                                                                          description
============================================================================================== ===========================================================
:py:class:`cesarp.retrofit.all_bldgs.SimpleRetrofitManager`                                    Manager class for simple retrofit, retrofitting a selection of building elements for all buildings on the site

:py:class:`cesarp.retrofit.energy_perspective_2050.EnergyPerspective2050RetrofitManager`       Manager class to retrofit buildingsfollowing the EnergyPerspective2050 path

============================================================================================== ===========================================================


If you have any custom requirements regarding the selection of buildings or building elements to be retrofitted, create your own retrofit manager class.
Classes intended to be used when creating your own retrofit manager:

============================================================================ ===========================================================
class/module                                                                 description
============================================================================ ===========================================================
:py:class:`cesarp.retrofit.RetrofitLog`                                      This class is used to keep track of retrofit measures (e.g. by BuildingElementsRetrofitter).
                                                                             Each change of a building element is logged along with the area, costs for retrofit and embodied emissions.

:py:class:`cesarp.retrofit.BuildingElementsRetrofitter`                      Responsible for performing the retrofit for specific building and building element

============================================================================ ===========================================================


Subpackages

============================================================================ ===========================================================
package                                                                      description
============================================================================ ===========================================================
cesarp.retrofit.embodied                                                     Cost and Emission for retrofit of different building elements. Note that those are only costs and emissions for retrofit of existing building elements and
                                                                             per default CESAR-P does not include embodied emissions and costs for new buildings.
                                                                             For the costs there are lookup files in the ressources folder, the embodied emission values are queried from the database (properties of materials)
                                                                             The BuildingElementsRetrofitter respectively the classes used by it do communicate with the classes from embodied.

cesarp.retrofit.all_bldgs                                                    package for simple retrofit, same retrofit for all buildings

cesarp.retrofit.energy_perspective_2050                                      package for retrofit strategy according to EnergyPerspective2050

============================================================================ ===========================================================

"""

import os
from pathlib import Path

_default_config_file = os.path.dirname(__file__) / Path("retrofit_config.yml")
