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
import copy
import os
from pathlib import Path

import cesarp.common
from cesarp.common.AgeClass import AgeClass
from cesarp.model.BuildingElement import BuildingElement
from cesarp.model.BuildingModel import BuildingModel
from cesarp.model.Site import Site
from cesarp.model.BldgType import BldgType
from cesarp.model.EnergySource import EnergySource
from cesarp.model.BuildingConstruction import BuildingConstruction, InstallationsCharacteristics
from cesarp.model.BldgShape import BldgShapeDetailed
from cesarp.results.EnergyDemandSimulationResults import EnergyDemandSimulationResults
from cesarp.manager.BuildingContainer import BuildingContainer
from cesarp.retrofit.RetrofitLog import RetrofitLog
from cesarp.emissons_cost.OperationalEmissionsAndCosts import OperationalEmissionsAndCostsResult

from cesarp.retrofit.energy_perspective_2050.EnergyPerspective2050BldgElementsRetrofitter import EnergyPerspective2050BldgElementsRetrofitter

class ConstrRetrofitterMock:
    retrofit_log = RetrofitLog()
    def set_year_of_retrofit(self, year):
        pass

    def set_bldg_elems_to_retrofit(self, bldg_elems):
        pass

    def retrofit_bldg_construction(self,
                                   bldg_fid: int,
                                   bldg_construction: BuildingConstruction,
                                   bldg_shape_detailed: BldgShapeDetailed):
        pass

    def reset_retrofit_log(self):
        pass


@pytest.fixture
def mock_ret_rates_cfg():
    fixture_path = os.path.dirname(__file__) / Path("testfixture") / Path("energy_strategy")
    ret_rates_input_files = {
        "ENERGY_STRATEGY":
        {
            "ENERGY_STRATEGY_SELECTION": "WWB",
            "WWB":
                {
                    "RETROFIT" :
                    {
                        "FULL_RATES" :
                        {
                            "SFH": {"PATH": fixture_path / Path("FullyRetrofitRates_EFH_Mock.csv")},
                            "MFH": {"PATH": fixture_path / Path("FullyRetrofitRates_MFH_Mock.csv")}
                        },
                        "PARTIAL_SHARES":
                        {
                            "SFH": {"PATH": fixture_path / Path("PartialRetrofitShares_EFH_Mock.csv")},
                            "MFH": {"PATH": fixture_path / Path("PartialRetrofitShares_MFH_Mock.csv")}
                        }
                    },
            }
        }
    }
    return ret_rates_input_files


def create_mock_bldg_containers(ureg):
    mock_containers = {fid: BuildingContainer() for fid in range(1, 8)}

    bldg_constr = BuildingConstruction(None,None,None,None,None,None,None,None,
                                       InstallationsCharacteristics(None, None, None, None,
                                                                    EnergySource.ELECTRICITY, # DHW
                                                                    EnergySource.HEATING_OIL)) # Heating

    mock_model = BuildingModel(fid=1,
                               year_of_construction=1977,
                               site=Site("", None, 2020),
                               bldg_shape=None,
                               neighbours=None,
                               neighbours_construction_props=None,
                               bldg_construction=bldg_constr,
                               bldg_operation_mapping=None,
                               bldg_type=BldgType.MFH)

    bldg_model_1 = copy.deepcopy(mock_model)
    bldg_model_1.fid = 1
    bldg_model_1.bldg_type = BldgType.SFH
    bldg_model_1.year_of_construction = 1901
    mock_containers[1].set_bldg_model(bldg_model_1)
    bldg_model_2 = copy.deepcopy(mock_model)
    bldg_model_2.fid = 2
    bldg_model_2.bldg_type = BldgType.MFH
    bldg_model_2.year_of_construction = 1977
    mock_containers[2].set_bldg_model(bldg_model_2)
    bldg_model_3 = copy.deepcopy(mock_model)
    bldg_model_3.fid = 3
    bldg_model_3.bldg_type = BldgType.MFH
    bldg_model_3.year_of_construction = 1977
    mock_containers[3].set_bldg_model(bldg_model_3)
    bldg_model_4 = copy.deepcopy(mock_model)
    bldg_model_4.fid = 4
    bldg_model_4.bldg_type = BldgType.MFH
    bldg_model_4.year_of_construction = 1977
    bldg_model_4.bldg_construction.installation_characteristics.e_carrier_dhw = EnergySource.SOLAR_THERMAL
    bldg_model_4.bldg_construction.installation_characteristics.e_carrier_heating = EnergySource.SOLAR_THERMAL
    mock_containers[4].set_bldg_model(bldg_model_4)
    bldg_model_5 = copy.deepcopy(mock_model)
    bldg_model_5.fid = 5
    bldg_model_5.bldg_type = BldgType.MFH
    bldg_model_5.year_of_construction = 2000
    mock_containers[5].set_bldg_model(bldg_model_5)
    bldg_model_6 = copy.deepcopy(mock_model)
    bldg_model_6.fid = 6
    bldg_model_6.bldg_type = BldgType.SFH
    bldg_model_6.year_of_construction = 1995
    mock_containers[6].set_bldg_model(bldg_model_6)
    bldg_model_7 = copy.deepcopy(mock_model)
    bldg_model_7.fid = 7
    bldg_model_7.bldg_type = BldgType.SFH
    bldg_model_7.year_of_construction = 1995
    mock_containers[7].set_bldg_model(bldg_model_7)
    return mock_containers


