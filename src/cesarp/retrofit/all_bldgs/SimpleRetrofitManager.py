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
    def __init__(
        self, ureg: pint.Quantity, base_config: Union[str, Dict[str, Any]], base_scenario_name: str, base_project_path: str, year_of_retrofit=2020, fids_to_use=None,
    ):
        self.bldg_constr_retrofitter = BuildingElementsRetrofitter(ureg=ureg)
        self.bldg_constr_retrofitter.set_year_of_retrofit(year_of_retrofit)
        self._proj_mgr = ProjectManager(base_config, base_project_path, fids_to_use=fids_to_use, unit_reg=ureg)
        self._base_scenario = base_scenario_name
        if not self._proj_mgr.load_saved_scenario(base_scenario_name):
            self._proj_mgr.create_scenario(base_scenario_name)

    def run_simulations(self):
        self._proj_mgr.run_not_simulated_scenarios()
        return self._proj_mgr.collect_all_scenario_summaries()

    def add_retrofit_case(self, szenario_name: str, bldg_elems_to_retrofit: List[BuildingElement]) -> pd.DataFrame:
        assert self._base_scenario, "no base scenario. add with add_base_case(scenario_name)"
        self.bldg_constr_retrofitter.set_bldg_elems_to_retrofit(bldg_elems_to_retrofit)
        self._proj_mgr.derive_scenario(self._base_scenario, szenario_name, self._apply_retrofit)
        self.bldg_constr_retrofitter.save_retrofit_log(str(self._proj_mgr.get_scenario_basepath(szenario_name) / Path(RETROFIT_LOG_NAME)))
        ret_log = self.bldg_constr_retrofitter.get_retrofit_log_as_df()
        self.bldg_constr_retrofitter.reset_retrofit_log()
        return ret_log

    def _apply_retrofit(self, bldg_model: BuildingModel):
        self.bldg_constr_retrofitter.retrofit_bldg_construction(bldg_model.fid, bldg_model.bldg_construction, bldg_model.bldg_shape)
