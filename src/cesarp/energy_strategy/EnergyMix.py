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
from typing import Dict, Any

from cesarp.model.EnergySource import EnergySource


class EnergyMix:
    """
    Note: terms written in CAPS are either set in the configuration or as constants at the beginning of the class definition.

    The class gets PEN Factor and CO2 Emission Coefficient for the EnergySource's defined in Cesar-P.
    For WOOD and GAS the resulting facotrs are combined from different base PEN/CO2 coefficient as defined in the PRIMARY_ENERGY_FACTORS_FILE.
    This takes the mix of different Gas/Wood types into account. As this mix will change over the years and is also dependent on the Energy Strategy,
    input files defining the mix compositions are defined in the energy strategy specific files. EnergySource DHW_OTHERS and HEATING_OTHERS reproduces
    the overall mix of DHW and HEATING system carriers, as for Wood/Gas chaning over the years and dependent on the energy strategy. Those categories
    combine the factors of the "base" Cesar-P EnergySource's, so the intended use is when no detailed information about the energy carrier per building
    is available.
    For Electricity (and thus also HEAT_PUMP) PEN and CO2 are read from a separate file, defining two electricity mixes, one with trade and one without. Factors change over the
    years and depend on the energy strategy
    For EnergySource NO and SOLAR_THERMAL the factors are 0 because there are no emissions during operation.
    EnergySource HEATING_OIL, COAL and DISTRICT_HEATING are directly mapped to a single entry in PRIMARY_ENERGY_FACTORS_FILE, thus without any change over the year and no
    dependency on the Energy Strategy.

    Details about data format of input files:
    Make sure that fuel names in COL_KEY_NAME_OF_FUEL are unique in PRIMARY_ENERGY_FACTORS_FILE and check that you in all XXX_MIX_FILE files you
    use only fule names that exist PRIMARY_ENERGY_FACTORS_FILE, column COL_KEY_NAME_OF_FUEL.
    Reason: When reading PRIMARY_ENERGY_FACTORS_FILE column with name COL_KEY_NAME_OF_FUEL is set as index, kind of Primary Key (Unique). In the XXX_MIX_FILE
    the column with the same name is used as a Foreign Key to get the right row (with matching fuel name) in data read from PRIMARY_ENERGY_FILE.
    """

    COL_KEY_NAME_OF_FUEL = "Name of Fuel"  # indicates column used as index in pandas df for WOOD_MIX_FILE and GAS_MIX_FILE
    COL_KEY_NAME_ENERGY_SOURCE = "CESAR-P EnergySource"  # indicates column used as index in pandas df for DHW_SYSTEM_MIX_FILE and HEATING_SYSTEM_MIX_FILE
    PEF_COL_PEN = "PEN non-renewable [MJ-eq]"
    PEF_COL_CO2_EQUIV = "CO2 Equivalent [kg CO2 - eq]"
    PEF_ROW_DISTRICT_HEATING = "Fernwärme, Durchschnitt CH"
    PEF_ROW_HEATING_OIL = "Heizöl"
    PEF_ROW_COAL = "Kohle Koks"
    # for the ElectricityFactors the rows have to be mapped because there are factors for electricity mix with or without trade
    EL_KEY_COL = 0  # indicates the column which is set as index in the pandas df and used for the row selection
    EL_ROW_PEN_FACTOR = "PEN_FACTOR"
    EL_ROW_CO2_COEFF = "CO2_COEFF"
    EL_ROW_SELECTION_WITH_TRADE = {  # mapping for selection of rows from pandas dataframe and renaming
        "PEN factor with trade": EL_ROW_PEN_FACTOR,
        "CO2 Coefficient with trade": EL_ROW_CO2_COEFF,
    }
    EL_ROW_SELECTION_WITHOUT_TRADE = {  # mapping for selection of rows from pandas dataframe and renaming
        "PEN factor without trade": EL_ROW_PEN_FACTOR,
        "CO2 Coefficient without trade": EL_ROW_CO2_COEFF,
    }

    def __init__(self, unit_registry: pint.UnitRegistry, energy_strategy_config: Dict[str, Any]):
        """
        :param ureg: pint UnitRegistry
        :param energy_strategy_config: dictonary with configuration entries of energy strategy in use
        """
        self.ureg = unit_registry
        self._es_cfg = energy_strategy_config
        primary_energy_factors = pd.read_excel(self._es_cfg["PRIMARY_ENERGY_FACTORS_FILE"], index_col=self.COL_KEY_NAME_OF_FUEL)[[self.PEF_COL_PEN, self.PEF_COL_CO2_EQUIV]]

        if self._es_cfg["ENERGYMIX"]["ELECTRICITY_FACTORS"]["MIX_WITH_TRADE"]:
            row_selection = self.EL_ROW_SELECTION_WITH_TRADE
        else:
            row_selection = self.EL_ROW_SELECTION_WITHOUT_TRADE
        electricity_factors_all_rows = pd.read_excel(self._es_cfg["ENERGYMIX"]["ELECTRICITY_FACTORS"]["PATH"], index_col=self.EL_KEY_COL)
        electricity_factors = electricity_factors_all_rows.loc[row_selection.keys()].rename(row_selection)
        wood_mix_per_period = self.get_mix_input_data(self._es_cfg["ENERGYMIX"]["WOOD_MIX_FILE"], index_col_name=self.COL_KEY_NAME_OF_FUEL)
        gas_mix_per_period = self.get_mix_input_data(self._es_cfg["ENERGYMIX"]["GAS_MIX_FILE"], index_col_name=self.COL_KEY_NAME_OF_FUEL)
        dhw_system_mix_per_period = self.get_mix_input_data(self._es_cfg["ENERGYMIX"]["DHW_SYSTEM_MIX_FILE"], index_col_name=self.COL_KEY_NAME_ENERGY_SOURCE)
        dhw_system_mix_per_period.index = list(map(lambda es_name: EnergySource(es_name), list(dhw_system_mix_per_period.index)))
        heating_system_mix_per_period = self.get_mix_input_data(self._es_cfg["ENERGYMIX"]["HEATING_SYSTEM_MIX_FILE"], index_col_name=self.COL_KEY_NAME_ENERGY_SOURCE)
        heating_system_mix_per_period.index = map(lambda es_name: EnergySource(es_name), list(heating_system_mix_per_period.index))

        self._pen_factors = self._init_factor_lookup_table(
            wood_mix_per_period,
            gas_mix_per_period,
            dhw_system_mix_per_period,
            heating_system_mix_per_period,
            primary_energy_factors[self.PEF_COL_PEN],
            electricity_factors.loc[self.EL_ROW_PEN_FACTOR],
        )

        self._co2_equiv = self._init_factor_lookup_table(
            wood_mix_per_period,
            gas_mix_per_period,
            dhw_system_mix_per_period,
            heating_system_mix_per_period,
            primary_energy_factors[self.PEF_COL_CO2_EQUIV],
            electricity_factors.loc[self.EL_ROW_CO2_COEFF],
        )

    def get_mix_input_data(self, file_path, index_col_name):
        mix_data_all_columns = pd.read_excel(file_path, index_col=index_col_name)
        try:
            mix_data_per_time_period = mix_data_all_columns[self._es_cfg["TIME_PERIODS"]]
        except KeyError as kerr:
            raise EnergyMixInputDataBad(f"One or more time period columns in {file_path} are missing: {kerr}")

        sums_per_period = mix_data_per_time_period.apply(sum)
        if all(sums_per_period < 100.3) and all(sums_per_period > 99.7):
            mix_data_per_time_period = mix_data_per_time_period.applymap(lambda val: val / 100)
        elif not all(sums_per_period == 1):
            raise EnergyMixInputDataBad(f"sum is not 100% for all time periods in {file_path} \n {sums_per_period}")

        return mix_data_per_time_period

    def _init_factor_lookup_table(
        self,
        wood_mix_per_period,
        gas_mix_per_period,
        dhw_system_mix_per_period,
        heating_system_mix_per_period,
        factor_per_energy_source,
        factor_for_electricity,
    ) -> pd.DataFrame:
        def do_mix_with_primaryenergyfactor(time_period_series: pd.Series):
            return sum(pen_fact * type_prc for pen_fact, type_prc in zip(factor_per_energy_source.loc[time_period_series.keys()], time_period_series))

        factors = pd.DataFrame(index=list(EnergySource), columns=self._es_cfg["TIME_PERIODS"])
        factors.loc[EnergySource.NO] = 0
        factors.loc[EnergySource.HEATING_OIL] = factor_per_energy_source.loc[self.PEF_ROW_HEATING_OIL]
        factors.loc[EnergySource.COAL] = factor_per_energy_source.loc[self.PEF_ROW_COAL]
        factors.loc[EnergySource.GAS] = gas_mix_per_period.apply(do_mix_with_primaryenergyfactor)
        factors.loc[EnergySource.WOOD] = wood_mix_per_period.apply(do_mix_with_primaryenergyfactor)
        factors.loc[EnergySource.ELECTRICITY] = factor_for_electricity
        factors.loc[EnergySource.HEAT_PUMP] = factor_for_electricity
        factors.loc[EnergySource.SOLAR_THERMAL] = 0
        factors.loc[EnergySource.DISTRICT_HEATING] = factor_per_energy_source.loc[self.PEF_ROW_DISTRICT_HEATING]

        def do_mix_with_energysource_factors(time_period_series: pd.Series):
            return sum(pen_fact * type_prc for pen_fact, type_prc in zip(factors.loc[time_period_series.keys(), time_period_series.name], time_period_series))

        factors.loc[EnergySource.HEATING_OTHER] = heating_system_mix_per_period.apply(do_mix_with_energysource_factors)
        factors.loc[EnergySource.DHW_OTHER] = dhw_system_mix_per_period.apply(do_mix_with_energysource_factors)

        return factors

    def get_pen_factor_for(self, carrier: EnergySource, time_period: int) -> float:
        assert time_period in self._es_cfg["TIME_PERIODS"], f"requested time period {time_period} not available. Time periods are {self._es_cfg['TIME_PERIODS']}"
        return self._pen_factors.loc[carrier, time_period] * self.ureg.Oileq

    def get_co2_coeff_for(self, carrier: EnergySource, time_period: int) -> float:
        assert time_period in self._es_cfg["TIME_PERIODS"], f"requested time period {time_period} not available. Time periods are {self._es_cfg['TIME_PERIODS']}"
        return self._co2_equiv.loc[carrier, time_period] * self.ureg.kg * self.ureg.CO2eq / self.ureg.MJ


class EnergyMixInputDataBad(Exception):
    def __init__(self, msg):
        Exception(msg)