def create_mock_containers_with_results(ureg):
    mock_containers = create_mock_bldg_containers(ureg)
    prev_sim_year = 2015
    kwh_year=ureg.kW*ureg.h/ureg.year

    energy_demand_res = EnergyDemandSimulationResults(
                                tot_dhw_demand=10000 * kwh_year,
                                tot_heating_demand=180000 * kwh_year,
                                tot_electricity_demand=80000 * kwh_year,
                                tot_cooling_demand=0 * kwh_year,
                                total_floor_area=250*ureg.m**2)

    for c in mock_containers.values():
        c.get_bldg_model().site.simulation_year = prev_sim_year
        c.set_energy_demand_sim_res(energy_demand_res)
        c.set_retrofit_log(RetrofitLog())

    retrofit_log_fid3 = RetrofitLog()
    retrofit_log_fid3.log_retrofit_measure(3, BuildingElement.WALL, None, prev_sim_year, None, None, None, None,
                                           "old_wall_constr", "new_wall_constr")
    mock_containers[3].set_retrofit_log(retrofit_log_fid3)


    energy_demand_low = EnergyDemandSimulationResults(
                                tot_dhw_demand=5000 * kwh_year,
                                tot_heating_demand=60000 * kwh_year,
                                tot_electricity_demand=5000 * kwh_year,
                                tot_cooling_demand=0 * kwh_year,
                                total_floor_area=250*ureg.m**2)

    mock_containers[4].set_energy_demand_sim_res(energy_demand_low)

    return mock_containers


def test_basic_retrofit():
    ureg = cesarp.common.init_unit_registry()
    last_period_bldg_containers = create_mock_bldg_containers(ureg)
    retrofitter = EnergyPerspective2050BldgElementsRetrofitter(ureg)
    assert retrofitter._energy_target.get_resi_op_pen_target(False).m == 250
    assert retrofitter._energy_target.get_resi_op_pen_target(True).m == 200


