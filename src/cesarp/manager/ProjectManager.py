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
import os
import pandas as pd
import logging
import pint
from typing import Callable, Any, Dict, Optional, Sequence, Union
from pathlib import Path

import cesarp.common
from cesarp.manager.SimulationManager import SimulationManager
from cesarp.model.BuildingModel import BuildingModel
import cesarp.eplus_adapter.eplus_sim_runner
from cesarp.manager import _default_config_file


class ProjectManager:
    """
    The ProjectManager organizes multiple simulation runs.
    You can create independent scenario definitions (see create_scenario()) or create a base scenario and derive a new scenario by copying and modifying the base (see derive_scenario()).
    If you have randomization/variability turned on either for the SIA parameters or the constructions, using derive_scenario() will preserve the mapping between the building
    and the random assignment. Using create_scenario() will randomly choose different assignments.
    The scnearios are identified with a name or key. You can use whatever you want, be it a number, a string or an individual Enum type. Only restriction is that it can be converted to a string and used as a folder name.
    Whenever you reference a scenario use those keys specified.
    For each scenario a folder named with the scenario name/key is created under the main project folder.
    It is also possible to load existing scenarios that were previously saved.
    """

    def __init__(
        self,
        base_config: Union[Path, str, Dict[str, Any]],
        project_path: Union[Path, str],
        all_scenarios_summary_filename="all_scenarios_result_summary.csvy",
        fids_to_use=None,
        unit_reg: pint.UnitRegistry = None,
    ):
        """
        :param base_config: path to yml configuration file or dictionary with main configuration entries valid for all scenarios, e.g. EnergyPlus Parameters
        :param project_path: full folder path where the project files should be saved
        :param fids_to_use: optional, if passed only the given fids are simulated. be careful when you save and
                            reload projects with only some of the fids used,that might end up in a mess
        :param unit_reg: if you already instantiated a UnitRegistry in the script or class initializing the
                        ProjectManager, pass that UnitRegistry instance, because the same UnitRegistry must be used in the whole
                        process, otherwise calculations of Quantity objects created with different Registries do not work
        """
        self._fids_to_use = fids_to_use
        if isinstance(base_config, dict):
            self._base_config = base_config
        else:
            self._base_config = cesarp.common.config_loader.load_config_full(base_config)
        self._mgr_config = cesarp.common.config_loader.load_config_for_package(_default_config_file, __package__, self._base_config)
        self.project_path = project_path

        if unit_reg:
            self.ureg = unit_reg
        else:
            self.ureg = cesarp.common.init_unit_registry()

        self._scenarios: Dict[SimulationManager] = {}  # type: ignore
        self.scenario_summary_res: Dict[pd.DataFrame] = {}  # type: ignore
        self.all_scenarios_summary_filepath = self.project_path / Path(all_scenarios_summary_filename)
        self.logger = logging.getLogger(__name__)

    def get_sim_mgr_for(self, sz_name):
        return self._scenarios[sz_name]

    def get_scenario_basepath(self, scenario_name: Any) -> str:
        return self._scenarios[scenario_name].base_output_path

    def create_scenario(self, name, specific_config_path=None) -> None:
        """
        Create a new scenario. In case of variability/random constructions, the assignment is not preserved from another scenario!

        :param name: name/key for the scneario. Has to be convertible to string (str(name)) and this string representation valid as a folder name.
        :param specific_config_path: If you have scenario specific configuration parameters, you can specify the
                                     config file path or a dictionary here.
                                     It overwrites properties of project configuration, if parameters are specified in both of them
        :param fids_to_use: the fid's of the site which are used in this scenario. Building models, IDF's and simulation is only performed for those fid's
        :return: nothing
        """
        sc_config = self._merge_config(specific_config_path)
        sc_path = self.__get_scenario_path_for_name(name)
        assert not os.path.exists(sc_path), f"cannot create new scenario named {name}, folder {sc_path} exists"
        simMgr = SimulationManager(sc_path, sc_config, self.ureg, fids_to_use=self._fids_to_use)
        simMgr.create_bldg_models()
        simMgr.save_bldg_containers()
        simMgr.create_IDFs()
        self._scenarios[name] = simMgr

    def __get_scenario_path_for_name(self, name):
        return self.project_path / Path(str(name))

    def derive_scenario(self, base_scenario_name, new_scenario_name, change_bldg_model_method_ref: Callable[[BuildingModel], Any]) -> None:
        """
        Generate a new scenario based on an existing one. The building models are copied from the base scenario, this means randomly assigned constructions and variable profiles
        are preserved.
        For the so copied building models, the passed method is called, thereafter the IDFs are generated.

        :param base_scenario_name: name of the scenario to be used as a base
        :param new_scenario_name: name for the new scenario
        :param change_bldg_model_method_ref: method to be called for each building model, modifing it's parameters to adapt to the new scenario
        :return: nothing, new scenario is saved
        """

        sc_path = self.__get_scenario_path_for_name(new_scenario_name)
        assert not os.path.exists(sc_path), f"cannot derive new scenario named {new_scenario_name}, folder {sc_path} exists"
        try:
            base = self._scenarios[base_scenario_name]
        except KeyError:
            raise KeyError(f"No existing scenario named {base_scenario_name} found in project manager")

        new_mgr: SimulationManager = SimulationManager.new_manager_from_template(base, sc_path)

        for bldg_container in new_mgr.bldg_containers.values():
            bldg_container.clear_results()
            if bldg_container.has_bldg_model():
                change_bldg_model_method_ref(bldg_container.get_bldg_model())

        new_mgr.save_bldg_containers()
        new_mgr.create_IDFs()
        self._scenarios[new_scenario_name] = new_mgr

    def load_saved_scenario(self, name, specific_config_path=None) -> bool:
        """
        Load existing building models and IDF for the specified scenario.

        :param name: name/key of the scenario (matching folder name from which to load)
        :param specific_config_path: if you have scenario specific configuration parameters, you can specify the config file path here. it overwrites properties of project configuration.
        :return: True if both, Building Models and IDF pathes including weather files mapping could be laoded
        """
        sc_path = self.__get_scenario_path_for_name(name)
        if not os.path.exists(sc_path):
            return False
        sc_config = self._merge_config(specific_config_path)
        simMgr = SimulationManager(sc_path, sc_config, self.ureg, load_from_disk=True)
        if simMgr.is_ready_to_run_sim():
            self._scenarios[name] = simMgr
            return True
        else:
            return False

    def run_not_simulated_scenarios(self) -> None:
        """
        For all defined scenarios, run the E+ simulation if no results folder is present for the scenario

        :param: be careful with passing only a subset of fids here in case some of the scenarios were run for more
                buildings it might result in a mess when trying to create a summary or relaoding etc.
        :return: None
        """
        for name, scenario in self._scenarios.items():
            if not scenario.output_folders:
                scenario.run_simulations()
                scenario.process_results()
                scenario.save_bldg_containers()
                scenario.save_summary_result()

    def collect_all_scenario_summaries(
        self,
        summary_res_columns: Optional[Sequence[str]] = None,
        do_overwrite=False,
        metadata_descr_project_summary="project summary, for detailed metadata see summary results of each scenario.",
    ) -> pd.DataFrame:
        """
        Combines one or several annual results for the different scenarios per building.

        Hint: Check a summary result of one of the scnearios to see available columns for parameter summary_res_columns and units for parameter unit. Which values are reported for
        each szenario further depend on the configuration settings for module cesarp.eplus_adapter. If requested column is not available for all of the scenarios, you will get an exception.

        If results are not available for some buildings for some of the scenarios there will be empty cells.

        :param: summary_res_columns: if None, then all values that are included in the per scenario summary are reported
        :param: do_overwrite: If True, an existing summary file is overwritten; If False, an exception is raised when the summary file already exists.
        :return: summary res as pandas df
        """
        assert do_overwrite or not os.path.exists(self.all_scenarios_summary_filepath), f"summary file already exists {self.all_scenarios_summary_filepath}"
        Path(self.all_scenarios_summary_filepath).unlink(missing_ok=True)  # type: ignore

        result_summaries = {}
        for name, scenario in self._scenarios.items():
            df_res = scenario.get_all_results_summary()
            if summary_res_columns:
                df_res = df_res.loc[:, df_res.columns.get_level_values("var_name").isin(summary_res_columns)]
            result_summaries[name] = df_res
        all_scenario_res = pd.concat(result_summaries.values(), keys=result_summaries.keys(), names=["scenario_name"], axis=1, sort=False)
        all_scenario_res.sort_values(by=["scenario_name", "unit"], axis=1, inplace=True)

        metadata = cesarp.common.DatasetMetadata.DatasetMetadata(
            source="energy plus simulation results",
            description=metadata_descr_project_summary,
        )
        header_data = {cesarp.common.csv_writer._KEY_SOURCE: metadata}
        cesarp.common.csv_writer.write_csv_with_header(header_data, all_scenario_res, self.all_scenarios_summary_filepath)
        self.logger.info(f"project results summary file written to {self.all_scenarios_summary_filepath}")
        return all_scenario_res

    def _merge_config(self, specific_config) -> Dict[str, Any]:
        """
        Merge the scenario specific config with the project config, where the scenario config overwrrites parameters from project config if they are present there.

        :param specific_config:
        :return: merged configruation as dict
        """
        if specific_config:
            if not isinstance(specific_config, dict):
                specific_config = cesarp.common.load_config_full(specific_config)
            scenario_config = cesarp.common.merge_config_recursive(self._base_config, specific_config)
        else:
            scenario_config = self._base_config
        return scenario_config
