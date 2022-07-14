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
from typing import Dict, Any, List, Tuple, Optional
import pandas as pd

from cesarp.common.AgeClass import AgeClass
from cesarp.model.BuildingElement import BuildingElement
from cesarp.model.BldgType import BldgType
from cesarp.energy_strategy import get_selected_energy_strategy_cfg
from cesarp.energy_strategy.input_parser_helper import check_timeperiod


class RetrofitRates:
    """
    Query the retrofit rates according to set energy strategy.
    Only supports BldgType.SFH and BldgType.MFH and assumes that they have identical age classes.
    """

    _COL_LABEL_YOC = "Year of Construction"
    _COL_LABEL_PARTIAL_AC_MAPPING = "AgeRangePartialRetrofit"
    _COL_LABEL_BLDG_ELEMS = "Building Element"

    def __init__(self, custom_config: Optional[Dict[str, Any]] = None):
        self._es_cfg = get_selected_energy_strategy_cfg(custom_config)
        self._full_rates = {
            BldgType.SFH: self.__read_full_rates(BldgType.SFH),
            BldgType.MFH: self.__read_full_rates(BldgType.MFH),
        }

        self._partial_shares = {
            BldgType.SFH: self.__read_partial_shares(BldgType.SFH),
            BldgType.MFH: self.__read_partial_shares(BldgType.MFH),
        }

        self.time_periods = self._es_cfg["TIME_PERIODS"]

    def get_retrofit_rates_age_classes(self):
        """
        Attention, assumes that age classes used for SFH and MFH are identical!

        :return: all age classes used in the full retrofit rate table.
        """
        return list(self._full_rates[BldgType.SFH].index)

    def get_full_retrofit_rate_per_age_class(self, sim_year: int, bldg_type: BldgType) -> Dict[AgeClass, float]:
        check_timeperiod(sim_year, self.time_periods, "full retrofit rates")
        rates_for_sim_period = self._full_rates[bldg_type][sim_year].to_dict()
        return rates_for_sim_period

    def get_partial_retrofit_rates_per_age_class(self, sim_year: int, bldg_type: BldgType) -> Dict[AgeClass, List[Tuple[List[BuildingElement], float]]]:
        check_timeperiod(sim_year, self.time_periods, __name__)
        all_partial_ret_shares: Dict[AgeClass, List[Tuple[List[BuildingElement], float]]] = self._get_all_partial_retrofit_shares(sim_year, bldg_type)
        full_ret_rates = self.get_full_retrofit_rate_per_age_class(sim_year, bldg_type)
        full_ret_to_part_ret_ac_mapping = self._get_mapping_full_ac_to_retrofit_ac(bldg_type)

        partial_ret_rates_per_ac: Dict[AgeClass, List[Tuple[List[BuildingElement], float]]] = {}
        for full_ret_ac, full_ret_rate in full_ret_rates.items():
            part_ret_ac = full_ret_to_part_ret_ac_mapping[full_ret_ac]
            part_ret_shares_for_ac = all_partial_ret_shares[part_ret_ac]
            ret_rates = [(bldg_elems_list, full_ret_rate * partial_ret_share) for (bldg_elems_list, partial_ret_share) in part_ret_shares_for_ac if partial_ret_share > 0]
            partial_ret_rates_per_ac[full_ret_ac] = ret_rates
        return partial_ret_rates_per_ac

    def _get_mapping_full_ac_to_retrofit_ac(self, bldg_type: BldgType) -> Dict[AgeClass, AgeClass]:
        return self._full_rates[bldg_type][self._COL_LABEL_PARTIAL_AC_MAPPING].to_dict()

    def _get_all_partial_retrofit_shares(self, sim_year: int, bldg_type: BldgType):
        try:
            partial_shares_df = self._partial_shares[bldg_type].loc[:, [sim_year, self._COL_LABEL_BLDG_ELEMS]]
            ret_shares_per_ac = {}
            for age_class in set(partial_shares_df.index):
                shares_for_ac = []
                for idx, row in partial_shares_df.loc[age_class].iterrows():
                    shares_for_ac.append((row["Building Element"], row[sim_year]))
                ret_shares_per_ac[age_class] = shares_for_ac
            return ret_shares_per_ac
        except KeyError:
            print(f"no partial retrofit share found for simulation period {sim_year}, bldg type {bldg_type.name}")
            raise

    def __read_full_rates(self, bldg_type: BldgType):
        """
        :param bldg_type:
        :return: pandas df, index is AgeClass() instance, representing year of construction range
        """
        full_ret_rates = self.__read_raw_df(self._es_cfg["RETROFIT"]["FULL_RATES"][bldg_type.name])
        idx = full_ret_rates[self._COL_LABEL_YOC].apply(lambda yoc: AgeClass.from_string(yoc))
        full_ret_rates.set_index(idx, inplace=True)
        full_ret_rates.drop(self._COL_LABEL_YOC, axis="columns", inplace=True)
        ac_to_part_ret_ac = full_ret_rates[self._COL_LABEL_PARTIAL_AC_MAPPING].apply(lambda ac: AgeClass.from_string(ac))
        full_ret_rates.drop(self._COL_LABEL_PARTIAL_AC_MAPPING, axis="columns", inplace=True)
        full_ret_rates.columns = [int(col_idx) for col_idx in full_ret_rates.columns]
        full_ret_rates = full_ret_rates.applymap(lambda x: x / 100)  # in input files retrofit rates are in % from 0..100
        return pd.concat([full_ret_rates, ac_to_part_ret_ac], axis="columns")

    def __read_partial_shares(self, bldg_type: BldgType):
        partial_ret_shares = self.__read_raw_df(self._es_cfg["RETROFIT"]["PARTIAL_SHARES"][bldg_type.name])
        idx = partial_ret_shares[self._COL_LABEL_YOC].apply(lambda yoc: AgeClass.from_string(yoc))
        partial_ret_shares.set_index(idx, inplace=True)
        partial_ret_shares.drop(self._COL_LABEL_YOC, axis="columns", inplace=True)
        partial_ret_shares.columns = [int(col_idx) if col_idx != self._COL_LABEL_BLDG_ELEMS else col_idx for col_idx in partial_ret_shares.columns]
        bldg_elem_col = partial_ret_shares[self._COL_LABEL_BLDG_ELEMS].apply(self.__convert_bldg_elems_str_to_enum_array)
        partial_ret_shares.drop(self._COL_LABEL_BLDG_ELEMS, axis="columns", inplace=True)  # remove column to be able to use applymap on all numeric entries...
        partial_ret_shares = partial_ret_shares.applymap(lambda x: x / 100)  # in input files retrofit rates are in % from 0..100
        partial_ret_shares = pd.concat([partial_ret_shares, bldg_elem_col], axis="columns")  # add bldg elem col again
        return partial_ret_shares

    @staticmethod
    def __convert_bldg_elems_str_to_enum_array(bldg_elems_as_str: str) -> List[BuildingElement]:
        """
        :param bldg_elems_as_str: string with building element names separated by +
        :return: array containing the building elmenets as BuildingElement Enum instances
        """
        return [BuildingElement(bldg_elem_name.strip()) for bldg_elem_name in bldg_elems_as_str.split("+")]

    def __read_raw_df(self, file_cfg):
        return pd.read_csv(file_cfg["PATH"], sep=file_cfg["SEPARATOR"])
