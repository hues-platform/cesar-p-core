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
from typing import Any, List
from eppy.modeleditor import IDF
from eppy.bunch_subclass import EpBunch
from cesarp.eplus_adapter import idf_writing_helpers, idf_strings
from cesarp.model.BuildingOperation import WindowShadingControl
from cesarp.model.WindowConstruction import WindowShadingMaterial


SHADE_CTRL_IDF_NAME_PREFIX = "shade_control"


def add_shading_on_windows(idf: IDF, zone_name: str, windows_in_zone: List[EpBunch], shading_ctrl_model: WindowShadingControl, shading_mat: WindowShadingMaterial):
    """
    For description of model used for window shading please refer to docs/features/passive-cooling.rst.

     Adds shading device and control for all windows on all floors, if windows shading material is defined and control is active

     Created IDF structure depends on EnergyPlus version.

     :param idf: eppy IDF object for which to add shading. Expects windows to be defined!
     :param zone_name: the idf zone name for which to add window shading
     :param windows_in_zone: list of all window idf objects for that zone
     :param shading_ctrl_model: control/operational parameters for the window shade
     :param shading_mat: material parameters for the window shade
     :return: nothing, idf is extended in place
    """
    if shading_ctrl_model.is_active and shading_mat.is_shading_available:
        if idf.idd_version[0] < 9:
            _add_shading_on_windows_EP8(idf, zone_name, windows_in_zone, shading_ctrl_model, shading_mat)
        else:
            _add_shading_on_windows_EP9(idf, zone_name, windows_in_zone, shading_ctrl_model, shading_mat)


def _add_shading_on_windows_EP8(idf: IDF, zone_name: str, windows_in_zone: List[EpBunch], shading_ctrl_model: WindowShadingControl, shading_mat: WindowShadingMaterial):
    shade_mat_idf_name = _add_shading_mat(idf, shading_mat)
    shd_ctrl_idf_name = _add_shading_control_EP8(idf, SHADE_CTRL_IDF_NAME_PREFIX, shade_mat_idf_name, shading_ctrl_model)
    for window in windows_in_zone:
        window.Shading_Control_Name = shd_ctrl_idf_name


def _add_shading_on_windows_EP9(idf: IDF, zone_name: str, windows_in_zone: List[EpBunch], shading_ctrl_model: WindowShadingControl, shading_mat: WindowShadingMaterial):
    shade_mat_idf_name = _add_shading_mat(idf, shading_mat)
    _add_shading_control_EP9(idf, SHADE_CTRL_IDF_NAME_PREFIX + "_" + zone_name, shade_mat_idf_name, zone_name, windows_in_zone, shading_ctrl_model)


def _add_shading_mat(idf, shading_mat_model: WindowShadingMaterial):
    shade_mat_idf_name = shading_mat_model.name
    if not idf_writing_helpers.exists_in_idf(idf, idf_strings.IDFObjects.win_shade_material, shade_mat_idf_name):
        window_shading_mat = idf.newidfobject(idf_strings.IDFObjects.win_shade_material)
        window_shading_mat.Name = shade_mat_idf_name
        window_shading_mat.Solar_Transmittance = shading_mat_model.solar_transmittance.to("solar_transmittance").m
        window_shading_mat.Solar_Reflectance = shading_mat_model.solar_reflectance.to("solar_reflectance").m
        window_shading_mat.Visible_Transmittance = shading_mat_model.visible_transmittance.to("visible_transmittance").m
        window_shading_mat.Visible_Reflectance = shading_mat_model.visible_reflectance.to("visible_reflectance").m
        window_shading_mat.Infrared_Hemispherical_Emissivity = shading_mat_model.infrared_hemispherical_emissivity.to("infrared_hemispherical_emissivity").m
        window_shading_mat.Infrared_Transmittance = shading_mat_model.infrared_transmittance.to("infrared_transmittance").m
        window_shading_mat.Thickness = shading_mat_model.thickness.to("m").m
        window_shading_mat.Conductivity = shading_mat_model.conductivity.to("W/(m*K)").m
        window_shading_mat.Shade_to_Glass_Distance = shading_mat_model.shade_to_glass_distance.to("m").m
        window_shading_mat.Top_Opening_Multiplier = shading_mat_model.top_opening_multiplier
        window_shading_mat.Bottom_Opening_Multiplier = shading_mat_model.bottom_opening_multiplier
        window_shading_mat.LeftSide_Opening_Multiplier = shading_mat_model.leftside_opening_multiplier
        window_shading_mat.RightSide_Opening_Multiplier = shading_mat_model.rightside_opening_multiplier
        window_shading_mat.Airflow_Permeability = shading_mat_model.airflow_permeability
    return shade_mat_idf_name


def _add_shading_control_EP9(
    idf: IDF, shade_ctrl_idf_name: str, shade_mat_idf_name: str, zone_idf_name: str, windows_in_zone: List[Any], shading_ctrl_model: WindowShadingControl
) -> str:
    window_shading_control = idf.newidfobject(idf_strings.IDFObjects.win_shading_ctrl_ep9)
    window_shading_control.Name = shade_ctrl_idf_name
    window_shading_control.Zone_Name = zone_idf_name
    window_shading_control.Shading_Type = _get_shading_type_str(shading_ctrl_model.is_exterior)
    window_shading_control.Shading_Control_Type = shading_ctrl_model.shading_control_type
    window_shading_control.Setpoint = shading_ctrl_model.radiation_min_setpoint.to("W/m2").m
    window_shading_control.Shading_Device_Material_Name = shade_mat_idf_name
    for i, window in enumerate(windows_in_zone, start=1):
        setattr(window_shading_control, "Fenestration_Surface_{}_Name".format(i), window.Name)
    return shade_ctrl_idf_name


def _add_shading_control_EP8(idf: IDF, shade_ctrl_idf_name: str, shade_mat_idf_name: str, shading_ctrl_model: WindowShadingControl) -> str:
    if not idf_writing_helpers.exists_in_idf(idf, idf_strings.IDFObjects.win_shading_ctrl_ep8, shade_ctrl_idf_name):
        window_shading_control = idf.newidfobject(idf_strings.IDFObjects.win_shading_ctrl_ep8)
        window_shading_control.Name = shade_ctrl_idf_name
        window_shading_control.Shading_Type = _get_shading_type_str(shading_ctrl_model.is_exterior)
        window_shading_control.Shading_Control_Type = shading_ctrl_model.shading_control_type
        window_shading_control.Setpoint = shading_ctrl_model.radiation_min_setpoint.to("W/m2").m
        window_shading_control.Shading_Device_Material_Name = shade_mat_idf_name
        # energy plus complains about undefined Slat_Angle_Schedule_Name if not explizit set here (eppy does not put it by default)
        # Type_of_Slat_Angle_Control_for_Blinds and Slat_Angle_Schedule_Name are set to their default values
        window_shading_control.Type_of_Slat_Angle_Control_for_Blinds = "FixedSlatAngle"
        window_shading_control.Slat_Angle_Schedule_Name = ""
    return shade_ctrl_idf_name


def _get_shading_type_str(is_exterior: bool):
    return "ExteriorShade" if is_exterior else "InteriorShade"
