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
from enum import Enum

autocalculate = "autocalculate"
version = "VERSION,{};"
no = "No"
yes = "Yes"
select_all = "*"
months = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]

# available pre-configured gas types for windows
win_gas_types = ["Air", "Argon", "Krypton", "Xenon"]


class Roughness(Enum):
    """the integer values have no speical meaning"""

    VeryRough = 1
    Rough = 2
    MediumRough = 3
    MediumSmooth = 4
    Smooth = 5
    VerySmooth = 6


class WindowMatGlazing:
    optical_data_type = "SpectralAverage"


class ViewFactorToGround(Enum):
    "integer values are the values to be set in the IDF as view factor to ground"
    adjacent = 0
    horizontal_up = 0
    horizontal_down = 1
    indoors = 0
    autocalculate = autocalculate


class SummaryReports:
    all_summary = "AllSummary"


class Weekdays:
    sunday = "Sunday"


class UnitConversion:
    j_to_kwh = "JtoKWH"


class ColumnSeparator:
    comma_and_html = "CommaAndHTML"


class KeyField:
    idf = "IDF"


class Coords:
    xcoordinate_pattern = "Vertex_{}_Xcoordinate"
    ycoordinate_pattern = "Vertex_{}_Ycoordinate"
    zcoordinate_pattern = "Vertex_{}_Zcoordinate"
    num_format = "{:.5f}"


# https://bigladdersoftware.com/epx/docs/8-0/input-output-reference/page-088.html#outputmeter-and-outputmetermeterfileonly
class ResultsFrequency(Enum):
    ANNUAL = "RunPeriod"
    MONTHLY = "Monthly"
    DAILY = "Daily"
    HOURLY = "Hourly"
    TIMESTEP = "Timestep"
    DETAILED = "Detailed"


class IDFObjects:
    bldg_surface_detailed = "BuildingSurface:Detailed".upper()
    fenestration_surface_detailed = "FenestrationSurface:Detailed".upper()
    zoneinfiltration_designflowrate = "ZoneInfiltration:DesignFlowRate".upper()
    hvac_template_zone_idealloadsairsystem = "HVACTemplate:Zone:IdealLoadsAirSystem".upper()
    desing_specifiction_outdoorair = "DesignSpecification:OutdoorAir".upper()
    zone = "Zone".upper()
    window_property_frame_and_divider = "WindowProperty:FrameAndDivider".upper()
    building = "Building".upper()
    global_geometry_rules = "GLOBALGEOMETRYRULES".upper()
    run_period = "RunPeriod".upper()
    simulation_control = "SimulationControl".upper()
    shading_bldg_detailed = "Shading:Building:Detailed".upper()
    shading_prop_reflectance = "ShadingProperty:Reflectance".upper()
    output_table_summary_reports = "Output:Table:SummaryReports".upper()
    output_control_table_style = "OutputControl:Table:Style".upper()
    output_meter = "Output:Meter".upper()
    output_variable = "Output:Variable".upper()
    output_variable_dictionary = "Output:VariableDictionary".upper()
    zone_infiltration_design_flow_rate = "ZoneInfiltration:DesignFlowRate".upper()
    schedule_file = "Schedule:File".upper()
    schedule_const = "Schedule:Constant".upper()
    schedule_compact = "Schedule:Compact".upper()
    schedule_type_limits = "ScheduleTypeLimits".upper()
    people = "PEOPLE".upper()
    hot_water_equipment = "HotWaterEquipment".upper()
    ligths = "Lights".upper()
    electric_equipment = "ElectricEquipment".upper()
    hvac_template_thermostat = "HVACTemplate:Thermostat".upper()
    design_specifictaion_outdoor_air = "DesignSpecification:OutdoorAir".upper()
    shadow_calculation = "ShadowCalculation".upper()
    zone_air_heat_balance_algorithm = "ZoneAirHeatBalanceAlgorithm"
    timestep = "Timestep".upper()
    convergence_limits = "ConvergenceLimits".upper()
    site_ground_temperature_building_surface = "Site:GroundTemperature:BuildingSurface".upper()
    site_ground_temperature_fc_factor_method = "Site:GroundTemperature:FCfactorMethod".upper()
    site_ground_temperature_shallow = "Site:GroundTemperature:Shallow".upper()
    site_ground_temperature_deep = "Site:GroundTemperature:Deep".upper()
    construction = "Construction".upper()
    material = "Material".upper()
    material_no_mass = "Material:NoMass".upper()
    material_air_gap = "Material:AirGap".upper()
    win_material_glazing = "WindowMaterial:Glazing".upper()
    win_material_gas = "WindowMaterial:Gas".upper()
    win_shading_ctrl_ep8 = "WindowProperty:ShadingControl".upper()
    win_shading_ctrl_ep9 = "WindowShadingControl".upper()
    win_shade_material = "WindowMaterial:Shade".upper()


