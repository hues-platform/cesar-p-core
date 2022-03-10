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
from typing import Protocol, Any
from cesarp.model.BuildingOperation import WindowShadingControl, NightVent


class PassiveCoolingOperationFactoryProtocol(Protocol):
    def create_night_vent(self, bldg_fid: int, max_indoor_temp_profile: Any) -> NightVent:
        """
        Create and return a night ventilation data object, initialized with data appropriately
        :param max_indoor_temp_profile: [description]
        :type max_indoor_temp_profile: cesarp.common.ScheduleFixedValue, ScheduleFile, ScheduleValues
        :return: NightVent object
        :rtype: NightVent
        """
        ...

    def create_win_shading_ctrl(self, bldg_fid: int) -> WindowShadingControl:
        ...
