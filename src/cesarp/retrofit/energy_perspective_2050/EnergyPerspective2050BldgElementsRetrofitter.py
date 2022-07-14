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
from typing import Dict, Any, List, Iterable, Optional
import logging
import pint
from dataclasses import dataclass

import cesarp.common
from cesarp.common.AgeClass import AgeClass
from cesarp.manager.BuildingContainer import BuildingContainer
from cesarp.model.EnergySource import EnergySource
from cesarp.model.BldgType import BldgType
from cesarp.model.BuildingElement import BuildingElement
from cesarp.model.BuildingModel import BuildingModel
from cesarp.results.EnergyDemandSimulationResults import EnergyDemandSimulationResults
from cesarp.emissons_cost.OperationalEmissionsAndCosts import OperationalEmissionsAndCosts
from cesarp.energy_strategy.RetrofitRates import RetrofitRates

from cesarp.retrofit.RetrofitLog import RetrofitLog
from cesarp.retrofit.energy_perspective_2050.EnergyTargetLookup import EnergyTargetLookup
from cesarp.retrofit.BuildingElementsRetrofitter import BuildingElementsRetrofitter
from cesarp.retrofit.energy_perspective_2050 import _default_config_file


@dataclass
class RetrofitCategoryDetails:
    """
    Little helper class to specify the parameters of a certain retrofit bucket or category.
    Used to keep track of the number of buildings that should get a retrofit, how many were retrofitted and
    """

    bldg_type: BldgType
    constr_ac: AgeClass
    bldg_elems_to_retrofit: List[BuildingElement]
    target_nr_of_bldgs_to_retrofit: int
    nr_of_bldgs_retrofitted: int = 0

    def is_target_nr_of_bldgs_reached(self) -> bool:
        return self.target_nr_of_bldgs_to_retrofit <= self.nr_of_bldgs_retrofitted

    def increment_retrofitted_cnt(self):
        self.nr_of_bldgs_retrofitted += 1


