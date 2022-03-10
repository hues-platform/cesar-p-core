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
from cesarp.manager.SimulationManager import define_fid_batches


def test_idf_batches_create():
    batches = define_fid_batches(range(1, 1000), 30)
    assert batches[0] == range(1, 35)
    for i in range(1, 29):
        assert batches[i] == range(i*34+1, (i+1)*34+1)
    assert batches[29] == range(987, 1000)

def test_batches_small_nr_of_bldgs():
    batches = define_fid_batches(range(1, 33), 30)
    assert batches[0] == range(1, 11)
    assert batches[1] == range(11, 21)
    assert batches[2] == range(21, 31)
    assert batches[3] == range(31, 33)    