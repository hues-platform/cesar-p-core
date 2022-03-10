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
import pint
import pandas as pd
from typing import List, Union, Dict, Any
from pathlib import Path
from cesarp.retrofit.BuildingElementsRetrofitter import BuildingElementsRetrofitter
from cesarp.model.BuildingElement import BuildingElement
from cesarp.model.BuildingModel import BuildingModel
from cesarp.manager.ProjectManager import ProjectManager

RETROFIT_LOG_NAME = "retrofit_log.csv"


class SimpleRetrofitManager:
    """
    Manager class, based on ProjectManager, to simulate a base scenario and any number of retrofit cases.
    For the retrofit cases, you can define which building elements shall be retrofitted. The retrofit is
    applied to all buildings on your site.

    1. Initialize the class
    2. Add retrofit scenarios with add_retrofit_case
    3. Run simulations with run_simulations
    """

    def __init__(
        self,
        ureg: pint.Quantity,
        base_config: Union[Path, str, Dict[str, Any]],
        base_scenario_name: str,
        project_path: Union[Path, str],
        year_of_retrofit: int = 2020,
        fids_to_use: List[int] = None,
    ):
        """Initialisation of manager

        :param ureg: unit registry instance
        :type ureg: pint.Quantity
        :param base_config: main/custom config for all scenarios, either path to the yml file or config already parsed as dictionary
        :type base_config: Union[Path, str, Dict[str, Any]]
        :param base_scenario_name: name of the base scenario (without retrofit)
        :type base_scenario_name: str
        :param project_path: full path to folder in which to store outputs for the different scenarios. a subfolder will be created per scenario (name: scenario name)
        :type project_path: Union[Path, str]
        :param year_of_retrofit: year of retrofit measure, in this implementation just for logging, does not influence embodied cost and emissions for retrofit measures, defaults to 2020
        :type year_of_retrofit: int, optional
        :param fids_to_use: if you want to use only part of your buildings, None if all should be used, defaults to None
        :type fids_to_use: List[int], optional
        """
        self.bldg_constr_retrofitter = BuildingElementsRetrofitter(ureg=ureg)
        self.bldg_constr_retrofitter.set_year_of_retrofit(year_of_retrofit)
        self._proj_mgr = ProjectManager(base_config, project_path, fids_to_use=fids_to_use, unit_reg=ureg)
        self._base_scenario = base_scenario_name
        if not self._proj_mgr.load_saved_scenario(base_scenario_name):
            self._proj_mgr.create_scenario(base_scenario_name)

    def run_simulations(self) -> pd.DataFrame:
        """
        Run the simulations for the base case and all scenarios.
        If results are already existing for base case or a scenario it is not re-run.

        :return: dataframe with annual results for base case and all the scenarios
        :rtype: pd.DataFrame
        """
        self._proj_mgr.run_not_simulated_scenarios()
        return self._proj_mgr.collect_all_scenario_summaries()

    def add_retrofit_case(self, scenario_name: str, bldg_elems_to_retrofit: List[BuildingElement]) -> Dict[str, pint.Quantity]:
        """
        Add a retrofit scenario.
        The detailed log about retrofit measures is written to disk in the scenario folder.

        :param szenario_name: name of the scenario, used as folder name
        :type szenario_name: str
        :param bldg_elems_to_retrofit: which parts of the building construction shall be retrofitted. see :py:class:`BuildingElementsRetrofitter` for retrofittable elements.
        :type bldg_elems_to_retrofit: List[BuildingElement]
        :return: pandas dataseries (dict-like), with entries "costs", "co2_emission", "non_renewable_pen", which are the sum over all retrofit measures for all building
        :rtype: Dict[str, pint.Quantity]
        """
        assert self._base_scenario, "no base scenario. add with add_base_case(scenario_name)"
        self.bldg_constr_retrofitter.set_bldg_elems_to_retrofit(bldg_elems_to_retrofit)
        self._proj_mgr.derive_scenario(self._base_scenario, scenario_name, self._apply_retrofit)
        self.bldg_constr_retrofitter.save_retrofit_log(str(self._proj_mgr.get_scenario_basepath(scenario_name) / Path(RETROFIT_LOG_NAME)))
        ret_sum_costs_emissions = self.bldg_constr_retrofitter.retrofit_log.get_sum_of_costs_and_emissions()
        # if you need any other special evaluation, the best is that you implement your own retrofit manager class like this one
        # and you postprocess the log as you need here - because the log is reset in the next step, if we would return it to the caller we
        # would need to do a deepcopy of it. the other possibility is that you reload the retrofit logs written to disk and postprocess them
        self.bldg_constr_retrofitter.reset_retrofit_log()
        return ret_sum_costs_emissions

    def _apply_retrofit(self, bldg_model: BuildingModel):
        self.bldg_constr_retrofitter.retrofit_bldg_construction(bldg_model.fid, bldg_model.bldg_construction, bldg_model.bldg_shape)
