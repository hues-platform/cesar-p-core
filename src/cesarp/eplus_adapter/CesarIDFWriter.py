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
import pint
import os
import copy
from typing import TypeVar, Mapping, Protocol, Optional, Union, Tuple, Dict, List
from eppy.modeleditor import IDF
from eppy.bunch_subclass import EpBunch
from six import StringIO

from cesarp.common.ScheduleFile import ScheduleFile
from cesarp.common.ScheduleFixedValue import ScheduleFixedValue
from cesarp.common import config_loader
from cesarp.eplus_adapter import _default_config_file
from cesarp.eplus_adapter import idf_writer_geometry
from cesarp.eplus_adapter import idf_strings
from cesarp.eplus_adapter import idf_writer_operation
from cesarp.eplus_adapter import idf_writing_helpers
from cesarp.eplus_adapter.eplus_sim_runner import get_eplus_version, get_idd_path
from cesarp.model.BldgShape import BldgShapeEnvelope, BldgShapeDetailed
from cesarp.model.BuildingModel import BuildingModel
from cesarp.model.BuildingConstruction import InstallationsCharacteristics
from cesarp.model.WindowConstruction import WindowShadingMaterial
from cesarp.model.BuildingOperationMapping import BuildingOperationMapping
from cesarp.model.SiteGroundTemperatures import SiteGroundTemperatures
from cesarp.eplus_adapter.ConstructionIDFWritingHandler import ConstructionIDFWritingHandler

ConstrType = TypeVar("ConstrType")


class ProfileFilesHandler(Protocol):
    def add_file(self, file_path):
        ...


def no_constr_writer(constr, idf: IDF):
    return idf


def no_idf_constr_files(constr):
    return []


