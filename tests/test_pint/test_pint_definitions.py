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
import cesarp.common


def test_dimensionless_solar_absorptance():
    ureg = cesarp.common.init_unit_registry()
    solar_absorptance_unit = ureg.solar_absorptance
    sol_abs_val = 0.5 * ureg.solar_absorptance
    assert sol_abs_val.m == 0.5
    assert sol_abs_val.u == solar_absorptance_unit
    assert 0.5 * ureg.dimensionless == sol_abs_val.to(ureg.dimensionless)


def test_percent():
    ureg = cesarp.common.init_unit_registry()
    assert (20 * ureg.percent).to(ureg.dimensionless) == 0.2 * ureg.dimensionless
