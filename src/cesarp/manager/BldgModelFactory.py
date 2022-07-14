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
from typing import Optional, Dict, Union, Any
from pathlib import Path
import pandas as pd
import pint
import logging

import cesarp.common
import cesarp.geometry.csv_input_parser

try:
    import cesarp.geometry.shp_input_parser
except Exception:
    pass
from cesarp.geometry.GeometryBuilderFactory import GeometryBuilderFactory
from cesarp.geometry import area_calculator
from cesarp.manager.GlazingRatioBldgSpecific import GlazingRatioBldgSpecific
from cesarp.manager import _default_config_file
from cesarp.manager.manager_protocols import (
    GeometryBuilderFactoryProtocol,
    GlazingRatioProviderProtocol,
    BuildingOperationFactoryProtocol,
    SiteFactoryProtocol,
)
from cesarp.construction.construction_protocols import (
    ArchetypicalConstructionFactoryProtocol,
    NeighbouringConstructionFactoryProtocol,
)
from cesarp.operation.protocols import PassiveCoolingOperationFactoryProtocol
from cesarp.operation.PassiveCoolingOperationFactory import PassiveCoolingOperationFactory
from cesarp.site.SingleSiteFactory import SingleSiteFactory
from cesarp.site.SitePerSwissCommunityFactory import SitePerSwissCommunityFactory
from cesarp.site.SitePerBuildingSpecificWeatherFile import SitePerBuildingSpecificWeatherFile
from cesarp.construction.ConstructionBuilder import ConstructionBuilder
from cesarp.construction.ConstructionFacade import ConstructionFacade
from cesarp.model.BuildingModel import BuildingModel
from cesarp.model.BldgType import BldgType
from cesarp.model.EnergySource import EnergySource
from cesarp.SIA2024.SIA2024Facade import SIA2024Facade

from cesarp.construction.NeighbouringBldgConstructionFactory import NeighbouringBldgConstructionFactory

_COL_HEATING_E_CARRIER = "heating_energy_carrier"
_COL_DHW_E_CARRIER = "dhw_energy_carrier"


