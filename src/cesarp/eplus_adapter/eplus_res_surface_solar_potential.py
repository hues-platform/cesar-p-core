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

import pandas as pd
from typing import Dict
from eppy.modeleditor import IDF
from cesarp.eplus_adapter.eplus_sim_runner import get_idd_path
from cesarp.eplus_adapter.eplus_eso_results_handling import collect_multi_entry_annual_result


COL_SURFACE_NAME = "name"
DETAILED_BUILDING_SURFACE_IDF_TAG = "BUILDINGSURFACE:DETAILED"
INCIDENT_SOLAR_VAR = "Surface Outside Face Incident Solar Radiation Rate per Area"
COL_AZIMUTH = "azimuth"
COL_TILT = "tilt"
COL_SUN_EXPLOSURE = "sun_exposure"
COL_AREA = "area"


def solar_potential_for_building(idf_path: str, single_result_folder: str) -> pd.DataFrame:
    """
    This function collects aggregates the solar exposure and the area of the sun exposed surfaces of a simulated
    building. The results are aggregated per cardinal orientation (N,E,S,W) and horizontal (H)
    This method requires the annual "Surface Outside Face Incident Solar Radiation Rate per Area" solar
    variable to added to the project yaml config under EPLUS_ADAPTER: OUTPUT_VARS: ANNUAL: when generating the idf files.
    :param idf_path: This is the folder containing the idf file of the building.
    :param single_result_folder: This is the folder containing the .eso energy plus results (eplus_output).
    :return: A data frame with the solar potential for each orientation. Index is numeric, columns are "cardinal_orientation", "insolation_kwh", "area".
             The returned dataframe has a multi-level column index (names: cardinal_orientation, None),
             to remove the 2nd level only stating "sum" for all columns use df.droplevel(1).
    """
    surfaces_df = collect_surface_geometries(idf_path)
    surfaces_dict = collect_multi_entry_annual_result(single_result_folder, INCIDENT_SOLAR_VAR)
    surface_insolation_df = solar_potential_aggregation(surfaces_df, surfaces_dict)
    return surface_insolation_df


def collect_surface_geometries(idf_path: str) -> pd.DataFrame:

    idd_path = get_idd_path()
    IDF.setiddname(idd_path)
    idf = IDF(str(idf_path))

    detailed_surfaces = idf.idfobjects[DETAILED_BUILDING_SURFACE_IDF_TAG]

    srf_names = [x.Name.upper() for x in detailed_surfaces]
    srf_azis = [x.azimuth for x in detailed_surfaces]
    srf_tilts = [x.tilt for x in detailed_surfaces]
    srf_areas = [x.area for x in detailed_surfaces]
    srf_sun_expos = [x.Sun_Exposure for x in detailed_surfaces]

    surface_data = {COL_SURFACE_NAME: srf_names, COL_AZIMUTH: srf_azis, COL_TILT: srf_tilts, COL_SUN_EXPLOSURE: srf_sun_expos, COL_AREA: srf_areas}

    surface_df = pd.DataFrame(surface_data)

    return surface_df


def calculate_cardinal(azimuth: int) -> str:
    if azimuth > 315:
        letter = "N"
    elif azimuth > 225:
        letter = "W"
    elif azimuth > 135:
        letter = "S"
    elif azimuth > 45:
        letter = "E"
    else:
        letter = "N"
    return letter


def solar_potential_aggregation(surface_df: pd.DataFrame, radiation_dict: Dict[str, float]) -> pd.DataFrame:

    surface_df = surface_df.loc[surface_df["sun_exposure"] == "SunExposed"]

    surface_df["annual_average_radiation_w_m2"] = surface_df["name"].map(radiation_dict)

    surface_df["annual_insolation_kwh_m2"] = surface_df["annual_average_radiation_w_m2"] * 8760 / 1000

    surface_df["insolation_kwh"] = surface_df["annual_insolation_kwh_m2"] * surface_df["area"]

    surface_df["cardinal_orientation"] = surface_df["azimuth"].apply(lambda x: calculate_cardinal(x))

    surface_df.loc[(surface_df["tilt"] == 0) | (surface_df["tilt"] == 180), "cardinal_orientation"] = "H"

    total_insolation = surface_df.groupby(["cardinal_orientation"]).agg({"insolation_kwh": ["sum"], "area": ["sum"]}).reset_index()

    return total_insolation
