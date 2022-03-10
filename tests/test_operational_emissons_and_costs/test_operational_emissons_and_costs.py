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
import cesarp.common
from cesarp.model.EnergySource import EnergySource
from cesarp.emissons_cost.OperationalEmissionsAndCosts import OperationalEmissionsAndCosts


@pytest.fixture
def ureg():
    return cesarp.common.init_unit_registry()


def test_EnergySource_enum():
    assert EnergySource("WOOD") == EnergySource.WOOD
    assert EnergySource("Solar Thermal") == EnergySource.SOLAR_THERMAL
    # legacy cesar matlab energy source number
    assert EnergySource(9) == EnergySource.DISTRICT_HEATING


def test_emissions_and_costs(ureg):
    """
    used testdata captured form cesar matlab for fid2 of sample building site, neighbourhood radius 100, no variability and random constructions
    glazing ratio by age class (with randomization...), infiltration rate by age class
    :param ureg:
    :return:
    """
    EL = "electricity"
    HEATING="heating"
    DHW="dhw"
    TOT="total"
    chf_year = ureg.CHF / ureg.year
    # expected results as were calculated by matlab
    expected_fuel_costs_fid_2 = {HEATING: 19840.28747 * chf_year,
                                 DHW: 2150.536616 * chf_year,
                                 EL: 18348.015 * chf_year
                                 }
    expected_pen_unit = ureg.MJ * ureg.Oileq / ureg.m**2 / ureg.year
    expected_co2_emission_unit = ureg.kg * ureg.CO2eq / ureg.m**2 / ureg.year
    expected_pen_fid_2 = {HEATING: 766.8884093,
                          DHW: 83.12966182,
                          EL: 545.006484,
                          TOT: 1395.024555}
    expected_co2_emisson_fid_2 = {HEATING: 51.74938047,
                                  DHW: 5.609562545,
                                  EL: 8.55846684,
                                  TOT: 65.91740985}

    # demand values for fid 2 of example site wiht 9 buildning, neighbour radios 100
    kWh_per_year = ureg.kW * ureg.h / ureg.year
    kWh_per_m2_per_year = ureg.kW * ureg.h / ureg.m**2 / ureg.year
    dhw_carrier = EnergySource.HEATING_OIL
    dhw_demand = 11.58 * kWh_per_m2_per_year
    tot_dhw_demand = 14475 * kWh_per_year
    heating_carrier = EnergySource.HEATING_OIL
    heating_demand = 139.2 * kWh_per_m2_per_year
    tot_heating_demand = 174010 * kWh_per_year
    el_demand = 57.5630 * kWh_per_m2_per_year
    tot_el_demand = 71953 * kWh_per_year
    op_calc = OperationalEmissionsAndCosts(ureg)

    op_consumption_res = op_calc.get_operational_emissions_and_costs(specific_dhw_demand=dhw_demand,
                                                total_dhw_demand=tot_dhw_demand,
                                                dhw_carrier=dhw_carrier,
                                                specific_heating_demand=heating_demand,
                                                total_heating_demand=tot_heating_demand,
                                                heating_carrier=heating_carrier,
                                                specific_electricity_demand=el_demand,
                                                total_electricity_demand=tot_el_demand,
                                                sim_year=2015)

    # FUEL COSTS
    assert op_consumption_res.heating_system.fuel_cost.u == expected_fuel_costs_fid_2[HEATING].u
    assert op_consumption_res.heating_system.fuel_cost.m == pytest.approx(expected_fuel_costs_fid_2[HEATING].m)
    assert op_consumption_res.dhw_system.fuel_cost.u == expected_fuel_costs_fid_2[DHW].u
    assert op_consumption_res.dhw_system.fuel_cost.m == pytest.approx(expected_fuel_costs_fid_2[DHW].m)
    assert op_consumption_res.electricity.fuel_cost.u == expected_fuel_costs_fid_2[EL].u
    assert op_consumption_res.electricity.fuel_cost.m == pytest.approx(expected_fuel_costs_fid_2[EL].m)

    # PEN
    assert op_consumption_res.dhw_system.pen.u == expected_pen_unit
    assert op_consumption_res.dhw_system.pen.m == pytest.approx(expected_pen_fid_2[DHW])
    assert op_consumption_res.heating_system.pen.u == expected_pen_unit
    assert op_consumption_res.heating_system.pen.m == pytest.approx(expected_pen_fid_2[HEATING])
    assert op_consumption_res.electricity.pen.u == expected_pen_unit
    assert op_consumption_res.electricity.pen.m == pytest.approx(expected_pen_fid_2[EL])
    assert op_consumption_res.total_pen.u == expected_pen_unit
    assert op_consumption_res.total_pen.m == pytest.approx(expected_pen_fid_2[TOT])

    # CO2
    assert op_consumption_res.heating_system.co2_emission.u == expected_co2_emission_unit
    assert op_consumption_res.heating_system.co2_emission.m == pytest.approx(expected_co2_emisson_fid_2[HEATING])
    assert op_consumption_res.dhw_system.co2_emission.u == expected_co2_emission_unit
    assert op_consumption_res.dhw_system.co2_emission.m == pytest.approx(expected_co2_emisson_fid_2[DHW])
    assert op_consumption_res.electricity.co2_emission.u == expected_co2_emission_unit
    assert op_consumption_res.electricity.co2_emission.m == pytest.approx(expected_co2_emisson_fid_2[EL])
    assert op_consumption_res.total_co2_emission.u == expected_co2_emission_unit
    assert op_consumption_res.total_co2_emission.m == pytest.approx(expected_co2_emisson_fid_2[TOT])


