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
from pint import DimensionalityError
from typing import List
from eppy.bunch_subclass import EpBunch

import cesarp.eplus_adapter.idf_strings as idf_strings
import cesarp.eplus_adapter.idf_writing_helpers as idf_writing_helpers
from cesarp.model.BuildingOperation import BuildingOperation, Occupancy, InstallationOperation, HVACOperation
from cesarp.model.BuildingConstruction import LightingCharacteristics, InstallationsCharacteristics
import cesarp.common.ScheduleTypeLimits
from cesarp.model.WindowConstruction import WindowShadingMaterial
from cesarp.eplus_adapter.idf_writer_window_shading import add_shading_on_windows
from cesarp.eplus_adapter import idf_writer_night_vent


def add_building_operation(idf, zone_idf_name, bldg_operation: BuildingOperation, install_characteristics: InstallationsCharacteristics, ureg):
    """
    :param idf: IDF
    :param bldg_operation: cesarp.operation.BuildingOperation
    :return:
    """
    add_people(idf, zone_idf_name, bldg_operation.occupancy, install_characteristics.fraction_radiant_from_activity, ureg)
    add_lights(idf, zone_idf_name, bldg_operation.lighting, install_characteristics.lighting_characteristics, ureg)
    add_electric_equipment(
        idf,
        zone_idf_name,
        bldg_operation.electric_appliances,
        install_characteristics.electric_appliances_fraction_radiant,
        ureg,
    )
    add_hot_water_equipment(idf, zone_idf_name, bldg_operation.dhw, install_characteristics.dhw_fraction_lost, ureg)
    add_HVAC_template(idf, zone_idf_name, bldg_operation.hvac, bldg_operation.name, ureg)


def add_passive_cooling(idf, zone_idf_name, windows_in_zone: List[EpBunch], bldg_operation: BuildingOperation, shading_mat_model: WindowShadingMaterial):
    add_shading_on_windows(idf, zone_idf_name, windows_in_zone, bldg_operation.win_shading_ctrl, shading_mat_model)
    if bldg_operation.night_vent.is_active:
        idf_writer_night_vent.add_night_ventilation_for_zone(idf, zone_idf_name, bldg_operation.night_vent)


def add_people(idf, zone_idf_name, occupancy: Occupancy, fraction_radiant_from_activity: pint.Quantity, ureg):
    occupancy_sched_idf_name = idf_writing_helpers.add_schedule(idf, occupancy.occupancy_fraction_schedule, required_type=cesarp.common.ScheduleTypeLimits.FRACTION())
    activity_sched_idf_name = idf_writing_helpers.add_schedule(idf, occupancy.activity_schedule, required_unit=ureg.W / ureg.person)
    people_idf_obj = idf.newidfobject(idf_strings.IDFObjects.people)
    people_idf_obj.Name = idf_strings.CustomObjNames.people.format(zone_idf_name)
    people_idf_obj.Zone_or_ZoneList_Name = zone_idf_name
    people_idf_obj.Number_of_People_Schedule_Name = occupancy_sched_idf_name
    people_idf_obj.Number_of_People_Calculation_Method = idf_strings.NumOfPeopleCalc.area_per_person
    people_idf_obj.Zone_Floor_Area_per_Person = occupancy.floor_area_per_person.to(ureg.m ** 2 / ureg.person).m
    people_idf_obj.Fraction_Radiant = fraction_radiant_from_activity.to(ureg.dimensionless).m
    people_idf_obj.Activity_Level_Schedule_Name = activity_sched_idf_name


def add_lights(idf, zone_idf_name, lighting_op: InstallationOperation, lighting_characteristics: LightingCharacteristics, ureg):
    lighting_sched_idf_name = idf_writing_helpers.add_schedule(idf, lighting_op.fraction_schedule, required_type=cesarp.common.ScheduleTypeLimits.FRACTION())
    lights_idf_obj = idf.newidfobject(idf_strings.IDFObjects.ligths)
    lights_idf_obj.Name = idf_strings.CustomObjNames.lights.format(zone_idf_name)
    lights_idf_obj.Zone_or_ZoneList_Name = zone_idf_name
    lights_idf_obj.Schedule_Name = lighting_sched_idf_name
    lights_idf_obj.Design_Level_Calculation_Method = idf_strings.DesignLevelCalc.watts_per_area
    lights_idf_obj.Watts_per_Zone_Floor_Area = lighting_op.power_demand_per_area.to(ureg.W / ureg.m ** 2).m
    lights_idf_obj.Return_Air_Fraction = lighting_characteristics.return_air_fraction.to(ureg.dimensionless).m
    lights_idf_obj.Fraction_Radiant = lighting_characteristics.fraction_radiant.to(ureg.dimensionless).m
    lights_idf_obj.Fraction_Visible = lighting_characteristics.fraction_visible.to(ureg.dimensionless).m


