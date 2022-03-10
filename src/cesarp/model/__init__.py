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
model
============

Data model of cesar-p.

For each building of the site an instance of :py:class:`cesarp.model.BuildingModel` is created.
The model includes all properties of the building needed to create the EnergyPlus IDF file.
If you extend cesar-p with new building properties, as was done e.g. for passive cooling, add the new parameters to the model.
In case you do so, make sure old versions stored to disk can be reloaded by adapting the upgrade_if_necessary() method and you increse the self._class_version in BuildingModel

The BuildingModel is serializable, meaning that you can use pickle to write it to disk. See :py:mod:`cesarp.manager.json_pickling`

This package contains the data model only and no business logic is implemented here. This is done to accomplish a separation of concerns
between assembling all necessary parameters and creating the EnergyPlus specific IDF file from it. The original idea was that with this
architecture we could from the same building model input files for another simulation tool. It turned out that we need quite a lot of
rather EnergyPlus specific parameters, thus the building model is quite linked to EnergyPlus requirements currently.

============================================================================ ===========================================================
class                                                                        description
============================================================================ ===========================================================
:py:class:`cesarp.model.BuildingModel`                                       Parent of the building model, linking to all other model classes.


:py:class:`cesarp.model.BldgType`                                            Building Types supported.

============================================================================ ===========================================================
"""