class GroundTempFieldNamePatterns:
    building_surface = "{}_Ground_Temperature"
    fcfactormethod = "{}_Ground_Temperature"
    shallow = "{}_Surface_Ground_Temperature"
    deep = "{}_Deep_Ground_Temperature"


class ZoneAirHeatBalanceAlgorithm:
    analytical_solution = "AnalyticalSolution"


class NumOfPeopleCalc:
    area_per_person = "Area/Person"


class DesignLevelCalc:
    watts_per_area = "Watts/Area"


class Separator:
    comma = "Comma"
    semicolon = "Semicolon"
    tab = "Tab"

    @staticmethod
    def get_for_char(separator_char):
        if "," == separator_char:
            return Separator.comma
        if ";" == separator_char:
            return Separator.semicolon
        if "\t" == separator_char:
            return Separator.tab
        else:
            raise Exception(f'idf supports as separator char "," or ";" or "\t" (Tab), but {separator_char} was given')


class NumericType:
    continuous = "CONTINUOUS"
    discrete = "DISCRETE"

    @staticmethod
    def get_num_type_for(py_type):
        if py_type == float:
            return NumericType.continuous
        if py_type == int:
            return NumericType.discrete
        raise Exception(f"no matching NumericType for {str(py_type)}")


class WeahterCond:
    sun_exposed = "SunExposed"
    not_sun_exposed = "NoSun"
    wind_exposed = "WindExposed"
    not_wind_exposed = "NoWind"


class OutsideBoundaryCond:
    outdoors = "Outdoors"
    adiabatic = "Adiabatic"
    ground = "Ground"
    surface = "Surface"


class FenestrationSurfaceType:
    window = "Window"


class VertexPosition:
    lower_left_corner = "LowerLeftCorner"


class VertexEntryDirection:
    counter_clockwise = "CounterClockWise"


class CoordinateSystem:
    relative = "Relative"


class BldgSurfaceType:
    wall = "Wall"
    floor = "Floor"
    ceiling = "Ceiling"
    roof = "Roof"


class CustomObjNames:
    bldg_zone_name = "ZoneFloor{}"
    wall_name = "{}_Wall_{}"
    window_name = "{}_Win"
    groundfloor_name = "{}_GroundFloor"
    floor_name = "{}_Floor"
    ceiling_name = "{}_Ceiling"
    roof_name = "{}_Roof"
    building = "Building"
    run_periods = "DefaultRunPeriod"
    frame_and_divider = "1"
    shading_bldg_wall_name = "Ext{}_Wall{}"
    shading_bldg_roof_name = "Ext{}_Roof"
    zone_infiltration = "{}_Infiltration"
    people = "{}_People"
    lights = "{}_Lights"
    electric_equipment = "{}_Appliances"
    hot_water_equipment = "{}_DHW"
    thermostat_template = "Residential_thermostat"
    outdoor_air_spec = "Residential_outdoorair"
    constant_schedule = "Constant_{}"


class HVACOutdoorAirMethod:
    detailed_specification = "DetailedSpecification"


class OutdoorAirCalcMethod:
    flow_per_area = "Flow/Area"


class FlowRateCalculationMethod:
    air_changes_per_hour = "AirChanges/Hour"
    flow_per_zone_area = "Flow/Area"
