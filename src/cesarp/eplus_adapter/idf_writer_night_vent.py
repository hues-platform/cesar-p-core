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
import cesarp.common
from eppy.modeleditor import IDF
from cesarp.eplus_adapter import idf_strings
from cesarp.model.BuildingOperation import NightVent
from cesarp.eplus_adapter.idf_writing_helpers import add_schedule, add_type_limits, exists_in_idf


def add_night_ventilation_for_zone(idf: IDF, idf_zone_name: str, night_vent_model: NightVent):
    """
    For description of model used for night ventilation please refer to docs/features/passive-cooling.rst.

    :param idf: eppy IDF object for which to add shading. Zones must already be defined in passed IDF object!
    :param idf_zone_name: zone name in idf for which to add night ventilation
    :param night_vent_model: parameters for the night ventilation
    :return: nothing, idf is extended in place
    """

    max_temp_profile_idf_name = add_schedule(idf, night_vent_model.maximum_indoor_temp_profile, required_type=cesarp.common.ScheduleTypeLimits.TEMPERATURE())
    night_vent_schedule_name = _adding_the_schedule(idf, night_vent_model.start_hour, night_vent_model.end_hour)

    night_vent_obj = idf.newidfobject("ZoneVentilation:DesignFlowRate")
    night_vent_obj.Name = idf_zone_name + "_night_vent"
    night_vent_obj.Zone_or_ZoneList_Name = idf_zone_name
    night_vent_obj.Schedule_Name = night_vent_schedule_name
    night_vent_obj.Design_Flow_Rate_Calculation_Method = idf_strings.FlowRateCalculationMethod.air_changes_per_hour
    night_vent_obj.Air_Changes_per_Hour = night_vent_model.flow_rate.to("ACH").m
    night_vent_obj.Ventilation_Type = "Natural"
    night_vent_obj.Minimum_Indoor_Temperature = night_vent_model.min_indoor_temperature.to("degreeC").m
    night_vent_obj.Maximum_Indoor_Temperature_Schedule_Name = max_temp_profile_idf_name
    night_vent_obj.Delta_Temperature = night_vent_model.maximum_in_out_deltaT.to("degreeC").m
    night_vent_obj.Maximum_Wind_Speed = night_vent_model.max_wind_speed.to("m/s").m


def _adding_the_schedule(idf: IDF, start_hour: str, end_hour: str):
    schedule_name = "night_vent_schedule"
    if not exists_in_idf(idf, idf_strings.IDFObjects.schedule_compact, schedule_name):
        idf_type_lim_name = add_type_limits(idf, cesarp.common.ScheduleTypeLimits.FRACTION())
        schedule_night_vent_obj = idf.newidfobject(idf_strings.IDFObjects.schedule_compact)
        schedule_night_vent_obj.Name = schedule_name
        schedule_night_vent_obj.Schedule_Type_Limits_Name = idf_type_lim_name

        schedule_night_vent_obj.Field_1 = "Through: 12 / 31"
        schedule_night_vent_obj.Field_2 = "For: AllDays"
        schedule_night_vent_obj.Field_3 = "Until: " + end_hour
        schedule_night_vent_obj.Field_4 = 1
        schedule_night_vent_obj.Field_5 = "until: " + start_hour
        schedule_night_vent_obj.Field_6 = 0
        schedule_night_vent_obj.Field_7 = "until: " + "24:00"
        schedule_night_vent_obj.Field_8 = 1
    return schedule_name
