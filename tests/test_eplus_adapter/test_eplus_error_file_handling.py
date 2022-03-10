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
import os
import pytest
from pathlib import Path
from cesarp.eplus_adapter.eplus_error_file_handling import check_eplus_error_level, EplusErrorLevel


@pytest.mark.parametrize(
    "err_file_name,expected_err_level",
    [
        ("eplusout_ip_note.err", EplusErrorLevel.IP_NOTE),
        ("eplusout_warning.err", EplusErrorLevel.WARNING),
        ("eplusout_severe.err", EplusErrorLevel.SEVERE),
        ("eplusout_fatal.err", EplusErrorLevel.FATAL),
    ]
)
def test_get_eplus_error_level(err_file_name, expected_err_level):
    eplus_err_file = os.path.dirname(__file__) / Path("testfixture") / Path(err_file_name)
    err_level = check_eplus_error_level(eplus_err_file)
    assert err_level == expected_err_level