class EnergyPerspective2050BldgElementsRetrofitter:
    """
    Implements constructional retrofit as outlined in the Master Thesis of Jonas Landolt.
    For Details about the retrofit strategy please check chapter 5.1.6 in CESAR-Tool_Documentation.pdf

    This class contains the logic to select the buildings for which a retrofit measure should be applied and in case
    partial retrofit is activated (configuration parameter DO_PARTIAL_RETROFIT) also which building elements shall be retrofitted,
    e.g. only Roof and Wall or Windows only. In case partial retrofit is not on, all buildings which get a retrofit
    are fully retrofitted, meaning Roof, Wall, Window, Groundfloor are retrofitted.
    To carry out the retrofits the cesarp.retrofit.BuildingElementsRetrofitter is used.

    Retrofit strategy only applied so far for residential buildings!
    Emission and costs for retrofit can only be calculated for rectangualr footprint shapes, as the area of the groundfloor and
    roof area are required and calculating the area of polygon area is not yet implemented (e.g. one could use shaply or another lib to do that).
    In case of non-rectangular footprint shape, retrofit emission and costs for roof and groundfloor are set to None in RetrofitLog

    The percentages of full and partial retrofit depending on building age and retrofit year/period are configurable
    through input files and are located in the cesarp.energy_strategy, as they relate to the energy strategy.

    Taking any retrofit shares that could not be "fulfilled" in one retrofit period to the next is not yet implemented,
    but was in the Matlab version. See gitlab Issue #109.

    If the site does not have buildings for a certain building type and age class used in the retrofit rate definition,
    that retrofit rate get's ignored. For example, if the site defines no single family home (SFH) buildings with
    year_of_construction in the range of 2001-2005, the assigned retrofit rates for age class 2001-2005 are ignored.
    """

    def __init__(self, ureg: pint.UnitRegistry, custom_config: Optional[Dict[str, Any]] = None):
        """
        :param ureg:
        :param year_of_retrofit: must match one of cesarp.energy_strategy config "TIME_PERIODS"
        :param custom_config:
        """
        self._cfg = cesarp.common.load_config_for_package(_default_config_file, __package__, custom_config)
        self._op_emissions_calculator = OperationalEmissionsAndCosts(ureg, custom_config)
        self._energy_target = EnergyTargetLookup(self._cfg["ENERGY_TARGETS_LOOKUP_FILE"], ureg)
        self._supported_bldg_types = [BldgType.MFH, BldgType.SFH]
        self._retrofit_rates_accessor: RetrofitRates = RetrofitRates(custom_config)
        self._per_elem_construction_retrofitter = BuildingElementsRetrofitter(ureg)
        self._retrofit_categories_last_run: Optional[Dict[BldgType, List[RetrofitCategoryDetails]]] = None
        self._all_buildings_retrofit_log: RetrofitLog = RetrofitLog()
        self._logger = logging.getLogger(__name__)

    def retrofit_site(
        self,
        year_of_retrofit: int,
        bldg_containers_current: Dict[int, BuildingContainer],
        bldg_containers_prev_period: Dict[int, BuildingContainer],
    ) -> RetrofitLog:
        """
        Retrofit building construction.
        Buildings meeting one of the following criteria do not get retrofitted:
        - Operational Emissions below target
        - Building got retrofitted

        As for the operational emissions calculation, dhw and heating energy carrier from current building model are
        used, make sure that if your retrofit strategy involves system retrofit to perform the system retrofit before
        calling this method.

        :param bldg_containers_current: dictionary with key fid, value the building container of the bldg for the
                                        current retrofit period, no simulation results expected
        :param bldg_containers_prev_period: dictionary with key fid, value the building container of the bldg for the
                                            previos retrofit period, should include simulation results and retrofit log
        :return: retrofit log for including retrofit measures for all buildings
        """
        retrofit_categories_by_bt = self._define_nr_of_bldgs_to_retrofit(year_of_retrofit, bldg_containers_current.values())

        self._all_buildings_retrofit_log = RetrofitLog()

        self._per_elem_construction_retrofitter.set_year_of_retrofit(year_of_retrofit)

        for fid, container_current in bldg_containers_current.items():
            self._per_elem_construction_retrofitter.reset_retrofit_log()
            model_current = container_current.get_bldg_model()

            if (
                model_current.bldg_construction.installation_characteristics.e_carrier_dhw is not None
                and model_current.bldg_construction.installation_characteristics.e_carrier_heating is not None
            ):
                container_prev_sim = bldg_containers_prev_period[fid]

                energy_demand_last_period = container_prev_sim.get_energy_demand_sim_res()
                emission_target_reached = self._check_emissions_below_target(
                    energy_demand_last_period,
                    model_current.bldg_construction.installation_characteristics.e_carrier_dhw,
                    model_current.bldg_construction.installation_characteristics.e_carrier_heating,
                    model_current.site.simulation_year,
                )
                retrofitted_in_last_period = self._check_retrofitted_in_last_period(container_prev_sim.get_bldg_model().site.simulation_year, container_prev_sim.get_retrofit_log())

                if not emission_target_reached and not retrofitted_in_last_period:
                    for ret_category in retrofit_categories_by_bt[model_current.bldg_type]:
                        if ret_category.constr_ac.isInClass(model_current.year_of_construction):
                            if not ret_category.is_target_nr_of_bldgs_reached():
                                self._do_retrofit(model_current, ret_category.bldg_elems_to_retrofit)
                                ret_category.increment_retrofitted_cnt()
                                break

                if container_current.has_retrofit_log():
                    container_current.get_retrofit_log().append_log(self._per_elem_construction_retrofitter.retrofit_log)
                else:
                    container_current.set_retrofit_log(self._per_elem_construction_retrofitter.retrofit_log)

                self._all_buildings_retrofit_log.append_log(self._per_elem_construction_retrofitter.retrofit_log)
            else:
                self._logger.warn(f"energy carrier for DHW and Heating not available for {fid}, thus that building was NOT considered for retrofit")

        return self._all_buildings_retrofit_log

    def get_retrofit_periods(self):
        return self._retrofit_rates_accessor.time_periods

    def get_retrofit_log(self):
        return self._all_buildings_retrofit_log

    def reset_retrofit_log(self):
        return self._per_elem_construction_retrofitter.reset_retrofit_log()

    def _define_nr_of_bldgs_to_retrofit(self, year_of_retrofit: int, bldg_containers: Iterable[BuildingContainer]) -> Dict[BldgType, List[RetrofitCategoryDetails]]:
        """
        :param year_of_retrofit: year of this retrofit period
        :param nr_of_bldgs_on_site:
        :return: Dict[Building Type, Dict[Construction Age Bucket, List[Tuple(List[Building Elements to Retrofit], nr of bldgs to retrofit, nr of bldgs retrofitted)]]]
                Building Type: one of the self._supported_bldg_tpyes
                Construction Age Bucket: age classes as used for the retrofit rate definition in cesarp.energy_strategy.RetrofitRates.
                                                Note: do not match with age class used for constructional archetypes
                Building Elements to Retrofit: Building elements to be retrofitted, for full retrofit this
                                                includes all building elements, thus only one Tuple will be
                                                in the List. If partial retrofit is active, the list may
                                                contain up to 15 entries, for each possible combination of building elements.
                nr of bldgs to retrofit: number of buildings, according to retrofit rate and total buildings of that
                                            type and with it's construction year in the age class, that should get a
                                            retrofit for the listed building elements
                nr of bldgs retrofitte: always 0 when returned by this function, can be used to track how many
                                        buildings got that retrofit measure
        """
        retrofit_categories_by_bt = {}
        age_classes_used_for_ret_rates = self._retrofit_rates_accessor.get_retrofit_rates_age_classes()
        nr_of_bldgs_on_site = self._get_nr_of_bldg_per_bldg_type_and_ac(bldg_containers, age_classes_used_for_ret_rates)
        for bt in self._supported_bldg_types:
            if self._cfg["DO_PARTIAL_RETROFIT"]:
                partial_retrofit_rates = self._retrofit_rates_accessor.get_partial_retrofit_rates_per_age_class(sim_year=year_of_retrofit, bldg_type=bt)
                ret_cats = []
                for ac, rate_per_bldg_elems in partial_retrofit_rates.items():
                    for (bldg_elems, ret_rate) in rate_per_bldg_elems:
                        target_num_bldgs = int(round(ret_rate * nr_of_bldgs_on_site[bt][ac], ndigits=0))
                        ret_cats.append(
                            RetrofitCategoryDetails(
                                bldg_type=bt,
                                constr_ac=ac,
                                bldg_elems_to_retrofit=bldg_elems,
                                target_nr_of_bldgs_to_retrofit=target_num_bldgs,
                            )
                        )
                retrofit_categories_by_bt[bt] = ret_cats

            else:
                retrofit_rates = self._retrofit_rates_accessor.get_full_retrofit_rate_per_age_class(sim_year=year_of_retrofit, bldg_type=bt)
                full_retrofit_elems = [
                    BuildingElement.ROOF,
                    BuildingElement.WINDOW,
                    BuildingElement.WALL,
                    BuildingElement.GROUNDFLOOR,
                ]
                ret_per_ac = []
                for ac, ret_rate in retrofit_rates.items():
                    target_num_bldgs = int(round(ret_rate * nr_of_bldgs_on_site[bt][ac], ndigits=0))
                    ret_per_ac.append(
                        RetrofitCategoryDetails(
                            bldg_type=bt,
                            constr_ac=ac,
                            bldg_elems_to_retrofit=full_retrofit_elems,
                            target_nr_of_bldgs_to_retrofit=target_num_bldgs,
                        )
                    )
                retrofit_categories_by_bt[bt] = ret_per_ac
        self._retrofit_categories_last_run = retrofit_categories_by_bt
        return retrofit_categories_by_bt

    def _get_nr_of_bldg_per_bldg_type_and_ac(self, bldg_containers: Iterable[BuildingContainer], age_buckets: List[AgeClass]) -> Dict[BldgType, Dict[AgeClass, int]]:

        nr_of_bldgs = {bt: {ac: 0 for ac in age_buckets} for bt in self._supported_bldg_types}
        for bldg_c in bldg_containers:
            model = bldg_c.get_bldg_model()
            for bucket in age_buckets:
                if bucket.isInClass(model.year_of_construction):
                    if model.bldg_type not in self._supported_bldg_types:
                        raise Exception(f"{__file__} does not support bldg type {model.bldg_type} of bldg fid {model.fid}")
                    nr_of_bldgs[model.bldg_type][bucket] += 1
                    break

        return nr_of_bldgs

    def _do_retrofit(self, model: BuildingModel, elems_to_retrofit: List[BuildingElement]) -> None:
        self._per_elem_construction_retrofitter.set_bldg_elems_to_retrofit(elems_to_retrofit)
        self._per_elem_construction_retrofitter.retrofit_bldg_construction(model.fid, model.bldg_construction, model.bldg_shape)

    def _check_emissions_below_target(
        self,
        energy_demand: EnergyDemandSimulationResults,
        dhw_carrier: EnergySource,
        heating_carrier: EnergySource,
        year_for_emission_calc,
    ):
        """
        Returns True if operational costs and emissions are below the required SIA target
        Translated from Matlab CESAR script constret_decision.m
        """
        op_emissions_costs = self._op_emissions_calculator.get_operational_emissions_and_costs(
            specific_dhw_demand=energy_demand.specific_dhw_demand,
            total_dhw_demand=energy_demand.tot_dhw_demand,
            dhw_carrier=dhw_carrier,
            specific_heating_demand=energy_demand.specific_heating_demand,
            total_heating_demand=energy_demand.tot_dhw_demand,
            heating_carrier=heating_carrier,
            specific_electricity_demand=energy_demand.specific_electricity_demand,
            total_electricity_demand=energy_demand.tot_electricity_demand,
            sim_year=year_for_emission_calc,
        )
        bldg_op_pen = op_emissions_costs.total_pen.to(self._energy_target.pen_unit)
        bldg_op_co2 = op_emissions_costs.total_co2_emission.to(self._energy_target.co2_unit)
        if bldg_op_pen.m <= self._energy_target.get_resi_op_pen_target(new_bldg=False).m and bldg_op_co2.m <= self._energy_target.get_resi_op_co2_target(new_bldg=False).m:
            return True
        return False

    def _check_retrofitted_in_last_period(self, last_period_year: int, last_sim_retrofit: RetrofitLog):
        # TODO should it really only look at the last year? (see issue 109 on gitlab)
        return last_sim_retrofit.was_construction_retrofitted_in(last_period_year)
