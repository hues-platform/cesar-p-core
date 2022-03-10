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
import pint
from cesarp.common import config_loader


class EnergyTargetLookup:
    """
    Reading energy targets for new/retrofitted residential buildings from given configuration
    """

    _KEY_RESIDENTIAL = "RESIDENTIAL"
    _KEY_NEW = "NEW"
    _KEY_RETROFITTED = "RETROFITTED"
    _KEY_OP_PEN = "OPERATIONAL_NON_RENEWABLE_PEN"
    _KEY_OP_CO2 = "OPERATIONAL_CO2_EMISSION"

    def __init__(self, file_path, ureg: pint.UnitRegistry):
        self._ureg = ureg
        self._energy_target_cfg = config_loader.load_config_full(file_path)
        self.pen_unit = ureg.MJ * ureg.Oileq / ureg.m ** 2 / ureg.year
        self.co2_unit = ureg.kg * ureg.CO2eq / ureg.m ** 2 / ureg.year

    def get_resi_op_pen_target(self, new_bldg: bool) -> pint.Quantity:
        """
        :param new_bldg: if true, target for newly built building is returend, otherwise for retrofitted building
        :return: non renewable primary energy consumption target for a residentail building
        """
        if new_bldg:
            pen_target = self._ureg(self._energy_target_cfg[self._KEY_RESIDENTIAL][self._KEY_NEW][self._KEY_OP_PEN])
        else:
            pen_target = self._ureg(self._energy_target_cfg[self._KEY_RESIDENTIAL][self._KEY_RETROFITTED][self._KEY_OP_PEN])
        return pen_target.to(self.pen_unit)

    def get_resi_op_co2_target(self, new_bldg: bool) -> pint.Quantity:
        """
        :param new_bldg: if true, target for newly built building is returend, otherwise for retrofitted building
        :return: co2 emission target for a residentail building
        """
        if new_bldg:
            co2_target = self._ureg(self._energy_target_cfg[self._KEY_RESIDENTIAL][self._KEY_NEW][self._KEY_OP_CO2])
        else:
            co2_target = self._ureg(self._energy_target_cfg[self._KEY_RESIDENTIAL][self._KEY_RETROFITTED][self._KEY_OP_CO2])
        return co2_target.to(self.co2_unit)
