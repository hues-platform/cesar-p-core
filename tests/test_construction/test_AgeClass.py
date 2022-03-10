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
import logging
from cesarp.common.AgeClass import AgeClass


def test_age_class_equal():
    logging.getLogger().setLevel(logging.DEBUG)
    a = AgeClass()
    equal_to_a = AgeClass()
    assert a == equal_to_a

    a = AgeClass(1987, 2000)
    equal_to_a = AgeClass(1987, 2000)
    assert a == equal_to_a

    b = AgeClass(1988, 2000)
    assert a != b
    b.min_age = a.min_age
    assert a == b

    b = AgeClass(1987, 2001)
    assert a != b
    b.max_age = a.max_age
    assert a == b

