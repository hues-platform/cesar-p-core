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
from typing import Any
from cesarp.model.BuildingModel import BuildingModel
from cesarp.emissons_cost.OperationalEmissionsAndCosts import OperationalEmissionsAndCostsResult
from cesarp.results.EnergyDemandSimulationResults import EnergyDemandSimulationResults
from cesarp.retrofit.RetrofitLog import RetrofitLog
import copy
from cesarp.eplus_adapter.eplus_error_file_handling import EplusErrorLevel


class BldgContainerDefaultEntries:
    BLDG_MODEL_KEY = "bldg_model"
    EPLUS_ERROR_LEVEL = "eplus_error_level"
    SIM_DEMAND_RES_KEY = "eplus_sim_res"
    COST_EMISSON_RES_KEY = "cost_and_emission"
    RETROFIT_LOG = "retrofit_log"
    ERROR = "error"
    CONTAINER_VERSION = "container_version"  # version number introduced with cesar-p V1.2.0


class BuildingContainer:
    """
    Bucket to save all information for a simulated building.
    See set_custom_obj / get_custom_obj to add your project-specific information.
    In case you change the structure, make sure old versions stored to disk can be reloaded by adapting the upgrade_if_necessary() method.
    """

    _RESULT_ENTRY_KEYS = [
        BldgContainerDefaultEntries.SIM_DEMAND_RES_KEY,
        BldgContainerDefaultEntries.COST_EMISSON_RES_KEY,
        BldgContainerDefaultEntries.EPLUS_ERROR_LEVEL,
    ]

    # 2 - container version numbering startet at 2, as there was a container definition without the EPLUS_ERROR_LEVEL entry up to CESAR-P Verison 1.2.0
    # 3 - changed building model to version 1.3 - no released version with container version 2 existst
    # 4 - updated to jsonpickle 2.0.0 which cannot read serialized json objects created with jsonpickle < 2.0.0
    _CONTAINER_VERSION = 4

    def __init__(self):
        self.container = {}
        self.container[BldgContainerDefaultEntries.CONTAINER_VERSION] = self._CONTAINER_VERSION

    def reset_error(self) -> None:
        self.container[BldgContainerDefaultEntries.ERROR] = False

    def set_error(self) -> None:
        self.container[BldgContainerDefaultEntries.ERROR] = True

    def has_error(self) -> bool:
        return self.is_entry_exisiting(BldgContainerDefaultEntries.ERROR)

    def clear_results(self) -> None:
        for RES_KEY in self._RESULT_ENTRY_KEYS:
            self.container[RES_KEY] = None

    def is_entry_exisiting(self, key) -> bool:
        return key in self.container.keys() and self.container[key] is not None

    def has_bldg_model(self) -> bool:
        return self.is_entry_exisiting(BldgContainerDefaultEntries.BLDG_MODEL_KEY)

    def has_retrofit_log(self) -> bool:
        return self.is_entry_exisiting(BldgContainerDefaultEntries.RETROFIT_LOG)

    def has_full_result(self) -> bool:
        return self.has_demand_result() and self.has_op_cost_and_emission_result()

    def has_op_cost_and_emission_result(self) -> bool:
        return self.is_entry_exisiting(BldgContainerDefaultEntries.COST_EMISSON_RES_KEY)

    def has_demand_result(self) -> bool:
        return self.is_entry_exisiting(BldgContainerDefaultEntries.SIM_DEMAND_RES_KEY)

    def set_bldg_model(self, bldg_model: BuildingModel) -> None:
        assert isinstance(
            bldg_model, BuildingModel
        ), "the passed object to be added to the container as a the building model does not have required type cesarp.model.BuildingModel"
        self.container[BldgContainerDefaultEntries.BLDG_MODEL_KEY] = bldg_model

    def get_bldg_model(self) -> BuildingModel:
        return self.container[BldgContainerDefaultEntries.BLDG_MODEL_KEY]

    def set_op_cost_and_emission(self, op_res: OperationalEmissionsAndCostsResult) -> None:
        assert isinstance(op_res, OperationalEmissionsAndCostsResult)
        self.container[BldgContainerDefaultEntries.COST_EMISSON_RES_KEY] = op_res

    def get_op_cost_and_emission(self) -> OperationalEmissionsAndCostsResult:
        return self.container[BldgContainerDefaultEntries.COST_EMISSON_RES_KEY]

    def set_energy_demand_sim_res(self, sim_res: EnergyDemandSimulationResults) -> None:
        assert isinstance(sim_res, EnergyDemandSimulationResults)
        self.container[BldgContainerDefaultEntries.SIM_DEMAND_RES_KEY] = sim_res

    def get_energy_demand_sim_res(self) -> EnergyDemandSimulationResults:
        return self.container[BldgContainerDefaultEntries.SIM_DEMAND_RES_KEY]

    def set_eplus_error_level(self, eplus_err_level: EplusErrorLevel) -> None:
        assert eplus_err_level is None or isinstance(eplus_err_level, EplusErrorLevel)
        self.container[BldgContainerDefaultEntries.EPLUS_ERROR_LEVEL] = eplus_err_level

    def get_eplus_error_level(self) -> EplusErrorLevel:
        return self.container[BldgContainerDefaultEntries.EPLUS_ERROR_LEVEL]

    def set_custom_obj(self, key, obj) -> None:
        """
        For future extensions - keep in mind that when you use SimulationManager.new_manager_from_template(),
        e.g. when using derive_scenario() in ProjectManager, custom entries are currently not copied.
        """
        assert key not in [
            e for e in BldgContainerDefaultEntries.__dict__.values()
        ], f"{key} not accepted as custom key in BuildingContaier becasue it clahes with one of the default keys"
        self.container[key] = obj

    def get_custom_obj(self, key) -> Any:
        return self.container[key]

    def set_retrofit_log(self, retrofit_log: RetrofitLog):
        self.container[BldgContainerDefaultEntries.RETROFIT_LOG] = retrofit_log

    def get_retrofit_log(self):
        return self.container[BldgContainerDefaultEntries.RETROFIT_LOG]

    def shallow_copy(self):
        the_copy = copy.copy(self)
        the_copy.container = copy.copy(self.container)
        return the_copy

    def upgrade_if_necessary(self) -> None:
        """
        Call this function on the container if you want to make sure that container is compatible with latest container definition
        """
        # EPLUS_ERROR_LEVEL entry was added with CESAR-P version 1.2.0 - as version number was introduced with version 1.2.0 this container format change needs to be detected in another way than the version number
        if BldgContainerDefaultEntries.EPLUS_ERROR_LEVEL not in self.container:
            self.set_eplus_error_level(EplusErrorLevel.UNKNOWN)  # set to unknown on upgrade

        if self.has_bldg_model():
            self.get_bldg_model().upgrade_if_necessary()
