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
from typing import Dict, Mapping, Optional, List, Any

import cesarp.common
from cesarp.SIA2024 import _default_config_file
from cesarp.model.BuildingOperation import BuildingOperation, Occupancy, InstallationOperation, HVACOperation
from cesarp.model.BuildingOperationMapping import BuildingOperationMapping
from cesarp.SIA2024.SIA2024ParamsManager import SIA2024ParamsManager, ParameterFactoryProtocol
from cesarp.SIA2024.SIA2024ParametersFactory import SIA2024ParametersFactory
from cesarp.SIA2024.NullParametersFactory import NullParameterFactory
from cesarp.SIA2024.SIA2024DataAccessor import SIA2024DataAccessor
from cesarp.SIA2024.SIA2024Parameters import SIA2024Parameters
from cesarp.SIA2024.SIA2024BuildingType import SIA2024BldgTypeKeys
from cesarp.operation.protocols import PassiveCoolingOperationFactoryProtocol


class SIA2024Facade:
    """
    This class provides the main interface to interact with the SIA2024 package.

    Implements the :py:class:`cesarp.manager.manager_protocols.BuildingOperationFactoryProtocol` and thus can be set as "BUILDING_OPERATION_FACTORY_CLASS" in the config of package :py:class:`cesarp.manager`

    The storage location of profiles is handled via configuration. Nominal and variable profiles are stored in separate locations by default in the folder *generated_params* (nominal and variable profiles) of this package.
    As we cannot include the SIA2024 data with the open source release, a set of pre-generated profiles is stored in the folder mentioned.

    To activate profile generation, you must get access to the SIA2024 base data. Contact the Urban Energy Systems Lab for this, as there are some additional input values used. For UES Lab members,
    check out the separate cesar-p-sia2024-data repository. To activte profile generation copy the PROFILE_GENERATION part of the package config to your main configuration file and adapt to your needs,
    especially point to the data file, change the location where to save the profiles (as otherwise your profiles will be overwritten when updating your cesar-p installation) and set the *ACTIVE* switch to *TRUE*.
    With that set up, the profiles will be generated when the destination folder for the profiles is empty or you explicitly call the *generate_all_parameter_sets* with **
    In the configuration you also have many options to control the variability (e.g. variability bands).

    One file is stored per parameter set, which means that single-value parameters are stored in the YAML header and yearly profile values in the following csv part. This file can be directly used
    as an input for EnergyPlus. The profiles returned by the module are represented as `cesarp.common.ScheduleFile`.

    Usage:

    1. create an instance of this class  (passing the mapping between the building ids and their type, if you use the lib to only generate parameters, you can pass an empty list)
    2. call method *load_or_create_parameters*  (passing the building types you want to laod the profiles for, use unique values of the mapping you passed to the init e.g. my_bldg_types.values().unique())
       VARIABILITY: to control whether variable or nominal profiles are used, see configuration parameter *USE_VARIABLE_PARAMSETS*
    3. call *get_building_operation* and/or *get_infiltration_profile*, *get_infiltration_rate* for each building you need the parameters and profiles

    For available building types see :py:class:`cesarp.SIA2024.SIA2024BuildingType.SIA2024BldgTypeKeys`. You have to pass the Enum entries as Strings, e.g. if you have Single family homes and offices, ['SFH', 'OFFICE']

    As this class implements the interface defined in :py:class:`cesarp.manager.manager_protocols.BuildingOperationFactoryProtocol`,
    and the SIA2024 package does not provide the operational parameters for passive cooling, we need a factory instance implementing :py:class:`cesarp.operation.protocolsPassiveCoolingOperationFactoryProtocol`
    to query for those parameters to be able to fulfill this interface/protocol. As this interface further requires that the query methods get_xxx take only the building fid as a parameter, we pass the mapping
    between the building fid and its type to the construction. (the reason for this implementation is that in case another implemntation needs another or additional attribute, e.g. building age,
    the interface will be unchanged, but only the parameters you would pass to the constructor of that method change, which means only in one location where the class is initialized a special handling must
    be implemented but not at each place where an instance of the interface/protocol is used)

    If you need greater control over the parameter generation than provided by this facade and the configuration parameters, you can use the :py:class:`cesarp.SIA2024.SIA2024ParameterFactory` to create
    SIA parameter sets. The factory just creates in-memory objects, so if you need to e.g. store the profiles to disk you can get some inspiration from :py:class:`cesarp.SIA2024.SIA2024ParameterManager`.
    """

    def __init__(
        self,
        bldg_fid_bldg_type_lookup: Mapping[int, str],
        passive_cooling_op_fact: PassiveCoolingOperationFactoryProtocol,
        ureg: pint.UnitRegistry,
        custom_config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialization of the facade.

        :param bldg_fid_bldg_type_lookup: dictionary defining the building type (as a string) of each building.
        :type bldg_fid_bldg_type_lookup: Mapping[int, str]
        :param passive_cooling_op_fact: the properties for passive cooling are not implemented withing SIA2024. As this interface class provides the full operational parameter set, we use this factory instance to genertate the passive cooling specific parameters.
        :type passive_cooling_op_fact: PassiveCoolingOperationFactoryProtocol
        :param ureg: instance of pint unit registry
        :type ureg: pint.UnitRegistry
        :param custom_config: dict with custom configuration entries
        :type custom_config: Dict[str, Any], optional
        """
        if custom_config is None:
            custom_config = {}
        self.bldg_fid_params_lookup: Dict[int, SIA2024Parameters] = dict()
        self._cfg = cesarp.common.load_config_for_package(_default_config_file, __package__, custom_config)
        # Initialize params manager with or without possibility to generate parameter sets. Option necessary, as SIA2024 base data needed to generate profiles is not
        # distributed with CESAR-P. SIA2024 data is licensed and stored in a separate python package.
        self.params_manager = SIA2024Facade.__create_params_manager(ureg, custom_config, with_parameter_generation=self._cfg["PROFILE_GENERATION"]["ACTIVE"])
        self.bldg_fid_bldg_type_lookup: Dict[int, SIA2024BldgTypeKeys] = self.__convert_dict_entries_to_bldg_type_enum(bldg_fid_bldg_type_lookup)
        self._passive_cooling_op_fact = passive_cooling_op_fact

    @staticmethod
    def __create_params_manager(ureg, custom_config: Optional[Dict[str, Any]], with_parameter_generation=True):
        if with_parameter_generation:
            sia_base_data = SIA2024DataAccessor(ureg, custom_config)
            params_factory: ParameterFactoryProtocol = SIA2024ParametersFactory(sia_base_data, ureg, custom_config)
        else:
            params_factory = NullParameterFactory()
        return SIA2024ParamsManager(params_factory, ureg, custom_config)

    @staticmethod
    def generate_all_parameter_sets(custom_config=None, cleanup_existing_profiles=True):
        params_mgr = SIA2024Facade.__create_params_manager(ureg=cesarp.common.init_unit_registry(), custom_config=custom_config)
        all_bldg_types = list(SIA2024BldgTypeKeys)
        params_mgr.create_and_save_param_sets_nominal(all_bldg_types, cleanup_existing_profiles)
        params_mgr.create_and_save_param_sets_variable(all_bldg_types, cleanup_existing_profiles)

    def load_or_create_parameters(self, bldg_types: List[str], variability_active: Optional[bool] = None):
        """
        Load parameter sets from disk or create a new parameter set if loading is not possible.
        Raises CesarpException if a parameter set cannot be loaded and parameter generation is not acitve (see initialization)
        Folder location is defined in the configuration (different location for variable and nominal profiles)

        :param bldg_types: list of building types (as string) for which to load parameters.
        :param variability_active: if true, variable profiles are loaded, if false nominal ones; optional, if not provided value form config is used.
        :return: nothing, parameters are loaded and ready for request by the get_xxx methods.
        """
        bldg_types = self.__convert_list_entries_to_bldg_type_enum(bldg_types)

        if variability_active is None:
            variability_active = self._cfg["USE_VARIABLE_PARAMSETS"]

        if variability_active:
            self.params_manager.create_or_load_param_sets_variable(bldg_types)
        else:
            self.params_manager.create_or_load_param_sets_nominal(bldg_types)

    def get_building_operation(self, bldg_fid: int, nr_of_floors) -> BuildingOperationMapping:
        """
        Request the building operation parameters for the given building fid.
        For all floors the same operational data is assigned.
        The method complies with the cesarp.manager.manager_protocols.BuildingOperationFactoryProtocol
        The parameters returned match the building type of the building according to the lookup table provided during initialization.
        Whether nominal or variable profiles are returned depends on the loaded parameters (see load_or_create_parameters).
        In case of variability, one of the available parameter sets for that building type is chosen randomly and cached on the first request for a certain building fid.
        Thus, repeated calls to this method or any other get_xxx method of this class return values from the same variable parameter set for a given building id.

        :param bldg_fid: id of building for which to get parameters
        :return: BuildingOperation object populated with data based on SIA2024
        """
        try:
            params = self.bldg_fid_params_lookup[bldg_fid]
        except KeyError:
            params = self.__assign_params_for_bldg(bldg_fid)

        bldg_op = BuildingOperation(
            params.name,
            Occupancy(params.floor_area_per_person, params.occupancy_fraction_schedule, params.activity_schedule),
            InstallationOperation(params.electric_appliances_fraction_schedule, params.electric_appliances_power_demand),
            InstallationOperation(params.lighting_fraction_schedule, params.lighting_power_demand),
            InstallationOperation(params.dhw_fraction_schedule, params.dhw_power_demand),
            HVACOperation(params.heating_setpoint_schedule, params.cooling_setpoint_schedule, params.ventilation_fraction_schedule, params.ventilation_outdoor_air_flow),
            self._passive_cooling_op_fact.create_night_vent(bldg_fid, params.cooling_setpoint_schedule),
            self._passive_cooling_op_fact.create_win_shading_ctrl(bldg_fid),
        )
        bldg_op_mapping = BuildingOperationMapping()
        bldg_op_mapping.add_operation_assignment_all_floors(nr_of_floors, bldg_op)
        return bldg_op_mapping

    def get_infiltration_profile(self, bldg_fid):
        """
        Request the infiltration profile for a given building fid.
        Currently there is no variability or building type specific variation for the infiltration profile, thus this method will always return a fraction profile with value 1 for all hours of the year.

        :param bldg_fid: id of building for which to get parameters
        :return: yearly fraction profile for infiltration
        """
        try:
            return self.bldg_fid_params_lookup[bldg_fid].infiltration_fraction_schedule
        except KeyError:
            return self.__assign_params_for_bldg().infiltration_fraction_schedule

    def get_infiltration_rate(self, bldg_fid) -> pint.Quantity:
        """
        Request the infiltration rate for the given building fid.
        The infiltration rate returned matches the building type of the building according to the lookup table provided during initialization.
        Whether nominal or variable infiltration rate is returned depends on the loaded parameters (see generate_new_parameters and load_parameters).
        In case of variability, one of the available parameter sets for that building type is chosen randomly and cached on the first request for a certain building fid.
        Thus, repeated calls to this method or any other get_xxx method of this class return values from the same variable parameter set for a given building id.

        :param bldg_fid: id of building for which to get parameters
        :return: infiltration rate
        """
        try:
            return self.bldg_fid_params_lookup[bldg_fid].infiltration_rate
        except KeyError:
            return self.__assign_params_for_bldg(bldg_fid).infiltration_rate

    def __assign_params_for_bldg(self, bldg_fid: int) -> SIA2024Parameters:
        bldg_type = self.bldg_fid_bldg_type_lookup[bldg_fid]
        self.bldg_fid_params_lookup[bldg_fid] = self.params_manager.get_param_set(bldg_type)
        return self.bldg_fid_params_lookup[bldg_fid]

    def __convert_list_entries_to_bldg_type_enum(self, bldg_types):
        return [SIA2024BldgTypeKeys[bldg_type] if isinstance(bldg_type, str) else bldg_type for bldg_type in bldg_types]

    def __convert_dict_entries_to_bldg_type_enum(self, dict_with_bldg_type_entries):
        return {bldg_fid: (SIA2024BldgTypeKeys[bldg_type] if isinstance(bldg_type, str) else bldg_type) for bldg_fid, bldg_type in dict_with_bldg_type_entries.items()}
