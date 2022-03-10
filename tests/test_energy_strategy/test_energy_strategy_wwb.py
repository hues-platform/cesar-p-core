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
import pytest
import os
from pathlib import Path
import cesarp.common
from cesarp.common.AgeClass import AgeClass
from cesarp.common.csv_reader import read_csvy_raw
from cesarp.energy_strategy.EnergyMix import EnergyMix, EnergyMixInputDataBad
from cesarp.model.EnergySource import EnergySource
from cesarp.model.BldgType import BldgType
from cesarp.model.BuildingElement import BuildingElement
from cesarp.energy_strategy.SystemEfficiencies import SystemEfficiencies
from cesarp.energy_strategy.FuelCosts import FuelCosts
from cesarp.energy_strategy.RetrofitRates import RetrofitRates
from cesarp.energy_strategy import get_selected_energy_strategy_cfg

expected_res_folder = os.path.dirname(__file__) / Path("expected_results")


@pytest.fixture
def ureg():
    return cesarp.common.init_unit_registry()

@pytest.fixture
def custom_conf_wwb():
    return {"ENERGY_STRATEGY": {"ENERGY_STRATEGY_SELECTION": "WWB"}}

@pytest.fixture
def wwb_es_cfg():
    return get_selected_energy_strategy_cfg({"ENERGY_STRATEGY":{"ENERGY_STRATEGY_SELECTION": "WWB"}})

def test_energy_mix_co2_coeffs(ureg, wwb_es_cfg):
    energy_mix = EnergyMix(ureg, wwb_es_cfg)
    metadata, expected_co2_coeffs = read_csvy_raw(expected_res_folder / Path("energymix_business_as_usual_co2_coeffs.csvy"), separator=";")
    expected_co2_coeffs.set_index("EnergySource", inplace=True)
    for period_name, expected_period_entries in expected_co2_coeffs.items():
        result_co2_coeffs = {energy_source: energy_mix.get_co2_coeff_for(EnergySource(energy_source), int(period_name)).m for energy_source in expected_period_entries.keys()}
        assert result_co2_coeffs.values() == pytest.approx(expected_period_entries.values.tolist(), rel=0.001)


def test_energy_mix_pen_factors(ureg, wwb_es_cfg):
    energy_mix = EnergyMix(ureg, wwb_es_cfg)
    metadata, expected_pen_factors = read_csvy_raw(expected_res_folder / Path("energymix_business_as_usual_pen_factors.csvy"), separator=";")
    expected_pen_factors.set_index("EnergySource", inplace=True)
    for period_name, expected_period_entries in expected_pen_factors.items():
        result_pen_factors = {energy_source: energy_mix.get_pen_factor_for(EnergySource(energy_source), int(period_name)).m for energy_source in expected_period_entries.keys()}
        assert result_pen_factors.values() == pytest.approx(expected_period_entries.values.tolist(), rel=0.001)


def test_time_period_in_mix_file_missing(ureg):
    custom_config = {"ENERGY_STRATEGY": {
                                         "ENERGY_STRATEGY_SELECTION": "WWB",
                                         "WWB": {"TIME_PERIODS": ["2015", "2020", "2060", "2080"]}
                                         }
                     }
    es_cfg = get_selected_energy_strategy_cfg(custom_config)
    with pytest.raises(EnergyMixInputDataBad):
        energy_mix = EnergyMix(unit_registry=ureg, energy_strategy_config=es_cfg)


def test_system_efficiencies(wwb_es_cfg):
    system_eff = SystemEfficiencies(wwb_es_cfg)
    assert system_eff.get_dhw_system_efficiency(EnergySource.HEAT_PUMP, 2030) == 2.93
    assert system_eff.get_heating_system_efficiency(EnergySource.WOOD, 2050) == 0.77


def test_fuel_costs(ureg, wwb_es_cfg):
    fuel_costs = FuelCosts(ureg, wwb_es_cfg)
    assert fuel_costs.get_fuel_cost_factor(EnergySource.COAL, 2050).m == pytest.approx(7.22/100, abs=0.0001)


def test_full_retrofit_rate(custom_conf_wwb):
    ret_rates = RetrofitRates(custom_conf_wwb)
    full_ret_rates_per_ac = ret_rates.get_full_retrofit_rate_per_age_class(sim_year=2020, bldg_type=BldgType.SFH)
    assert len(full_ret_rates_per_ac) == 19
    assert full_ret_rates_per_ac[AgeClass(max_age=1918)] == 0.06


def test_partial_retrofit_rate_withebox(custom_conf_wwb):
    ret_rates = RetrofitRates(custom_conf_wwb)
    partial_ret_share_per_ac = ret_rates._get_all_partial_retrofit_shares(sim_year=2020,
                                                                            bldg_type=BldgType.SFH)
    assert len(partial_ret_share_per_ac) == 4
    for ac, partial_ret_shares in partial_ret_share_per_ac.items():
        assert len(partial_ret_shares) == 15

    for (bldg_elems, partial_share) in partial_ret_share_per_ac[AgeClass(min_age=1975, max_age=1984)]:
        if bldg_elems == [BuildingElement.WINDOW]:
            assert partial_share == pytest.approx(0.5833)
            break


def test_partial_retrofit_rate(custom_conf_wwb):
    ret_rates = RetrofitRates(custom_conf_wwb)
    partial_ret_rates_per_ac = ret_rates.get_partial_retrofit_rates_per_age_class(sim_year=2030, bldg_type=BldgType.SFH)
    assert len(partial_ret_rates_per_ac) == 19

    ac_to_test = AgeClass(1946, 1960)
    partial_ret_rates = partial_ret_rates_per_ac[ac_to_test]
    assert len(partial_ret_rates) == 4
    ret_rate_sum = 0
    for bldg_elems, ret_rate in partial_ret_rates:
        ret_rate_sum += ret_rate
    assert ret_rate_sum == ret_rates.get_full_retrofit_rate_per_age_class(sim_year=2030, bldg_type=BldgType.SFH)[ac_to_test]