def test_emissions_and_costs_no_ec(ureg):
    """
    test that emission and costs are zero if no ennergy carrier for heating and dhw were chosen
    """
    EL = "electricity"
    HEATING="heating"
    DHW="dhw"
    TOT="total"
    # expected results as were calculated by matlab
    expected_pen_unit = ureg.MJ * ureg.Oileq / ureg.m**2 / ureg.year
    expected_co2_emission_unit = ureg.kg * ureg.CO2eq / ureg.m**2 / ureg.year
    expected_fuel_cost_unit = ureg.CHF / ureg.year

    # demand values for fid 2 of example site wiht 9 buildning, neighbour radios 100
    kWh_per_year = ureg.kW * ureg.h / ureg.year
    kWh_per_m2_per_year = ureg.kW * ureg.h / ureg.m**2 / ureg.year
    dhw_carrier = EnergySource.NO
    dhw_demand = 11.58 * kWh_per_m2_per_year
    tot_dhw_demand = 14475 * kWh_per_year
    heating_carrier = EnergySource.NO
    heating_demand = 139.2 * kWh_per_m2_per_year
    tot_heating_demand = 174010 * kWh_per_year
    el_demand = 57.5630 * kWh_per_m2_per_year
    tot_el_demand = 71953 * kWh_per_year
    op_calc = OperationalEmissionsAndCosts(ureg)

    op_consumption_res = op_calc.get_operational_emissions_and_costs(specific_dhw_demand=dhw_demand,
                                                total_dhw_demand=tot_dhw_demand,
                                                dhw_carrier=dhw_carrier,
                                                specific_heating_demand=heating_demand,
                                                total_heating_demand=tot_heating_demand,
                                                heating_carrier=heating_carrier,
                                                specific_electricity_demand=el_demand,
                                                total_electricity_demand=tot_el_demand,
                                                sim_year=2015)

    # FUEL COSTS
    assert op_consumption_res.heating_system.fuel_cost.u == expected_fuel_cost_unit
    assert op_consumption_res.heating_system.fuel_cost.m == 0
    assert op_consumption_res.dhw_system.fuel_cost.u == expected_fuel_cost_unit
    assert op_consumption_res.dhw_system.fuel_cost.m == 0
    assert op_consumption_res.electricity.fuel_cost.u == expected_fuel_cost_unit
    assert op_consumption_res.electricity.fuel_cost.m >= 0

    # PEN
    assert op_consumption_res.dhw_system.pen.u == expected_pen_unit
    assert op_consumption_res.dhw_system.pen.m == 0
    assert op_consumption_res.heating_system.pen.u == expected_pen_unit
    assert op_consumption_res.heating_system.pen.m == 0
    assert op_consumption_res.electricity.pen.u == expected_pen_unit
    assert op_consumption_res.electricity.pen.m >= 0
    assert op_consumption_res.total_pen.u == expected_pen_unit
    assert op_consumption_res.total_pen.m >= 0

    # CO2
    assert op_consumption_res.heating_system.co2_emission.u == expected_co2_emission_unit
    assert op_consumption_res.heating_system.co2_emission.m == 0
    assert op_consumption_res.dhw_system.co2_emission.u == expected_co2_emission_unit
    assert op_consumption_res.dhw_system.co2_emission.m == 0
    assert op_consumption_res.electricity.co2_emission.u == expected_co2_emission_unit
    assert op_consumption_res.electricity.co2_emission.m >= 0
    assert op_consumption_res.total_co2_emission.u == expected_co2_emission_unit
    assert op_consumption_res.total_co2_emission.m >= 0