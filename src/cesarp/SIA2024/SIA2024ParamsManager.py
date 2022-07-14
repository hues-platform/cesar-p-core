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
import logging
import shutil
from typing import Dict, List, Iterable, Protocol
from pathlib import Path
import random
from enum import Enum
import os

import cesarp.common
from cesarp.SIA2024.SIA2024Parameters import SIA2024Parameters

from cesarp.SIA2024 import _default_config_file
from cesarp.SIA2024.CSVYFileDumper import save_sia_param_set_to_file, read_sia_param_set_from_file


class ParameterFactoryProtocol(Protocol):
    def get_sia2024_parameters(self, bldg_type_key: Enum, variability_active: bool, name: str = None):
        ...

    def is_building_type_residential(self, bldg_type_key):
        ...


class SIA2024ParamsManager:
    """
    Intermediate layer between the SIA2024Facade and SIA2024ParametersFactory handling the caching and persistent storage of the parameter sets.
    The class provides two sets of method, one for nominal profiles and one for variable ones, as the cache is shared between the nominal and variable profiles,
    only nominal or variable profiles can be loaded at the same time.
    """

    def __init__(self, sia2024_params_factory: ParameterFactoryProtocol, ureg=cesarp.common.init_unit_registry(), custom_config=None):
        """
        :param sia2024_params_factory: SIA2024ParametersFactory instance or a NullParameterFactory instance in case parameter generation is not needed or enabled
        :type sia2024_params_factory: ParameterFactoryProtocol
        :param ureg: pass here the unit registry instance of your application, defaults to cesarp.common.init_unit_registry() in case you use the class only for parameter generation
        :type ureg: pint.UnitRegistry, optional
        :param custom_config: dictionary with configuration parameters - make sure to configure SIA data ressources if you want to create new parameter sets, as in the default version those ressources are not included, defaults to {}
        :type custom_config: dict, optional
        """
        self.sia2024_params_factory = sia2024_params_factory
        self.ureg = ureg
        self._cfg = cesarp.common.config_loader.load_config_for_package(_default_config_file, __package__, custom_config)
        self.params_cache: Dict[Enum, List[SIA2024Parameters]] = dict()  # int is param set id
        self._logger = logging.getLogger(__name__)

    def get_param_set(self, bldg_type: Enum):
        try:
            if len(self.params_cache[bldg_type]) == 1:
                return self.params_cache[bldg_type][0]
            else:
                return random.choice(self.params_cache[bldg_type])
        except KeyError:
            raise KeyError(f"for {bldg_type.name} there are no param sets initialized")

    def create_or_load_param_sets_nominal(self, bldg_types: Iterable[Enum]):
        """
        Searches for each building type for profiles in the configured path,
        if none were found and no nominal profiles were loaded previously for this building type a new set of profiles is generated.

        :param bldg_types:  building types for which to load or create profiles
        :return: nothing, profiles loaded into cache
        """
        self.load_param_sets_nominal(bldg_types)
        for bldg_type in bldg_types:
            if bldg_type not in self.params_cache.keys() or not self.params_cache[bldg_type]:
                self.create_and_save_param_sets_nominal([bldg_type])

    def load_param_sets_nominal(self, bldg_types: Iterable[Enum]):
        for bldg_type in bldg_types:
            filepath_pattern = str(self._cfg["PARAMSETS_NOMINAL_SAVE_FOLDER"] / Path(self._cfg["PROFILE_NOMINAL_FILENAME_PATTERN_REL"]))
            filepath = filepath_pattern.format(bldg_type.name)
            try:
                self.params_cache[bldg_type] = [read_sia_param_set_from_file(filepath, self.ureg, self._cfg["CSV_SEPARATOR"])]
                self._logger.info(f"SIAParameters for {bldg_type.name} loaded from {filepath}")
            except FileNotFoundError:
                self._logger.warning(f"SIAParameters for {bldg_type.name} not loaded, file not found {filepath}")

    def create_and_save_param_sets_nominal(self, bldg_types: Iterable[Enum], cleanup_existing_profiles=False):
        save_folder = self._cfg["PARAMSETS_NOMINAL_SAVE_FOLDER"]
        if cleanup_existing_profiles and os.path.exists(save_folder):
            shutil.rmtree(save_folder)
        os.makedirs(save_folder, exist_ok=True)

        for bldg_type in bldg_types:
            filepath_pattern = str(save_folder / Path(self._cfg["PROFILE_NOMINAL_FILENAME_PATTERN_REL"]))
            sia2024NominalParams = self.sia2024_params_factory.get_sia2024_parameters(bldg_type, variability_active=False, name=f"{str(bldg_type.name)}_NOMINAL")
            filepath = filepath_pattern.format(bldg_type.name)
            assert not os.path.exists(filepath), f"Cannot save nominal SIA profile for {bldg_type.name} to {filepath}, file already exists."
            save_sia_param_set_to_file(filepath, sia2024NominalParams, self._cfg["CSV_SEPARATOR"], self._cfg["CSV_FLOAT_FORMAT"])

        # loading again from file, as to pass to energyplus writer we need the profile pointing to a file, and not the newly created siaparams holding profile values as a list...
        self.load_param_sets_nominal(bldg_types)

    def create_or_load_param_sets_variable(self, bldg_types: Iterable[Enum]):
        """
        Searches for each building type for profiles in the configured path,
        if none were found and no nominal profiles were loaded previously for this building type a new set of profiles is generated.

        :param bldg_types:  building types for which to load or create profiles
        :return: nothing, profiles loaded into cache
        """
        self.load_param_sets_variable(bldg_types)
        for bldg_type in bldg_types:
            if bldg_type not in self.params_cache.keys() or not self.params_cache[bldg_type]:
                self.create_and_save_param_sets_variable([bldg_type])

    def load_param_sets_variable(self, bldg_types: Iterable[Enum]):
        """
        Expects profile ID's to be 1...n, without any missing numbers
        :param bldg_types:
        :return:
        """
        for bldg_type in bldg_types:
            filename_pattern = self._cfg["PROFILE_VARIABLE_FILENAME_PATTERN_REL"].format(bldg_type.name, "*")  # filename with wildcard for the id
            self.params_cache[bldg_type] = []
            for path in Path(self._cfg["PARAMSETS_VARIABLE_SAVE_FOLDER"]).glob(filename_pattern):
                self.params_cache[bldg_type].append(read_sia_param_set_from_file(path, self.ureg, self._cfg["CSV_SEPARATOR"]))
            nr_profiles_loaded = len(self.params_cache[bldg_type])
            if nr_profiles_loaded == 0:
                self._logger.warning(
                    f"SIAParameters for {bldg_type.name} with variability could not be loaded, no profiles found in folder {self._cfg['PARAMSETS_VARIABLE_SAVE_FOLDER']}"
                )
            else:
                self._logger.info(f"SIAParameters for {bldg_type.name} loaded, number of variable profiles {nr_profiles_loaded}")

    def create_and_save_param_sets_variable(self, bldg_types: Iterable[Enum], cleanup_existing_profiles=False):
        save_folder = self._cfg["PARAMSETS_VARIABLE_SAVE_FOLDER"]
        if cleanup_existing_profiles and os.path.exists(save_folder):
            shutil.rmtree(save_folder)
        os.makedirs(save_folder, exist_ok=True)

        filepath_pattern = str(save_folder / Path(self._cfg["PROFILE_VARIABLE_FILENAME_PATTERN_REL"]))
        for bldg_type in bldg_types:
            if self.sia2024_params_factory.is_building_type_residential(bldg_type):
                max_nr_param_sets = self._cfg["PROFILE_GENERATION"]["MAX_NR_PARAMSETS_PER_RESIDENTIAL_BLDG_TYPE"]
            else:
                max_nr_param_sets = self._cfg["PROFILE_GENERATION"]["MAX_NR_PARAMSETS_PER_NON_RESIDENTIAL_BLDG_TYPE"]

            for id in range(1, max_nr_param_sets + 1):
                sia_params = self.sia2024_params_factory.get_sia2024_parameters(bldg_type, variability_active=True, name=f"{str(bldg_type.name)}_VAR_{id}")
                filepath = filepath_pattern.format(bldg_type.name, id)
                assert not os.path.exists(filepath), f"Cannot save variable profile for {bldg_type.name} to {filepath}, file already exists."
                save_sia_param_set_to_file(filepath, sia_params, self._cfg["CSV_SEPARATOR"], self._cfg["CSV_FLOAT_FORMAT"])

        # loading again from file, as to pass to energyplus writer we need the profile pointing to a file, and not the newly created siaparams holding profile values as a list...
        self.load_param_sets_variable(bldg_types)
