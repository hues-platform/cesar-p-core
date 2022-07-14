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
from typing import Dict, Any, Optional
import pint
import cesarp.common
from cesarp.model.BuildingOperation import NightVent, WindowShadingControl
from cesarp.operation import _default_config_file


class PassiveCoolingOperationFactory:
    """
    For documentation about the passive cooling features modeled, namely night ventilation and window shading, see docs/features/passive-cooling.rst
    """

    def __init__(self, ureg: pint.UnitRegistry, custom_cfg: Optional[Dict[str, Any]]):
        self._ureg = ureg
        self._cfg_pckg = cesarp.common.load_config_for_package(_default_config_file, __package__, custom_cfg)

    def create_night_vent(self, bldg_fid: int, max_indoor_temp_profile: Any) -> NightVent:
        """
        Initializes night ventilation model according to configuration parameters.
        Currently, night ventilation has identical parameters for all the buildings.

        :param bldg_fid: fid of the building, currently unused
        :type bldg_fid: int
        :param max_indoor_temp_profile: ScheduleFile or other Schedule type from cesarp.common defining the maximal indoor temperature
        :type max_indoor_temp_profile: Any
        :return: Fully configured NightVent model object. Model might have None values set in case night ventilation is deactivated.
        :rtype: NightVent
        """
        cfg_nv = self._cfg_pckg["NIGHT_VENTILATION"]
        if cfg_nv["ACTIVE"]:
            return NightVent(
                is_active=True,
                flow_rate=self._ureg(cfg_nv["flow_rate"]),
                min_indoor_temperature=self._ureg(cfg_nv["min_indoor_temperature"]),
                maximum_in_out_deltaT=self._ureg(cfg_nv["maximum_in_out_deltaT"]),
                max_wind_speed=self._ureg(cfg_nv["max_wind_speed"]),
                start_hour=cfg_nv["start_hour"],
                end_hour=cfg_nv["end_hour"],
                maximum_indoor_temp_profile=max_indoor_temp_profile,
            )
        else:
            return NightVent.create_empty_inactive()

    def create_win_shading_ctrl(self, bldg_fid: int) -> WindowShadingControl:
        """
        Initializes window shading control according to configuration parameters.
        Currently, shading control has identical parameters for all the buildings.
        Note that the shading device/material is defined in the constructional part and depends on the building age.

        :param bldg_fid: fid of the building, currently unused
        :type bldg_fid: int
        :return: Fully configured WindowShadingControl, but might be inactive
        :rtype: WindowShadingControl
        """
        cfg_ws = self._cfg_pckg["WINDOW_SHADING_CONTROL"]
        if cfg_ws["ACTIVE"]:
            return WindowShadingControl(
                is_active=True, is_exterior=cfg_ws["is_exterior"], radiation_min_setpoint=self._ureg(cfg_ws["rad_min_set"]), shading_control_type=cfg_ws["shading_control_type"]
            )
        else:
            return WindowShadingControl.create_empty_inactive()
