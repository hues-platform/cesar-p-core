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
from pathlib import Path
from typing import Dict

import cesarp.common
from cesarp.retrofit.energy_perspective_2050.EnergyPerspective2050BldgElementsRetrofitter import EnergyPerspective2050BldgElementsRetrofitter
from cesarp.retrofit.RetrofitLog import RetrofitLog
from cesarp.model.BuildingModel import BuildingModel
from cesarp.manager.ProjectManager import ProjectManager

RETROFIT_LOG_NAME = "retrofit_log_all_periods.csv"


class EnergyPerspective2050RetrofitManager:
    """
    Seqencer for energy perspective 2050 retrofit.
    Initializes a base case and according to the time periods defined in cesarp.energy_strategy a number of subsequent
    scenarios, each building up on the previous one.
    For details on retrofit strategy see :py:class`cesarp.retrofit.energy_perspective_2050.EnergyPerspective2050BldgElementsRetrofitter`

    1. Initialize class
    2. Call run() on your instance
    """

    def __init__(
        self,
        ureg: pint.Quantity,
        base_config_path: str,
        project_base_path: str,
        weather_per_period: Dict[int, str],
        fids_to_use=None,
    ):
        """
        :param ureg: pint unit registry instance
        :param base_config_path: path to custom/main configuration file, used for base scenario and all retrofit periods
                                 configuration for weather file is ignored, see param weather_per_period
        :param project_base_path: path to folder where the simulation scenarios should be saved
        :param weather_per_period: dictionary with mapping of retrofit period to weather file. keys must match
                retrofit periods used in EnergyPerspective2050BldgElementsRetrofitter (which correspont to
                cesarp.energy_strategy config TIME_PERIODS.
                Those weather files OVERRIDE the weather file specified in the configuration!
        :param fids_to_use: optional, if passed only the given fid's are simulated
        """
        self._proj_base_path = project_base_path
        self._proj_mgr = ProjectManager(base_config_path, project_base_path, fids_to_use=fids_to_use, unit_reg=ureg)
        base_config = cesarp.common.load_config_full(base_config_path)
        self._retrofitter = EnergyPerspective2050BldgElementsRetrofitter(ureg, base_config)
        assert list(weather_per_period.keys()) == self._retrofitter.get_retrofit_periods(), (
            f"periods used in weather file list {list(weather_per_period.keys())} do not match the ones of the "
            f"retrofitter, which are {self._retrofitter.get_retrofit_periods()}"
        )
        self._weather_per_period: Dict[int, str] = weather_per_period
        self._current_sim_period_year: int = None  # type: ignore

    def run(self) -> pd.DataFrame:
        """
        Do run the project with retrofitting.
        It does create the retrofit scenarios for each of retrofit periods you passed in the weather files dictionary in the initilization.

        :return: annual results for all retrofit scenarios.
        :rtype: pd.DataFrame
        """
        retrofit_period_years = self._retrofitter.get_retrofit_periods()

        # create base scenario
        self._current_sim_period_year = retrofit_period_years[0]
        base_weather_file = self._weather_per_period[self._current_sim_period_year]
        base_scenario_config = {
            "MANAGER": {"SINGLE_SITE": {"ACTIVE": True, "WEATHER_FILE": base_weather_file}, "SITE_PER_CH_COMMUNITY": {"ACTIVE": False}},
            "SITE": {"SIMULATION_YEAR": self._current_sim_period_year},
        }
        self._proj_mgr.create_scenario(str(self._current_sim_period_year), base_scenario_config)
        prev_sz_name = str(self._current_sim_period_year)
        for bldg_c in self._proj_mgr.get_sim_mgr_for(prev_sz_name).bldg_containers.values():
            # initialize empty retrofit logs because in retrofit method log is uesed to lookup for previous retrofits...
            bldg_c.set_retrofit_log(RetrofitLog())

        # retrofit needs energy demand from previous simulation to calculate emissions, thus run simulation for
        # before going to the next retrofit period
        self._proj_mgr.run_not_simulated_scenarios()
        # create and run scenario for each retrofit period
        for sim_year in retrofit_period_years[1:]:
            sz_name = str(sim_year)
            self._current_sim_period_year = sim_year
            self._proj_mgr.derive_scenario(prev_sz_name, sz_name, self._change_sim_year_for_model)
            self._retrofitter.retrofit_site(
                sim_year,
                self._proj_mgr.get_sim_mgr_for(sz_name).bldg_containers,
                self._proj_mgr.get_sim_mgr_for(prev_sz_name).bldg_containers,
            )
            self._proj_mgr.run_not_simulated_scenarios()
            prev_sz_name = sz_name

        self._retrofitter.get_retrofit_log().save(str(self._proj_base_path / Path(RETROFIT_LOG_NAME)))
        return self._proj_mgr.collect_all_scenario_summaries(
            metadata_descr_project_summary=f"Retrofit sceanarios created with {__name__}. Simulation year and weather defined in configuarion is not used! "
            f"following weather files were used: {self._weather_per_period}. For other "
            f"details please have a look in the metadata of each simulation period"
        )

    def _change_sim_year_for_model(self, bldg_model: BuildingModel):
        bldg_model.site.simulation_year = self._current_sim_period_year  # type: ignore
        bldg_model.site.weather_file_path = self._weather_per_period[self._current_sim_period_year]