def add_hot_water_equipment(idf, zone_idf_name, dhw_op: InstallationOperation, dhw_fraction_lost: pint.Quantity, ureg):
    dhw_schedule_idf_name = idf_writing_helpers.add_schedule(idf, dhw_op.fraction_schedule, required_type=cesarp.common.ScheduleTypeLimits.FRACTION())
    hot_water_equ_idf_obj = idf.newidfobject(idf_strings.IDFObjects.hot_water_equipment)
    hot_water_equ_idf_obj.Name = idf_strings.CustomObjNames.hot_water_equipment.format(zone_idf_name)
    hot_water_equ_idf_obj.Zone_or_ZoneList_Name = zone_idf_name
    hot_water_equ_idf_obj.Schedule_Name = dhw_schedule_idf_name
    hot_water_equ_idf_obj.Design_Level_Calculation_Method = idf_strings.DesignLevelCalc.watts_per_area
    hot_water_equ_idf_obj.Power_per_Zone_Floor_Area = dhw_op.power_demand_per_area.to(ureg.W / ureg.m ** 2).m
    hot_water_equ_idf_obj.Fraction_Lost = dhw_fraction_lost.to(ureg.dimensionless).m


def add_electric_equipment(idf, zone_idf_name, el_app_op: InstallationOperation, el_app_fraction_radiant: pint.Quantity, ureg):
    applicance_sched_idf_name = idf_writing_helpers.add_schedule(idf, el_app_op.fraction_schedule, required_type=cesarp.common.ScheduleTypeLimits.FRACTION())
    el_equ_idf_obj = idf.newidfobject(idf_strings.IDFObjects.electric_equipment)
    el_equ_idf_obj.Name = idf_strings.CustomObjNames.electric_equipment.format(zone_idf_name)
    el_equ_idf_obj.Zone_or_ZoneList_Name = zone_idf_name
    el_equ_idf_obj.Schedule_Name = applicance_sched_idf_name
    el_equ_idf_obj.Design_Level_Calculation_Method = idf_strings.DesignLevelCalc.watts_per_area
    el_equ_idf_obj.Watts_per_Zone_Floor_Area = el_app_op.power_demand_per_area.to(ureg.W / ureg.m ** 2).m
    el_equ_idf_obj.Fraction_Radiant = el_app_fraction_radiant.to(ureg.dimensionless).m


def add_HVAC_template(idf, zone_idf_name, hvac: HVACOperation, name_prefix: str, ureg):
    thermostat_templ_idf_name = add_thermostat_template(idf, hvac.heating_setpoint_schedule, hvac.cooling_setpoint_schedule, name_prefix)
    outdoor_air_spec_idf_name = add_outdoor_air_sepc(idf, hvac.ventilation_fraction_schedule, hvac.outdoor_air_flow_per_zone_floor_area, name_prefix, ureg)
    hvac_idf_obj = idf.newidfobject(idf_strings.IDFObjects.hvac_template_zone_idealloadsairsystem)
    hvac_idf_obj.Zone_Name = zone_idf_name
    hvac_idf_obj.Template_Thermostat_Name = thermostat_templ_idf_name
    hvac_idf_obj.Outdoor_Air_Method = idf_strings.HVACOutdoorAirMethod.detailed_specification
    hvac_idf_obj.Design_Specification_Outdoor_Air_Object_Name = outdoor_air_spec_idf_name
    # clean up unused defaults due to change of outdoor air method
    hvac_idf_obj.Outdoor_Air_Flow_Rate_per_Person = 0


