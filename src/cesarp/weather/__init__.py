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

Package handles weather files per community and is used together with :py:class:`cesarp.site.SitePerSwissCommunityFactory`

The classes/modules built to be used from outside (API of package):

============================================================================ ====================================================
class/module                                                                 description
============================================================================ ====================================================
:py:class:`cesarp.weather.swiss_communities.SwissCommunityWeatherChooser`    mapping a weather file to each community

============================================================================ ====================================================

"""
