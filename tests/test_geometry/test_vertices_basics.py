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
import pandas as pd
import pandas.util.testing

from cesarp.geometry import vertices_basics


def test_set_first_corner_as_origin():
    test_input = pd.DataFrame([[10, 5], [10, 10], [25, 10], [25, 5]], columns=["x", "y"]).astype(
        "float64"
    )
    expected_output = pd.DataFrame([[0, 0], [0, 5], [15, 5], [15, 0]], columns=["x", "y"]).astype(
        "float64"
    )
    test_output = vertices_basics.set_first_corner_as_origin(test_input)
    pandas.util.testing.assert_frame_equal(test_output, expected_output)

def test_circumference():
    test_input = pd.DataFrame([[10, 5], [10, 10], [25, 10], [25, 5]], columns=["x", "y"]).astype(
        "float64"
    )
    assert vertices_basics.calc_circumference_of_polygon(test_input) == 40