class BldgModelFactory:
    """
    The factory controls how the cesarp.model.BuildingModel is created.
    It reads the per-building information from the input file(s) set in the config, reads the site vertices
    and chooses the right factory classes according to the configuration settings to create the different parts
    of the model.

    Note that reading the site vertices file can take quite long. This file is only read once per instance of BldgModelFactory.
    In case you have different site vertices files for your project, create a new BldgModelFactory for each of those site vertices
    files.

    In case you want to take control over a part of the model creation for which the factory class cannot be set in the
    configuration, you can change the factory instance after initialization of this class.
    If you only want to change the IDF creation part, check out the instruction in :py:class:`cesarp.eplus_adapter`

    After the class has been initialized, you can call create_bldg_model(bldg_fid) for each building of your site for
    which you want to create a building model. The necessary input data for all the buildings is loaded in the initialization.
    """

    _BLDG_I_COL_OVERALL_GLZ_RATIO = "resulting_overall_bldg_glazing_ratio"
    _BLDG_I_COL_TARGET_GLZ_RATIO = "target_per_wall_glazing_ratio"
    _BLDG_I_COL_HEIGHT = "bldg_height_meter"
    _BLDG_I_COL_FLOOR_HEIGHT = "floor_height_meter"
    _BLDG_I_COL_NR_OF_FLOORS = "nr_of_floors"
    _BLDG_I_COl_GROUNDFLOOR_AREA = "groundfloor_area"

    def __init__(self, ureg: pint.UnitRegistry, custom_config: Optional[Dict[str, Any]], sia_params_generation_lock=None):
        """
        :param ureg: pint unit registry application instance
        :type ureg: pint.UnitRegistry
        :param custom_config: main configuration parameters, overwriting the CESAR-P defaults, must at least contain the configuration pointing to input files
        :type custom_config: Dict[str, Any], optional
        :param sia_params_generation_lock: when using multiprocessing and creating SIA profile files on request, we need to synchronize the processes, defaults to None (usually not required anymore if using the pre-generated profiles)
        :type sia_params_generation_lock: Lock, optional
        """
        # per_bldg_infos_used is used to collect all input information used during model creation, must be defined before calling subsequent init-methods, so they can fill in their information...
        self.per_bldg_infos_used = pd.DataFrame()
        self._logger = logging.getLogger(__name__)
        self._unit_reg = ureg
        self._custom_config = custom_config
        self._mgr_config = cesarp.common.config_loader.load_config_for_package(_default_config_file, __package__, custom_config)
        self._year_of_constr_per_bldg = self.__read_year_of_construction_per_bldg()
        _bldg_type_per_bldg_series = self.__read_bldg_type()
        self._bldg_type_per_bldg: Dict[int, BldgType] = {fid: BldgType[bldg_type_str] for fid, bldg_type_str in _bldg_type_per_bldg_series.to_dict().items()}

        self.per_bldg_infos_used = pd.concat([self.per_bldg_infos_used, self._year_of_constr_per_bldg])
        self.per_bldg_infos_used = pd.concat([self.per_bldg_infos_used, _bldg_type_per_bldg_series], axis="columns")
        self.per_bldg_infos_used[self._BLDG_I_COL_HEIGHT] = None
        self.per_bldg_infos_used[self._BLDG_I_COL_FLOOR_HEIGHT] = None
        self.per_bldg_infos_used[self._BLDG_I_COL_NR_OF_FLOORS] = None

        # all following factories can be set to a custom factory after initialization of BldgModelFactory
        self._geometry_builder_factory: GeometryBuilderFactoryProtocol = self.__create_geometry_builder_factory()
        self._archetype_constr_factory: ArchetypicalConstructionFactoryProtocol = self.__create_archetype_constr_factory(self._year_of_constr_per_bldg)
        self._neighbouring_bldg_constr_factory: NeighbouringConstructionFactoryProtocol = NeighbouringBldgConstructionFactory(self._unit_reg, self._custom_config)
        self._glazing_ratio_provider: Optional[GlazingRatioProviderProtocol] = self.__create_glazing_ratio_provider()
        self._bldg_operation_factory: BuildingOperationFactoryProtocol = self.__create_bldg_operation_factory(_bldg_type_per_bldg_series, sia_params_generation_lock)
        self._site_factory: SiteFactoryProtocol = self.__create_site_factory()

    def create_bldg_model(self, bldg_fid: int) -> BuildingModel:
        """
        :param bldg_fid: fid of building for which to create the model
        :return: BuildingModel
        """
        bldg_constr = self.__get_bldg_construction(bldg_fid)
        geometry_builder = self._geometry_builder_factory.get_geometry_builder(bldg_fid, bldg_constr.glazing_ratio)
        shape = geometry_builder.get_bldg_shape_detailed()
        neighbours = geometry_builder.get_bldg_shape_of_neighbours()
        self.__add_target_glz_ratio_to_used_info_df(bldg_fid, bldg_constr.glazing_ratio)
        self.__add_resulting_glz_ratio_to_used_info_df(bldg_fid, geometry_builder.overall_glazing_ratio)
        neighbours_constr_props = self._neighbouring_bldg_constr_factory.get_neighbours_construction_props(bldg_constr.window_constr.glass)
        site = self._site_factory.get_site(bldg_fid)
        bldg_operation = self._bldg_operation_factory.get_building_operation(bldg_fid, shape.get_nr_of_floors())
        self.per_bldg_infos_used.loc[bldg_fid, self._BLDG_I_COL_HEIGHT] = shape.get_bldg_height()
        self.per_bldg_infos_used.loc[bldg_fid, self._BLDG_I_COL_NR_OF_FLOORS] = shape.get_nr_of_floors()
        self.per_bldg_infos_used.loc[bldg_fid, self._BLDG_I_COL_FLOOR_HEIGHT] = shape.get_floor_height()
        self.per_bldg_infos_used.loc[bldg_fid, self._BLDG_I_COl_GROUNDFLOOR_AREA] = area_calculator.calc_groundfloor_area(shape)

        return BuildingModel(
            bldg_fid,
            self._year_of_constr_per_bldg.loc[bldg_fid, "year_of_construction"],
            site,
            shape,
            neighbours,
            neighbours_constr_props,
            bldg_constr,
            bldg_operation,
            self._bldg_type_per_bldg[bldg_fid],
        )

    def __create_geometry_builder_factory(self):
        site_vertices_filepath = self._mgr_config["SITE_VERTICES_FILE"]["PATH"]
        self._logger.info(f"loading site vertices from {site_vertices_filepath}. Takes a while depending on the size of the site. For 10'000 building ~3 Minutes on a Laptop...")
        if Path(site_vertices_filepath).suffix == ".shp":
            from cesarp.geometry.shp_input_parser import read_sitevertices_from_shp

            flat_site_vertices_list = read_sitevertices_from_shp(site_vertices_filepath)
        else:
            flat_site_vertices_list = cesarp.geometry.csv_input_parser.read_sitevertices_from_csv(
                site_vertices_filepath,
                self._mgr_config["SITE_VERTICES_FILE"]["LABELS"],
                self._mgr_config["SITE_VERTICES_FILE"]["SEPARATOR"],
            )
        return GeometryBuilderFactory(flat_site_vertices_list, ureg=self._unit_reg, custom_config=self._custom_config)

    def __create_bldg_operation_factory(self, sia_bldg_type_mapping: pd.Series, sia_params_generation_lock=None) -> BuildingOperationFactoryProtocol:
        """
        :param sia_bldg_type_mapping: series, index is bldg fid, value bldg type as string
        :param sia_params_generation_lock: only relevant in case sia2024 profiles are used. pass a instance of a lock if sia
        parameters might be generated from several threads at the same time in the same location
        :return: object providing the BuildingOperationFactoryProtocol, concrete implementation depends on configuration
        """
        passive_cooling_op_fact: PassiveCoolingOperationFactoryProtocol = PassiveCoolingOperationFactory(self._unit_reg, self._custom_config)

        op_fact_class_name: str = self._mgr_config["BUILDING_OPERATION_FACTORY_CLASS"]
        if op_fact_class_name == "cesarp.SIA2024.SIA2024Facade.SIA2024Facade":
            # save as member because sia2024 is probably used as infiltration rate source as well....
            self.sia2024 = SIA2024Facade(sia_bldg_type_mapping.to_dict(), passive_cooling_op_fact, self._unit_reg, self._custom_config)

            if sia_params_generation_lock:
                sia_params_generation_lock.acquire()
            # load has to be synchronized as well, because 2nd process has to wait till the first finished creating the profiles...
            self.sia2024.load_or_create_parameters(sia_bldg_type_mapping.unique())
            if sia_params_generation_lock:
                sia_params_generation_lock.release()
            return self.sia2024
        else:
            op_fact_class = cesarp.common.get_class_from_str(op_fact_class_name)
            return op_fact_class(passive_cooling_op_fact, self._unit_reg, self._custom_config)

    def __create_archetype_constr_factory(self, year_of_constr_per_bldg: pd.DataFrame):
        year_of_constr_as_dict = year_of_constr_per_bldg["year_of_construction"].to_dict()
        try:
            e_carriers_per_bldg = self.__read_ecarriers_per_bldg()
            self.per_bldg_infos_used = pd.concat([self.per_bldg_infos_used, e_carriers_per_bldg], axis="columns")
            dhw_e_carrier_as_dict = e_carriers_per_bldg[_COL_DHW_E_CARRIER].to_dict()
            heating_e_carrier_as_dict = e_carriers_per_bldg[_COL_HEATING_E_CARRIER].to_dict()
        except (Exception, FileNotFoundError) as exc:
            if self._mgr_config["DO_CALC_OP_EMISSIONS_AND_COSTS"]:
                self._logger.error(
                    "Could not read energy carrier pre building info. Setting Energy Carrier info to " "None in building models. Operational emission&costs cannot be calculated.",
                    exc_info=exc,
                )
            dhw_e_carrier_as_dict = {fid: None for fid in year_of_constr_as_dict.keys()}
            heating_e_carrier_as_dict = {fid: None for fid in year_of_constr_as_dict.keys()}

        return ConstructionFacade.get_constructional_archetype_factory(
            year_of_constr_as_dict,
            dhw_e_carrier_as_dict,
            heating_e_carrier_as_dict,
            self._unit_reg,
            self._custom_config,
        )

    def __read_year_of_construction_per_bldg(self) -> pd.DataFrame:
        all_bldgs_yearofconstr = cesarp.common.csv_reader.read_csvy(
            self._mgr_config["BLDG_AGE_FILE"]["PATH"],
            ["gis_fid", "year_of_construction"],
            self._mgr_config["BLDG_AGE_FILE"]["LABELS"],
            self._mgr_config["BLDG_AGE_FILE"]["SEPARATOR"],
            "gis_fid",
        )
        return all_bldgs_yearofconstr

    def __read_ecarriers_per_bldg(self):
        energy_carriers = cesarp.common.csv_reader.read_csvy(
            self._mgr_config["BLDG_INSTALLATION_FILE"]["PATH"],
            ["gis_fid", _COL_DHW_E_CARRIER, _COL_HEATING_E_CARRIER],
            self._mgr_config["BLDG_INSTALLATION_FILE"]["LABELS"],
            self._mgr_config["BLDG_INSTALLATION_FILE"]["SEPARATOR"],
            "gis_fid",
        )
        return energy_carriers.loc[:, [_COL_DHW_E_CARRIER, _COL_HEATING_E_CARRIER]].applymap(lambda x: EnergySource(x))

    def __read_bldg_type(self) -> pd.Series:
        sia_bldg_type_mapping = cesarp.common.csv_reader.read_csvy(
            self._mgr_config["BLDG_TYPE_PER_BLDG_FILE"]["PATH"],
            ["gis_fid", "sia_bldg_type"],
            self._mgr_config["BLDG_TYPE_PER_BLDG_FILE"]["LABELS"],
            self._mgr_config["BLDG_TYPE_PER_BLDG_FILE"]["SEPARATOR"],
            "gis_fid",
        )["sia_bldg_type"]
        return sia_bldg_type_mapping

    def __create_glazing_ratio_provider(self) -> Optional[GlazingRatioProviderProtocol]:
        if self._mgr_config["GLAZING_RATIO_PER_BLDG_FILE"]["ACTIVE"]:
            all_bldgs_glazing_ratio = cesarp.common.csv_reader.read_csvy(
                self._mgr_config["GLAZING_RATIO_PER_BLDG_FILE"]["PATH"],
                ["gis_fid", "glazing_ratio"],
                self._mgr_config["GLAZING_RATIO_PER_BLDG_FILE"]["LABELS"],
                self._mgr_config["GLAZING_RATIO_PER_BLDG_FILE"]["SEPARATOR"],
                "gis_fid",
            )
            return GlazingRatioBldgSpecific(all_bldgs_glazing_ratio["glazing_ratio"].to_dict())
        else:
            return None

    def __create_site_factory(self) -> SiteFactoryProtocol:
        single_site_active = self._mgr_config["SINGLE_SITE"]["ACTIVE"]
        ch_sites_active = self._mgr_config["SITE_PER_CH_COMMUNITY"]["ACTIVE"]
        weather_file_per_bldg_active = self._mgr_config["WEATHER_FILE_PER_BUILDING"]["ACTIVE"]
        assert not (
            (single_site_active and ch_sites_active) or (single_site_active and weather_file_per_bldg_active) or (ch_sites_active and weather_file_per_bldg_active)
        ), "check configuration. only one of SITE_PER_CH_COMMUNITY, SINGLE_SITE, WEATHER_FILE_PER_BUILDING should be active."
        if single_site_active:
            return SingleSiteFactory(self._mgr_config["SINGLE_SITE"]["WEATHER_FILE"], self._unit_reg, self._custom_config)
        elif ch_sites_active:
            mapping_file_cfg = self._mgr_config["SITE_PER_CH_COMMUNITY"]["BLDG_TO_COMMUNITY_FILE"]
            bldg_fid_to_community_id = cesarp.common.read_csvy(
                mapping_file_cfg["PATH"],
                ["bldg_fid", "community_id"],
                mapping_file_cfg["LABELS"],
                mapping_file_cfg["SEPARATOR"],
                index_column_name="bldg_fid",
            )
            return SitePerSwissCommunityFactory(bldg_fid_to_community_id["community_id"].to_dict(), self._unit_reg, self._custom_config)
        elif weather_file_per_bldg_active:
            mapping_file_cfg = self._mgr_config["WEATHER_FILE_PER_BUILDING"]["WEATHER_FILE_PER_BLDG_FILE"]
            bldg_fid_to_weather_file = cesarp.common.read_csvy(
                mapping_file_cfg["PATH"],
                ["gis_fid", "weather"],
                mapping_file_cfg["LABELS"],
                mapping_file_cfg["SEPARATOR"],
                index_column_name="gis_fid",
            )
            weather_files_folder_path = self._mgr_config["WEATHER_FILE_PER_BUILDING"]["WEATHER_FILES_FOLDER"]
            return SitePerBuildingSpecificWeatherFile(bldg_fid_to_weather_file["weather"].to_dict(), weather_files_folder_path, self._unit_reg, self._custom_config)
        else:
            raise Exception("no site strategy activated in config. set SITE_PER_CH_COMMUNITY or SINGLE_SITE or WEATHER_FILE_PER_BUILDING active")

    def __add_target_glz_ratio_to_used_info_df(self, bldg_fid: int, target_glazing_ratio: Union[pint.Quantity, float]):
        if isinstance(target_glazing_ratio, pint.Quantity):
            target_glazing_ratio = target_glazing_ratio.m
        if self._BLDG_I_COL_TARGET_GLZ_RATIO not in self.per_bldg_infos_used.columns:  # add column if not already there
            self.per_bldg_infos_used.insert(len(self.per_bldg_infos_used.columns), self._BLDG_I_COL_TARGET_GLZ_RATIO, None)
        self.per_bldg_infos_used.at[bldg_fid, self._BLDG_I_COL_TARGET_GLZ_RATIO] = round(target_glazing_ratio, ndigits=4)

    def __add_resulting_glz_ratio_to_used_info_df(self, bldg_fid: int, overall_glazing_ratio: float):
        if self._BLDG_I_COL_OVERALL_GLZ_RATIO not in self.per_bldg_infos_used.columns:  # add column if not already there
            self.per_bldg_infos_used.insert(len(self.per_bldg_infos_used.columns), self._BLDG_I_COL_OVERALL_GLZ_RATIO, None)
        self.per_bldg_infos_used.at[bldg_fid, self._BLDG_I_COL_OVERALL_GLZ_RATIO] = round(overall_glazing_ratio, ndigits=4)

    def __get_bldg_construction(self, bldg_fid):
        constr_archetype = self._archetype_constr_factory.get_archetype_for(bldg_fid)
        constr_builder = ConstructionBuilder(bldg_fid, constr_archetype)
        if self._mgr_config["RANDOM_CONSTRUCTIONS"]:
            constr_builder.activate_randomization()
        if self._glazing_ratio_provider:
            constr_builder.set_external_glazing_ratio(self._glazing_ratio_provider.get_for_bldg_fid)
        inf_rate_source_selection = self._mgr_config["INFILTRATION_RATE_SOURCE"]
        if inf_rate_source_selection == "SIA2024":
            assert (
                self.sia2024
            ), "not expected that INFILTRATION_RATE_SOURCE is set to SIA2024 but BUILDING_OPERATION_FACTORY_CLASS not to SIA2024Facade. Please check your configuration."
            constr_builder.set_external_infiltration_profile(self.sia2024.get_infiltration_profile)
            constr_builder.set_external_infiltration_rate(self.sia2024.get_infiltration_rate)
        elif inf_rate_source_selection != "Archetype":
            raise Exception(f"infiltration rate source {inf_rate_source_selection} not supported.")
        return constr_builder.build()
