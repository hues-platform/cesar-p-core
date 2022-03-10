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
import pint
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from enum import Enum
from cesarp.model.BuildingElement import BuildingElement


class LOG_KEYS(Enum):
    BLDG_FID = "bldg_fid"
    BLDG_ELEMENT = "bldg_element"
    RETROFITTED_AREA = "retrofitted_area"
    YEAR_OF_RETROFIT = "year"
    RETROFIT_TARGET = "retrofit_target"
    COSTS = "costs"
    NON_RENEWABLE_PEN = "non_renewable_pen"
    CO2_EMISSION = "co2_emission"
    OLD_CONSTRUCTION_NAME = "old_construction_name"
    NEW_CONSTRUCTION_NAME = "new_construction_name"


class RetrofitLog:
    """
    Log retrofit entries. Log can either by used per building or for a site, as building fid is included in each
    entry.
    The idea is to save the retrofit information as fine grained as possible. To get any information out of the log,
    the best is to convert it to a dataframe with convert_to_df method and then e.g. sum the costs column
    or query how many buildings got a window retrofitted or whatever information interests you.
    """

    def __init__(self):
        self.my_log_entries: List[Dict[LOG_KEYS, Any]] = []

    def log_retrofit_measure(
        self,
        bldg_fid: int,
        bldg_element: BuildingElement,
        retrofitted_area: pint.Quantity,
        year_of_retrofit: Optional[int],
        retrofit_target: str,
        costs: pint.Quantity,
        non_renewable_pen: pint.Quantity,
        co2_emission: pint.Quantity,
        old_construction_name: str,
        new_construction_name: str,
    ):
        self.my_log_entries.append(
            {
                LOG_KEYS.BLDG_FID: bldg_fid,
                LOG_KEYS.BLDG_ELEMENT: bldg_element,
                LOG_KEYS.RETROFITTED_AREA: retrofitted_area,
                LOG_KEYS.YEAR_OF_RETROFIT: year_of_retrofit,
                LOG_KEYS.RETROFIT_TARGET: retrofit_target,
                LOG_KEYS.COSTS: costs,
                LOG_KEYS.NON_RENEWABLE_PEN: non_renewable_pen,
                LOG_KEYS.CO2_EMISSION: co2_emission,
                LOG_KEYS.OLD_CONSTRUCTION_NAME: old_construction_name,
                LOG_KEYS.NEW_CONSTRUCTION_NAME: new_construction_name,
            }
        )

    def was_construction_retrofitted_in(self, year: int, bldg_fid: int = None) -> bool:
        if not self.my_log_entries:
            return False
        if not bldg_fid:
            try:
                bldg_fid = self.my_log_entries[0][LOG_KEYS.BLDG_FID]
            except KeyError:
                return False
            assert all([e[LOG_KEYS.BLDG_FID] == bldg_fid for e in self.my_log_entries]), "no bldg fid passed to but log has entries from multiple buildings"

        # TODO add more criteria to only get constructional retrofit when log is extended for system retrofit
        any_construction_retrofit_measure = any([entry[LOG_KEYS.YEAR_OF_RETROFIT] == year and entry[LOG_KEYS.BLDG_FID] == bldg_fid for entry in self.my_log_entries])
        return any_construction_retrofit_measure

    def append_log(self, ret_log_to_append):
        self.my_log_entries + ret_log_to_append.my_log_entries

    def save(self, filepath: Union[str, Path]) -> None:
        """
        Save the retrofit log as a csv.

        :param filepath: filename with full path to write retrofit log to
        :type filepath: Union[str, path]
        """
        if self.my_log_entries:
            log_as_df = self.convert_to_df()
            log_as_df.to_csv(filepath)
        else:
            logging.getLogger(__name__).info("did not write retrofit log because it is empty")

    def convert_to_df(self) -> pd.DataFrame:
        """
        :return: the retrofit log as a dataframe. Each retrofit measure as a row, columns are the entries of LOG_KEYS enum
        :rtype: pd.DataFrame
        """
        log_as_df = pd.DataFrame(self.my_log_entries)
        log_as_df.columns = [log_key.value for log_key in LOG_KEYS]
        return log_as_df

    def get_sum_of_costs_and_emissions(self) -> Dict[str, pint.Quantity]:
        """
        Returns a pandas DataSeries (which can be queried like a dict) with entries "costs", "co2_emission", "non_renewable_pen",
        each having as a value the sum of those LOG_KEYS over all retrofit log entries as a pint.Quantity.

        :return: pandas Series with sum of costs and emission, as described above
        :rtype: Dict[str, pint.Quantity]
        """
        ret_log_as_df = self.convert_to_df()
        return ret_log_as_df[[LOG_KEYS.COSTS.value, LOG_KEYS.CO2_EMISSION.value, LOG_KEYS.NON_RENEWABLE_PEN.value]].apply(sum)
