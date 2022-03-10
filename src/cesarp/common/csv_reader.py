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
import yaml
from pathlib import Path
from typing import Dict, List, Union, Tuple, Any

YAML_DELIMITER = "---"


def read_csv(
    full_file_name: str,
    required_columns: List[str],
    data_labels_mapping: Dict[str, str],
    separator: str = ";",
    index_column_name: str = None,
    drop_unmapped_cols: bool = True,
) -> pd.DataFrame:
    return read_csvy(full_file_name, required_columns, data_labels_mapping, separator, index_column_name, drop_unmapped_cols)


def read_csvy(
    full_file_name: Union[str, Path],
    required_columns: List[str],
    data_labels_mapping: Dict[str, str],
    separator: str = ";",
    index_column_name: str = None,
    drop_unmapped_cols: bool = True,
) -> pd.DataFrame:
    """
    Reads data from CSV or CSVY to a pandas Dataframe. If a YAML header, delimited with --- is found at the beginning of the file this block is ignored.

    :param full_file_name: full path to csv file
    :param required_columns: columns to be read
    :param data_labels_mapping: mapping between names defined in required columns and column names as they are in the csv
    :param separator: optional, value separator used in csv as string, default is ","
    :param index_column_name: optional, column name out of required_columns
    :param drop_unmapped_cols: if True drop columns not specified in required_columns from dataframe, default is True
    :return: Dataframe with columns named as defined in required_columns. Index using column values of
                index_column_name if given, otherwise a numeric index is used.
    """
    assert list(data_labels_mapping.keys()) == required_columns, f"keys of given data_labels {list(data_labels_mapping.keys())} do not match required ones {required_columns}"

    data_labels_orig_to_cesar = dict([(value, key) for key, value in data_labels_mapping.items()])  # use values as keys
    metadata, data_with_orig_labels = read_csvy_raw(full_file_name, separator)

    data_relabeled = data_with_orig_labels.rename(columns=data_labels_orig_to_cesar, errors="raise")
    if drop_unmapped_cols:
        data_relabeled = data_relabeled[required_columns]
    if index_column_name is not None:
        data_relabeled = data_relabeled.set_index(index_column_name, drop=False)
    return data_relabeled


def read_csvy_raw(full_file_name: Union[str, Path], separator: str = ";", encoding="utf-8", header="infer", index_col=None) -> Tuple[Dict[Any, Any], pd.DataFrame]:
    """
    Reading a csvy file (csv tabular data with YAML header, delimitted by ---) and return the metadata and csv data portion separately.
    If no YAML header is found then just read as a plain csv.

    :param full_file_name: full file path to be read
    :type full_file_name: Union[str, Path]
    :param separator: separator used in csv part
    :type separator: str
    :param encoding: forwarding parameter to pandas.read_csv, encoding used in file, defaults to "utf-8"
    :type encoding: str, optional
    :param header: forwarding parameter to pandas.read_csv, defaults to "infer"
    :param index_col: forwarding parameter to pands.read_csv, defaults to None
    :return: (YAML data as dict, csv data as pd.DataFrame)
    :rtype: Tuple[Dict[Any, Any], pd.DataFrame]
    """
    delimiter_hits = 0
    data_with_orig_labels = None
    yaml_lines = []
    with open(full_file_name) as file_handel:
        for line_nr, line_str in enumerate(file_handel, 1):
            if YAML_DELIMITER in line_str:
                delimiter_hits += 1
                if delimiter_hits == 2:
                    break
            elif delimiter_hits == 1:
                yaml_lines.append(line_str)
        if yaml_lines:
            metadata = yaml.safe_load("".join(yaml_lines))
        else:
            metadata = {}
        try:
            data_with_orig_labels = pd.read_csv(file_handel, sep=separator, encoding=encoding, header=header, index_col=index_col)
        except pd.errors.EmptyDataError:
            pass  # no delimiters found, thus file_handel was at end of file... try to read plain csv below
    if data_with_orig_labels is None:
        data_with_orig_labels = pd.read_csv(full_file_name, sep=separator, encoding=encoding, header=header, index_col=index_col)
    return metadata, data_with_orig_labels
