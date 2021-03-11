# coding=utf-8
#
# Copyright (c) 2021, Empa, Leonie Fierz, Aaron Bojarski, Ricardo Parreira da Silva, Sven Eggimann.
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
import glob
import re
import logging
import pandas as pd
from pathlib import Path

import cesarp.common
from cesarp.model.Construction import BuildingElement

construction_age_classes = {
    1: cesarp.common.AgeClass(max_age=1918),
    2: cesarp.common.AgeClass(1919, 1948),
    3: cesarp.common.AgeClass(1949, 1978),
    4: cesarp.common.AgeClass(1979, 1994),
    5: cesarp.common.AgeClass(1995, 2001),
    6: cesarp.common.AgeClass(2002, 2006),
    7: cesarp.common.AgeClass(2007, 2009),
    8: cesarp.common.AgeClass(2010, 2014),
    9: cesarp.common.AgeClass(min_age=2015),
}


def read_standard_external_constructions_from_dir(path):

    fnpattern = "*[0-9][0-9][0-9][0-9].idf"
    path = path / Path(fnpattern)
    idf_construction_files = glob.glob(str(path))

    all_constructions = pd.DataFrame(columns={"age_class", "elem_name", "constr_option_nr", "path"})
    for file in idf_construction_files:
        file_name = Path(file).stem
        reMatch = re.match(r"(.*)([0-9]{2})([0-9]{2})", file_name)
        logging.debug("elem {} ageclass {} nr {}".format(reMatch.group(1), int(reMatch.group(2)), reMatch.group(3)))
        all_constructions = all_constructions.append(
            {
                "age_class": construction_age_classes[int(reMatch.group(2))],
                "elem_name": BuildingElement(reMatch.group(1)),
                "constr_option_nr": int(reMatch.group(3)),
                "path": file,
            },
            ignore_index=True,
        )

    return all_constructions


def read_glazing_ratio(cfg, ureg) -> pd.DataFrame:
    path = cfg["PATH"]
    data_labels_mapping = cfg["LABELS"]
    separator = cfg["SEPARATOR"]
    required_columns = ["age_class_nr", "min", "max"]
    glazing_ratio = cesarp.common.read_csvy(path, required_columns, data_labels_mapping, separator, index_column_name="age_class_nr")

    if glazing_ratio["min"].iat[0] > 1 or glazing_ratio["max"].iat[0] > 1:
        glazing_ratio["min"] /= 100
        glazing_ratio["max"] /= 100
    glazing_ratio["min"] = glazing_ratio["min"].apply(lambda x: x * ureg.dimensionless)
    glazing_ratio["max"] = glazing_ratio["max"].apply(lambda x: x * ureg.dimensionless)
    index_to_age_class = {ac_nr: construction_age_classes[ac_nr] for ac_nr in glazing_ratio.index.values}
    glazing_ratio.rename(index=index_to_age_class, inplace=True)

    return glazing_ratio


def read_infiltration_rate(cfg, ureg):
    path = cfg["PATH"]
    data_labels_mapping = cfg["LABELS"]
    separator = cfg["SEPARATOR"]
    required_columns = ["age_class_nr", "ACH_normal_pressure"]
    infiltration = cesarp.common.read_csvy(path, required_columns, data_labels_mapping, separator, index_column_name="age_class_nr")
    index_to_age_class = {ac_nr: construction_age_classes[ac_nr] for ac_nr in infiltration.index.values}
    infiltration.rename(index=index_to_age_class, inplace=True)
    infiltration["ACH_normal_pressure"] = infiltration["ACH_normal_pressure"].apply(lambda x: x * ureg.ACH)
    return infiltration
