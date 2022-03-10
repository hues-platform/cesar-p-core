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
import pandas as pd

from cesarp.model.EnergySource import EnergySource


def get_energysource_vs_timeperiod_params_table(filepath, expected_time_periods, COL_NR_ENERGY_CARRIER):
    """
    Get parameters form excel file, having COL_NR_ENERGY_CARRIER string descriptions of the Energy Carrier / Energy Source (matching string values of Enum EnergySource) and
    columns beeing time periods matching time periods defined in configuration TIME_PERIODS.
    :param filepath: full file path to excel file
    :return: pandas dataframe with parameters, index EnergySource and columns time period (int)
    """
    parameters = pd.read_excel(filepath, index_col=COL_NR_ENERGY_CARRIER)
    parameters.index = map(lambda es_name: EnergySource(es_name), list(parameters.index))
    assert all(
        [tp in parameters.columns for tp in expected_time_periods]
    ), f"Time periods {[parameters.columns]} do not match required ones {expected_time_periods} while reading {filepath}"
    return parameters


def check_timeperiod(year, available_time_periods, err_msg_prefix):
    assert year in available_time_periods, f"{err_msg_prefix}: requested {year} is not valid as time period, available are {available_time_periods}"
