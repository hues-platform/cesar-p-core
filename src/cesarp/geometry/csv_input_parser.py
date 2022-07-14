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
Import building shape data from csv or shape file
"""
import pandas as pd
from typing import Dict
from cesarp.geometry import _REQUIRED_SITEVERTICES_PD_COLUMNS


def read_sitevertices_from_csv(file_path, data_labels: Dict[str, str], separator=",") -> pd.DataFrame:
    """
    Read building shape information from csv and aggregate to a DataFrame.
    To each building a unique bld_id is assigned.

    Expected entries per row in csv, each representing one vertex of a building
    'gis_fid': fid identifying building in the external gis tool; expected to be numeric
    'height': height of building in meter
    'x': x coordinate of vertex, meter
    'y': y coordinate of vertex, meter

    :param file_path: full path to csv file
    :param data_labels: dictionary mapping the desired columns to the column names in the input CSV file
    :param separator: data separator, most likely "," or ";"
    :return: pandas DataFrame with one row for each building, columns being 'gis_fid', 'height', 'footprint_shape' and 'bld_id' as index.
            'footprint_shape' is a pandas DataFrame[columns=[x,y]] holding all building vertices
    """
    assert (
        list(data_labels.keys()) == _REQUIRED_SITEVERTICES_PD_COLUMNS
    ), f"keys of given data_labels {list(data_labels.keys())} do not match required ones {_REQUIRED_SITEVERTICES_PD_COLUMNS}"

    allentries = pd.read_csv(file_path, sep=separator)
    data_labels_orig_to_cesar = dict([(value, key) for key, value in data_labels.items()])  # reverse dict
    allentries = allentries.rename(columns=data_labels_orig_to_cesar, errors="raise")
    allentries = allentries.astype({"gis_fid": "int"})

    return allentries
