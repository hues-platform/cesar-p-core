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
Customized input parameter checking contracts
Those contracts are used to check input parameters within this package.
Note that this approach with input contracts has only been used within
the geometry package, as we pass often pd.DataFrame for which the python
typing hints do not well describe what is actually expected.
"""
from collections.abc import Iterable
import contracts
import pandas as pd


def coords_2d(arg_to_check):
    """Is arg a dataframe with columns x,y ?"""
    return isinstance(arg_to_check, pd.DataFrame) and "x" in arg_to_check and "y" in arg_to_check


def coords_2d_raw(arg_to_check):
    """Is arg a dataframe with 2 columns?"""
    return isinstance(arg_to_check, pd.DataFrame) and len(arg_to_check.columns) == 2


def coords_3d(arg_to_check):
    """Is arg a dataframe with columns x,y,z ?"""
    return isinstance(arg_to_check, pd.DataFrame) and "x" in arg_to_check and "y" in arg_to_check and "z" in arg_to_check


def coords_3d_raw(arg_to_check):
    """Is arg a dataframe with 3 columns defining x and y and z coordinates ?"""
    return isinstance(arg_to_check, pd.DataFrame) and len(arg_to_check.columns) == 3


def coords_3d_square(arg_to_check):
    """Is arg a rectangular shape in a plane parallel to the z-axis defined by 4 vertices?"""
    if coords_3d(arg_to_check) and len(arg_to_check) == 4:
        return arg_to_check.loc[0, "z"] == arg_to_check.loc[1, "z"] and arg_to_check.loc[2, "z"] == arg_to_check.loc[3, "z"] and arg_to_check.loc[1, "z"] < arg_to_check.loc[2, "z"]
    else:
        return False


def list_coords_3d(arg_to_check):
    """Is arg a list with pandas.DataFrame with columns x,y,z or empty list?"""
    if isinstance(arg_to_check, list):
        if not arg_to_check:  # is empty
            return True
        else:
            return coords_3d(arg_to_check[0])
            # just check the first element, assume the other will be ok to avoid performance leak for a long list...
    else:
        return False


def iterable_coords_2d(arg_to_check):
    """Is arg a list, series or other iterable object with elements pandas.DataFrame[columns=x,y] (or empty)?"""
    if isinstance(arg_to_check, pd.DataFrame) and arg_to_check.empty:  # empty DataFrame is ok
        return True
    if isinstance(arg_to_check, Iterable):
        try:
            return coords_2d(next(iter(arg_to_check)))
            # just check the first element, assume the other will be ok to avoid performance leak for a long list...
        except StopIteration:  # if empty
            return True
    else:
        return False


def list2d_coords_3d_square(arg_to_check):
    """Is arg a list of lists containing as values squares pandas.DataFrame[columns=[x,y,z]]?"""
    if isinstance(arg_to_check, list):
        if len(arg_to_check) == 0:
            return True
        return coords_3d_square(arg_to_check[0][0])
    else:
        return False


def percentage(arg_to_check):
    """Is arg floating point in the range of 0...1?"""
    return (arg_to_check == 1 or arg_to_check == 0) or (contracts.floating_point(arg_to_check) and arg_to_check <= 1)