class CesarIDFWriter:
    """
    Handels the IDF Writing process

    For each building, you create a new instance of CesarIDFWriter and call write_bldg_model() to create a full IDF file.

    """

    def __init__(
        self,
        idf_file_path,
        unit_registry,
        profiles_files_handler: Optional[ProfileFilesHandler] = None,
        custom_config=None,
    ):
        """
        You can only use one construction type at a time. All three constr_xxx callables take a construction object as the first argument.
        Either constr_writer or constr_get_idf_files should point to a method of your construction, you can also assign both method if you wish.

        :param constr_name_lookup: function which returns the name for a given construction object
        :param constr_writer: function which writes the passed construction object to the idf file passed as a second parameter
        :param constr_get_idf_files: function which returns partial idf files for that construction which shall be appended at the end of IDF-Writing process. files are collected
               and before writing duplicated files are removed. this allows that you return the same file several
               times and it will only be appended once, but means that you have to make sure files with different content have different file names.
        :param idf_file_path: file name including full path to write IDF to. file should not exist.
        :param geometry_writer: instance of class to write geometry properties from the model to the IDF
        :param custom_config: dictionary containing configuration entries overwriting package default config
        """
        assert not os.path.exists(idf_file_path), f"Cannot create IDF File {idf_file_path}. Already existing."
        self.logger = logging.getLogger(__name__)
        self._cfg = config_loader.load_config_for_package(_default_config_file, __package__, custom_config)
        self.unit_registry = unit_registry
        idd_path = get_idd_path(ep_config=self._cfg)
        self.logger.info(f"using IDD {idd_path}")
        IDF.setiddname(idd_path)
        self.idf_file_path = idf_file_path
        self.__create_empty_idf()
        self.zone_data = Optional[Dict[int, Tuple[str, List[EpBunch]]]]
        if profiles_files_handler:
            self.profiles_files_handler_method = profiles_files_handler.add_file
        else:
            self.profiles_files_handler_method = lambda x: x  # do nothing, just return filepath back

    def write_bldg_model(self, bldg_model: BuildingModel) -> None:
        """
        :param bldg_model: Building model to write to IDF
        :type bldg_model: BuildingModel
        """
        idf = IDF(str(self.idf_file_path))
        self.add_basic_simulation_settings(idf, bldg_model.site.site_ground_temperatures)
        constr_handler = ConstructionIDFWritingHandler(bldg_model.bldg_construction, bldg_model.neighbours_construction_props, self.unit_registry)
        self.add_building_geometry(idf, bldg_model.bldg_shape, constr_handler)

        self.add_neighbours(idf, bldg_model.neighbours, constr_handler)
        self.add_building_properties(
            idf,
            bldg_model.bldg_operation_mapping,
            bldg_model.bldg_construction.installation_characteristics,
            bldg_model.bldg_construction.infiltration_rate,
            self.__handle_profile_file(bldg_model.bldg_construction.infiltration_profile),
            bldg_model.bldg_construction.window_constr.shade,
        )
        idf = self.add_output_settings(idf)
        idf.save(filename=str(self.idf_file_path))

    def add_basic_simulation_settings(self, idf, site_ground_temps: SiteGroundTemperatures) -> IDF:
        """
        adds to the idf simulation settings needed to run the simulation in the way we want

        :return: nothing, changes are saved to idf file
        """

        simulationCtrl = idf.newidfobject(idf_strings.IDFObjects.simulation_control)
        simulationCtrl.Run_Simulation_for_Sizing_Periods = idf_strings.no

        bldg_idf_obj = idf.newidfobject(idf_strings.IDFObjects.building)
        bldg_idf_obj.Name = idf_strings.CustomObjNames.building

        timestep = idf.newidfobject(idf_strings.IDFObjects.timestep)
        timestep.Number_of_Timesteps_per_Hour = self._cfg["SIMULATION_SETTINGS"]["NR_OF_TIMESTEPS"]

        convergence_limits = idf.newidfobject(idf_strings.IDFObjects.convergence_limits)
        convergence_limits.Minimum_System_Timestep = self._cfg["SIMULATION_SETTINGS"]["MIN_SYSTEM_TIMESTAMP"]
        convergence_limits.Maximum_HVAC_Iterations = self._cfg["SIMULATION_SETTINGS"]["MAX_HVAC_ITERATIONS"]

        runPeriod = idf.newidfobject(idf_strings.IDFObjects.run_period)
        runPeriod.Name = idf_strings.CustomObjNames.run_periods
        runPeriod.Begin_Month = 1
        runPeriod.Begin_Day_of_Month = 1
        runPeriod.End_Month = 12
        runPeriod.End_Day_of_Month = 31
        runPeriod.Day_of_Week_for_Start_Day = idf_strings.Weekdays.sunday
        runPeriod.Use_Weather_File_Holidays_and_Special_Days = idf_strings.no
        runPeriod.Use_Weather_File_Daylight_Saving_Period = idf_strings.no

        zone_air_heat_balance_algo = idf.newidfobject(idf_strings.IDFObjects.zone_air_heat_balance_algorithm)
        zone_air_heat_balance_algo.Algorithm = idf_strings.ZoneAirHeatBalanceAlgorithm.analytical_solution

        self._add_site_ground_temperatures(idf, site_ground_temps)

        return idf

    def _add_site_ground_temperatures(self, idf, site_ground_temps: SiteGroundTemperatures):
        site_ground_bldg_surface = idf.newidfobject(idf_strings.IDFObjects.site_ground_temperature_building_surface)
        idf_writing_helpers.add_monthly(
            site_ground_bldg_surface,
            [site_ground_temps.building_surface.to(self.unit_registry.degreeC).m] * 12,
            idf_strings.GroundTempFieldNamePatterns.building_surface,
        )
        site_ground_fcfactormethod = idf.newidfobject(idf_strings.IDFObjects.site_ground_temperature_fc_factor_method)
        idf_writing_helpers.add_monthly(
            site_ground_fcfactormethod,
            [temp.to(self.unit_registry.degreeC).m for temp in site_ground_temps.ground_temp_per_month],
            idf_strings.GroundTempFieldNamePatterns.fcfactormethod,
        )
        site_ground_shallow = idf.newidfobject(idf_strings.IDFObjects.site_ground_temperature_shallow)
        idf_writing_helpers.add_monthly(
            site_ground_shallow,
            [site_ground_temps.shallow.to(self.unit_registry.degreeC).m] * 12,
            idf_strings.GroundTempFieldNamePatterns.shallow,
        )
        site_ground_deep = idf.newidfobject(idf_strings.IDFObjects.site_ground_temperature_deep)
        idf_writing_helpers.add_monthly(
            site_ground_deep,
            [site_ground_temps.deep.to(self.unit_registry.degreeC).m] * 12,
            idf_strings.GroundTempFieldNamePatterns.deep,
        )

    @staticmethod
    def _add_output_meter(idf, name, frequency):
        meter = idf.newidfobject(idf_strings.IDFObjects.output_meter)
        if idf.idd_version[0] < 9 and idf.idd_version[1] < 8:
            meter.Name = name
        else:
            meter.Key_Name = name
        meter.Reporting_Frequency = frequency

    @staticmethod
    def _add_output_variable(idf, name, frequency):
        out_var = idf.newidfobject(idf_strings.IDFObjects.output_variable)
        out_var.Variable_Name = name
        out_var.Reporting_Frequency = frequency

    def add_output_settings(self, idf) -> IDF:
        """
        Add definitions to the IDF for generating appropriate outputs.

        :return: nothing, changes are saved to idf file
        """
        variable_dict = idf.newidfobject(idf_strings.IDFObjects.output_variable_dictionary)
        variable_dict.Key_Field = idf_strings.KeyField.idf
        table_summary = idf.newidfobject(idf_strings.IDFObjects.output_table_summary_reports)
        table_summary.Report_1_Name = idf_strings.SummaryReports.all_summary
        table_style = idf.newidfobject(idf_strings.IDFObjects.output_control_table_style)
        table_style.Column_Separator = idf_strings.ColumnSeparator.comma_and_html
        table_style.Unit_Conversion = idf_strings.UnitConversion.j_to_kwh

        for frequency, meters in self._cfg["OUTPUT_METER"].items():
            if meters:  # there might be no entries for a certain frequency
                freq_idf_str = idf_strings.ResultsFrequency[frequency].value
                [CesarIDFWriter._add_output_meter(idf, meter_var, freq_idf_str) for meter_var in meters]
        for frequency, output_vars in self._cfg["OUTPUT_VARS"].items():
            if output_vars:  # there might be no entries for a certain frequency
                freq_idf_str = idf_strings.ResultsFrequency[frequency].value
                [CesarIDFWriter._add_output_variable(idf, output_var, freq_idf_str) for output_var in output_vars]

        return idf

    def add_building_geometry(self, idf, bldg_shape_detailed: BldgShapeDetailed, constr_handler: ConstructionIDFWritingHandler):
        """
        Add the building specified by the passed geometry. Uses the construction handler to assign the Constructions to
        the geometry elements.

        :param idf: python object to which the geometry shall be added; will be changed in place!
        :param bldg_shape_detailed: defines building geometry
        :param constr_handler: object handling the construction of wall, roof, groundfloor and windows for the building
        :return: list of partial idf files defining construction and materials which are referenced by the geometry
                 objects added; might be emtpy in case constuctions and materials are written to the idf python object
        """

        idf_writer_geometry.add_basic_geometry_settings(idf)
        self.zone_data = idf_writer_geometry.add_building(idf, bldg_shape_detailed, constr_handler)

    def add_neighbours(
        self,
        idf,
        neighbour_bldg_shapes_simple: Mapping[int, BldgShapeEnvelope],
        constr_handler: ConstructionIDFWritingHandler,
    ) -> IDF:
        """
        Add neighbouring buildings as shading objects

        :param neighbour_bldg_shapes_simple: defining the envelop geometries of neighbouring buildings, mapping of gis_fid to BldgShapeEnvelope
        :param constr_handler: handling adding constructional properties to idf/idf object. holds the construction information
        :return: nothing, changes are directly saved to IDF file
        """
        idf_writer_geometry.add_basic_shading_settings(idf, self._cfg["SIMULATION_SETTINGS"]["SHADOW_CALCULATION_FREQUENCY"])
        idf_writer_geometry.add_neighbours_as_shading_objects(idf, neighbour_bldg_shapes_simple, constr_handler)
        return idf

    def add_building_properties(
        self,
        idf,
        building_operation_mapping: BuildingOperationMapping,
        installation_characteristics: InstallationsCharacteristics,
        infiltrationRate: pint.Quantity,
        infiltrationProfile: Union[ScheduleFile, ScheduleFixedValue],
        window_shading_material: WindowShadingMaterial,
    ) -> IDF:
        """
        Adding internal conditions according to the passed definition to each zone of the building.

        :param building_operation: model object holding all operational parameters
        :param installation_characteristics: model object holding all installation specific characteristics, e.g. the efficiency of lighting
        :return: nothing, changes are saved to the idf
        """
        assert self.zone_data is not None, "make sure that prior to calling add_buidlding_properties attribute zone_data is initialized, e.g. by calling add_buidling_geometry"
        assert (
            list(self.zone_data.keys()) == building_operation_mapping.all_assigned_floor_nrs  # type: ignore  # checked self.zone_data for none in assert on line 288
        ), f"zones/floors {list(self.zone_data.keys())} in geometry do not match with the floors in the building operation mapping ({building_operation_mapping.all_assigned_floor_nrs})"  # type: ignore  # checked self.zone_data for none in assert on line 288

        for (floor_nrs, bldg_op) in building_operation_mapping.get_operation_assignments():
            bldg_op_local_profiles = copy.deepcopy(bldg_op)
            bldg_op_local_profiles.electric_appliances.fraction_schedule = self.__handle_profile_file(bldg_op_local_profiles.electric_appliances.fraction_schedule)
            bldg_op_local_profiles.lighting.fraction_schedule = self.__handle_profile_file(bldg_op_local_profiles.lighting.fraction_schedule)
            bldg_op_local_profiles.occupancy.occupancy_fraction_schedule = self.__handle_profile_file(bldg_op_local_profiles.occupancy.occupancy_fraction_schedule)
            bldg_op_local_profiles.dhw.fraction_schedule = self.__handle_profile_file(bldg_op_local_profiles.dhw.fraction_schedule)
            bldg_op_local_profiles.hvac.ventilation_fraction_schedule = self.__handle_profile_file(bldg_op_local_profiles.hvac.ventilation_fraction_schedule)
            bldg_op_local_profiles.hvac.cooling_setpoint_schedule = self.__handle_profile_file(bldg_op_local_profiles.hvac.cooling_setpoint_schedule)
            bldg_op_local_profiles.hvac.heating_setpoint_schedule = self.__handle_profile_file(bldg_op_local_profiles.hvac.heating_setpoint_schedule)
            bldg_op_local_profiles.occupancy.activity_schedule = self.__handle_profile_file(bldg_op_local_profiles.occupancy.activity_schedule)

            if bldg_op_local_profiles.night_vent.is_active:
                bldg_op_local_profiles.night_vent.maximum_indoor_temp_profile = self.__handle_profile_file(bldg_op_local_profiles.night_vent.maximum_indoor_temp_profile)

            for floor_nr, (zone_name, windows_in_zone) in self.zone_data.items():  # type: ignore  # checked self.zone_data for none in assert on line 288
                if floor_nr in floor_nrs:
                    idf_writer_operation.add_building_operation(idf, zone_name, bldg_op_local_profiles, installation_characteristics, self.unit_registry)
                    idf_writer_operation.add_zone_infiltration(idf, zone_name, infiltrationRate, infiltrationProfile, self.unit_registry)
                    idf_writer_operation.add_passive_cooling(idf, zone_name, windows_in_zone, bldg_op_local_profiles, window_shading_material)

        return idf

    def __handle_profile_file(self, the_profile):
        if isinstance(the_profile, ScheduleFile):
            the_profile_updated_path = copy.copy(the_profile)
            the_profile_updated_path.schedule_file = self.profiles_files_handler_method(the_profile_updated_path.schedule_file)
            return the_profile_updated_path
        return the_profile

    def __create_empty_idf(self):
        idfstring = idf_strings.version.format(get_eplus_version(ep_config=self._cfg))
        fhandle = StringIO(idfstring)
        idf = IDF(fhandle)
        idf.save(str(self.idf_file_path))