def test_with_full_retrofit_only(mock_ret_rates_cfg):
    ureg = cesarp.common.init_unit_registry()
    mock_ret_rates_cfg["ENERGY_PERSPECTIVE_2050"] = {"DO_PARTIAL_RETROFIT": False}

    containers_prev_sim = create_mock_containers_with_results(ureg)
    containers_current = create_mock_bldg_containers(ureg)
    retrofitter = EnergyPerspective2050BldgElementsRetrofitter(ureg, custom_config=mock_ret_rates_cfg)
    retrofitter._per_elem_construction_retrofitter = ConstrRetrofitterMock()
    retrofitter.retrofit_site(2020, containers_current, containers_prev_sim)
    print("\nSFH\n====\n")
    for x in retrofitter._retrofit_categories_last_run[BldgType.SFH]:
        print(f"{x.constr_ac}; {x.bldg_elems_to_retrofit}; {x.target_nr_of_bldgs_to_retrofit}; {x.nr_of_bldgs_retrofitted}")
        if x.constr_ac == AgeClass(min_age=None, max_age=1918):
            assert x.target_nr_of_bldgs_to_retrofit == 1
            assert x.nr_of_bldgs_retrofitted == 1
        if x.constr_ac == AgeClass(min_age=1991, max_age=1995):
            # two buildings in that age class, but retrofit only requires one to be retrofitted
            assert x.target_nr_of_bldgs_to_retrofit == 1
            assert x.nr_of_bldgs_retrofitted == 1

    print("\nMFH\n====\n")
    for x in retrofitter._retrofit_categories_last_run[BldgType.MFH]:
        print(f"{x.constr_ac}; {x.bldg_elems_to_retrofit}; {x.target_nr_of_bldgs_to_retrofit}; {x.nr_of_bldgs_retrofitted}")
        if x.constr_ac == AgeClass(min_age=1971, max_age=1980):
            # there are three bldg in that age class, with retrofit rate of 90% acutally 3 out of 3 buildings would
            # be retrofitted, but one had a retrofit in the last period and one reaches energy target, thus  only one
            # builing gets retrofitted
            assert x.target_nr_of_bldgs_to_retrofit == 3
            assert x.nr_of_bldgs_retrofitted == 1
        if x.constr_ac == AgeClass(min_age=1996, max_age=2000):
            # there is a bldg in that age class, but retrofit rate too low
            assert x.target_nr_of_bldgs_to_retrofit == 0
            assert x.nr_of_bldgs_retrofitted == 0



def test_with_partial_retrofit(mock_ret_rates_cfg):
    ureg = cesarp.common.init_unit_registry()
    mock_ret_rates_cfg["ENERGY_PERSPECTIVE_2050"] = {"DO_PARTIAL_RETROFIT": True}
    containers_prev_sim = create_mock_containers_with_results(ureg)
    containers_current = create_mock_bldg_containers(ureg)
    retrofitter = EnergyPerspective2050BldgElementsRetrofitter(ureg, custom_config=mock_ret_rates_cfg)
    retrofitter._per_elem_construction_retrofitter = ConstrRetrofitterMock()
    retrofitter.retrofit_site(2020, containers_current, containers_prev_sim)

    for x in retrofitter._retrofit_categories_last_run[BldgType.SFH]:
        #print(f"{x.constr_ac}; {x.bldg_elems_to_retrofit}; {x.target_nr_of_bldgs_to_retrofit}; {x.nr_of_bldgs_retrofitted}")
        if x.constr_ac == AgeClass(min_age=1991, max_age=1995):
            if x.bldg_elems_to_retrofit == [BuildingElement.WINDOW]:
                assert x.target_nr_of_bldgs_to_retrofit == 1
                assert x.nr_of_bldgs_retrofitted ==1
            else:
                x.target_nr_of_bldgs_to_retrofit == 0

    tot_retrofitted_ac_1977 = 0
    tot_to_retrofit_ac_1977 = 0
    for x in retrofitter._retrofit_categories_last_run[BldgType.MFH]:
        #print(f"{x.constr_ac}; {x.bldg_elems_to_retrofit}; {x.target_nr_of_bldgs_to_retrofit}; {x.nr_of_bldgs_retrofitted}")
        if x.constr_ac == AgeClass(min_age=1971, max_age=1980):
            tot_retrofitted_ac_1977 += x.nr_of_bldgs_retrofitted
            tot_to_retrofit_ac_1977 += x.target_nr_of_bldgs_to_retrofit
            if x.bldg_elems_to_retrofit == [BuildingElement.ROOF]:
                assert x.target_nr_of_bldgs_to_retrofit == 1
            elif x.bldg_elems_to_retrofit == [BuildingElement.WALL, BuildingElement.WINDOW]:
                assert x.target_nr_of_bldgs_to_retrofit == 2
            else:
                x.target_nr_of_bldgs_to_retrofit == 0

    assert 3 == tot_to_retrofit_ac_1977
    assert 1 == tot_retrofitted_ac_1977