def add_outdoor_air_sepc(idf, ventilation_schedule, outdoor_air_flow_per_floor_area: pint.Quantity, name_prefix: str, ureg):
    ventilation_sched_idf_name = idf_writing_helpers.add_schedule(idf, ventilation_schedule, required_type=cesarp.common.ScheduleTypeLimits.FRACTION())
    idf_obj_type = idf_strings.IDFObjects.design_specifictaion_outdoor_air
    name = name_prefix + "_" + idf_strings.CustomObjNames.outdoor_air_spec
    if not idf_writing_helpers.exists_in_idf(idf, idf_obj_type, name):
        outdoor_air_spec_idf_obj = idf.newidfobject(idf_obj_type)
        outdoor_air_spec_idf_obj.Name = name
        outdoor_air_spec_idf_obj.Outdoor_Air_Method = idf_strings.OutdoorAirCalcMethod.flow_per_area
        outdoor_air_spec_idf_obj.Outdoor_Air_Flow_per_Zone_Floor_Area = outdoor_air_flow_per_floor_area.to(ureg.m ** 3 / ureg.s / ureg.m ** 2).m
        # clean up default values: set to zero because calc method changed to flow/area
        outdoor_air_spec_idf_obj.Outdoor_Air_Flow_per_Person = 0
        if idf.idd_version[0] < 9 and idf.idd_version[1] < 6:
            outdoor_air_spec_idf_obj.Outdoor_Air_Flow_Rate_Fraction_Schedule_Name = ventilation_sched_idf_name
        else:
            outdoor_air_spec_idf_obj.Outdoor_Air_Schedule_Name = ventilation_sched_idf_name

    return name


def add_thermostat_template(idf, heating_setpoint_schedule, cooling_setpoint_schedule, name_prefix: str):
    # calling add_schedule before checking if the thremostat template already exists only to have the schedule name to create thermostat template idf name,
    # which must be different in case different schedules for different zones shall be used...
    heating_sched_idf_name = idf_writing_helpers.add_schedule(idf, heating_setpoint_schedule, required_type=cesarp.common.ScheduleTypeLimits.TEMPERATURE())
    cooling_sched_idf_name = idf_writing_helpers.add_schedule(idf, cooling_setpoint_schedule, required_type=cesarp.common.ScheduleTypeLimits.TEMPERATURE())
    name = name_prefix + "_" + idf_strings.CustomObjNames.thermostat_template
    idf_obj_type = idf_strings.IDFObjects.hvac_template_thermostat
    if not idf_writing_helpers.exists_in_idf(idf, idf_obj_type, name):
        templ_thermostat_idf_obj = idf.newidfobject(idf_obj_type)
        templ_thermostat_idf_obj.Name = name
        templ_thermostat_idf_obj.Heating_Setpoint_Schedule_Name = heating_sched_idf_name
        templ_thermostat_idf_obj.Cooling_Setpoint_Schedule_Name = cooling_sched_idf_name
        templ_thermostat_idf_obj.Constant_Cooling_Setpoint = ""

    return name


def add_zone_infiltration(idf, zone_idf_obj_name, infiltration_rate, infiltration_profile, ureg):
    infiltration_idf_obj = idf.newidfobject(idf_strings.IDFObjects.zone_infiltration_design_flow_rate)
    infiltration_idf_obj.Name = idf_strings.CustomObjNames.zone_infiltration.format(zone_idf_obj_name)
    infiltration_idf_obj.Zone_or_ZoneList_Name = zone_idf_obj_name
    infiltration_schedule_name = idf_writing_helpers.add_schedule(idf, infiltration_profile, required_type=cesarp.common.ScheduleTypeLimits.FRACTION())
    infiltration_idf_obj.Schedule_Name = infiltration_schedule_name
    try:
        infiltration_idf_obj.Design_Flow_Rate_Calculation_Method = idf_strings.FlowRateCalculationMethod.air_changes_per_hour
        infiltration_idf_obj.Air_Changes_per_Hour = infiltration_rate.to(ureg.ACH).m
    except DimensionalityError:
        try:
            infiltration_idf_obj.Design_Flow_Rate_Calculation_Method = idf_strings.FlowRateCalculationMethod.flow_per_zone_area
            infiltration_idf_obj.Flow_per_Zone_Floor_Area = infiltration_rate.to(ureg.m ** 3 / ureg.s / ureg.m ** 2).m
        except DimensionalityError:
            raise Exception(f"infiltration rate should be in ACH or m3/s/m2 but was {str(infiltration_rate)}")
