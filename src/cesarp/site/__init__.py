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
site
============

Package handles parameters depending on the site of the building.

The main reason is handling of weatehr files. We have two options built in, either all buildings are located on the same site and use the same weather file
or each building is located at a different site.

Note that in case of different site per building, we still expect all buildings to be included in the same site vertices input file.
This can grow big and inefficient in case neighbouring buildings shall be modeled. For such cases, you better set up a pipeline processing
each building individually (each building with its own building information file and site vertices file, the latter including its neighbouring buildings).

The classes/modules built to be used as the API of the package:

======================================================================= ===========================================================
class/module                                                            description
======================================================================= ===========================================================
:py:class:`cesarp.site.SingleSiteFactory`                               interface to use when all your buildings are located at the same
                                                                        site, using the same weather file input

:py:class:`cesarp.site.SitePerSwissCommunityFactory`                    interface for distributed site in switzerland, each building is assigned
                                                                        to a community and for each community a weather file is assigned

======================================================================= ===========================================================

"""

import os
from pathlib import Path

_default_config_file = os.path.dirname(__file__) / Path("site_config.yml")
