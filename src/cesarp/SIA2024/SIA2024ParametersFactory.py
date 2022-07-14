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
from typing import List, Protocol
from enum import Enum

import cesarp.common.csv_writer
import cesarp.common
from cesarp.SIA2024.SIA2024DataAccessor import SIA2024DataAccessor
from cesarp.SIA2024.demand_generators.OccupancyProfileGenerator import OccupancyProfileGenerator
from cesarp.SIA2024.demand_generators.AreaPerPersonCalculator import AreaPerPersonCalculator
from cesarp.SIA2024.demand_generators.ActivityHeatGainCalculator import ActivityHeatGainCalculator
from cesarp.SIA2024.demand_generators.AppliancesDemandGenerator import AppliancesDemandGenerator
from cesarp.SIA2024.demand_generators.DHWDemandGenerator import DHWDemandGenerator
from cesarp.SIA2024.demand_generators.DHWDemandBasedOnLiterPerDayGenerator import DHWDemandBasedOnLiterPerDayGenerator
from cesarp.SIA2024.demand_generators.InfiltrationRateGenerator import InfiltrationRateGenerator
from cesarp.SIA2024.demand_generators.LightingDemandGenerator import LightingDemandGenerator
from cesarp.SIA2024.demand_generators.NighttimePatternGenerator import NighttimePatternGenerator
from cesarp.SIA2024.demand_generators.ThermostatDemandGenerator import ThermostatDemandGenerator
from cesarp.SIA2024.demand_generators.VentilationDemandGenerator import VentilationDemandGenerator
from cesarp.SIA2024.demand_generators.VariationMonthly import VariationMonthly
from cesarp.SIA2024 import _default_config_file
from cesarp.SIA2024.SIA2024Parameters import SIA2024Parameters


class DHWDemandProtocol(Protocol):
    def get_dhw_power_per_area_for_bldg(self) -> float:
        """
        :return: electricity demand for dhw in W/m2 aggregated for the building
        """
        ...

    def get_dhw_profile_for_bldg(self) -> List[float]:
        """
        Domestic hot water usage profile aggreagted for the building
        :return: year profile defining hourly fraction of full load dhw demand [0...1]
        """
        ...


class SIA2024ParametersFactory:
    """
    Creates a set of operation demand profiles and values (without passive cooling aspects) as well as infiltration properties based on SIA2024 derived base data.
    Base data can be defined by passing an instance to a data accessor (sia_base_data), which should implement all methods defined in the BaseDataXXXProtocol of
    the different generators in sub-package demand_generators.

    For variability, generally a triangular distribution was used whenever a minimum, standard and maximum (resp. Zielwert, Standard, Bestand) is given by SIA2024, otherwise a standard distrubution is used.
    Thermostat variability: with SIA2024-2006 there was a min/max given for thermostat setpoint, thus a triangular distribution was used. In SIA2024-2016 those values are not given anymore and
    according to literature research more often a standard distribution is used for thermostat setpoint, so with SIA2024-2016 demand values generation a standard distribution was used.
    Heat gain by people activity: No variability for the activity heat gain, as uncertainty is quite small (people do no sports in their home or the like, which would give much more heat gain).
    For more details about how the variability is introduced and the used distributions please refer to the PhD thesis from George Mavromatidis
    and the review paper "A review of uncertainty characterisation approaches for the optimal design of distributed energy systems", https://doi.org/10.1016/j.rser.2018.02.021
    You can configure details of variability bandwith etc in the package configuration, sia2024_default_config.yml.

    For detailed settings on the variability (e.g. variability bands) please have a look at the package configuration file, sia2024_default_config.yml.
    """

    __VARIABILITY_SETTINGS_KEY = "VARIABILITY_SETTINGS"
    __DHW_BASED_ON_LITER_PER_DAY_KEY = "DHW_BASED_ON_LITER_PER_DAY"

    def __init__(self, sia_base_data: SIA2024DataAccessor, ureg, custom_config=None):
        """
        Initialization

        :param sia_base_data: object providing the base data for creating the parameter sets.
        :param ureg: unit registry instance
        :param custom_config: custom configuration parameters
        """
        cfg = cesarp.common.config_loader.load_config_for_package(_default_config_file, __package__, custom_config)
        self._cfg = cfg
        self._cfg_variability = cfg["PROFILE_GENERATION"][self.__VARIABILITY_SETTINGS_KEY]
        self.sia_base_data = sia_base_data
        self.ureg = ureg
        self.profile_files_nr_counter = 0
        self.data_descr = sia_base_data.data_source
        base_data_descr = ""
        if self.data_descr.DESCRIPTION is not None:
            base_data_descr = f"Base data description: {self.data_descr.DESCRIPTION}.\n"
        self.data_descr.DESCRIPTION = (
            f"{base_data_descr}All parameters and profiles in this data set are derived from the described source by {cesarp.common.get_fully_qualified_classname(self)}"
        )
        self.data_descr.CONFIG_ENTRIES.update({self.__VARIABILITY_SETTINGS_KEY: self._cfg_variability})

    def get_sia2024_parameters(self, bldg_type_key: Enum, variability_active: bool, name: str = None):
        """
        Creates one SIA2024 parameter set for teh given building type, with variability or nominal

        :param bldg_type_key: building type for which to create the parameter set, the Enum is dynamically loaded in the data accessor (e.g. SIA2024DataAccessor)
        :type bldg_type_key: SIA2024BldgTypeKeys (defined as Enum to satisfy protocol definition)
        :param variability_active:
        :param name: name for this parameter set, if None bldg_type_key is used
        :return: parameter set as object of type SIA2024Parameters
        """
        if not name:
            name = bldg_type_key.name
        if variability_active:
            vertical_var_band = self._cfg_variability["VERTICAL_VARIABILITY_FRACTION_PROFILES"]
        else:
            vertical_var_band = 0
        bldg_type = self.sia_base_data.get_bldg_type(bldg_type_key)
        nighttime_pattern_gen = NighttimePatternGenerator(self.sia_base_data)
        nighttime_pattern_profile = nighttime_pattern_gen.get_nighttime_year_profile_hourly()
        if variability_active:
            nighttime_pattern_gen.activate_variability(variability_band=self._cfg_variability["DAILY_ROUTINE_VARIABILITY"])
        monthly_variation = VariationMonthly(bldg_type, self.sia_base_data, vertical_variability=vertical_var_band)
        area_pp_gen = AreaPerPersonCalculator(bldg_type, self.sia_base_data, area_pp_variability=variability_active)
        profile_start_date = self._cfg["PROFILE_GENERATION"]["PROFILE_SETTINGS"]["START_DATE"]
        occ_prof_gen = OccupancyProfileGenerator(
            bldg_type=bldg_type,
            base_data=self.sia_base_data,
            nighttime_pattern_year_profile_bldg_hourly=nighttime_pattern_profile,
            get_year_profile_variation_monthly_for_room_method=monthly_variation.get_monthly_variation_per_room,
            profile_start_date=profile_start_date,
        )
        if variability_active:
            occ_prof_gen.activate_profile_variability(
                vertical_variability=self._cfg_variability["VERTICAL_VARIABILITY_FRACTION_PROFILES"],
                do_horizontal_variability=self._cfg_variability["DO_HORIZONTAL_VARIABILTY"],
            )

        sia2024params = SIA2024Parameters.emptyObj()
        sia2024params.data_descr = self.data_descr
        sia2024params.name = name
        self.__add_building_operation(sia2024params, area_pp_gen, bldg_type, monthly_variation, nighttime_pattern_profile, occ_prof_gen, variability_active, profile_start_date)
        self.__add_hvac(sia2024params, bldg_type, nighttime_pattern_profile, occ_prof_gen, area_pp_gen, variability_active)
        self.__add_infiltration(sia2024params, bldg_type, variability_active)
        self.profile_files_nr_counter += 1

        return sia2024params

    def is_building_type_residential(self, bldg_type_key):
        """
        Check wether the given building type is residential or not

        :param bldg_type_key: building type as Enum (Enum type is dynamically loaded in SIA2024DataAccessor)
        :return: true if the building type is residential
        """
        return self.sia_base_data.get_bldg_type(bldg_type_key).is_residential

    def __add_building_operation(
        self, sia2024params, area_pp_gen, bldg_type, monthly_variation, nighttime_pattern_profile, occ_prof_gen, variability_active: bool, profile_start_date
    ):
        activity_gen = ActivityHeatGainCalculator(bldg_type, self.sia_base_data, self.ureg)  # activity has no variability option

        appliance_gen = AppliancesDemandGenerator(bldg_type, self.sia_base_data, monthly_variation.get_monthly_variation_per_room, profile_start_date)
        if variability_active:
            appliance_gen.activate_profile_variability(
                self._cfg_variability["VERTICAL_VARIABILITY_FRACTION_PROFILES"],
                self._cfg_variability["DO_HORIZONTAL_VARIABILTY"],
            )
            appliance_gen.activate_appliance_level_variability()

        lighting_gen = LightingDemandGenerator(bldg_type, self.sia_base_data)
        if variability_active:
            lighting_gen.activate_lighting_density_variability()
            var_prc = self.ureg(self._cfg_variability["LIGHTING_SETPOINT_VARIABILITY_PRC"])
            assert var_prc.u == self.ureg.dimensionless, f"unit of LIGHTING_SETPOINT_VARIABILITY_PRC must be dimensionless, but is {var_prc.u}"
            lighting_gen.activate_lighting_setpoint_variability(var_prc.m)

        cfg_dhw_based_on_lpd = self._cfg["PROFILE_GENERATION"][self.__DHW_BASED_ON_LITER_PER_DAY_KEY]
        if cfg_dhw_based_on_lpd["ACTIVE"]:
            dhw_gen: DHWDemandProtocol = DHWDemandBasedOnLiterPerDayGenerator(
                bldg_type,
                self.sia_base_data,
                variability_active,
                self.ureg(cfg_dhw_based_on_lpd["NOMINAL_TEMPERATURE"]),
                self.ureg(cfg_dhw_based_on_lpd["COLD_WATER_TEMPERATURE"]),
                occ_prof_gen.get_occupancy_profile_for_room_method,
                nighttime_pattern_profile,
                monthly_variation.get_monthly_variation_per_room,
                self.ureg,
            )

        else:
            dhw_gen = DHWDemandGenerator(
                bldg_type,
                self.sia_base_data,
                variability_active,
                occ_prof_gen.get_occupancy_profile_for_room_method,
                nighttime_pattern_profile,
            )

        area_pp_bldg = area_pp_gen.get_area_pp_for_bldg()
        occ_profile = occ_prof_gen.get_occupancy_profile_for_bldg(area_pp_bldg, area_pp_gen.get_area_pp_for_room)
        activity_prof = activity_gen.get_activity_heat_gain_profile_for_bldg()
        appliance_prof = appliance_gen.get_appliance_profile_for_bldg()
        appliance_level = appliance_gen.get_appliance_level_for_bldg()
        lighting_dens_prof = lighting_gen.get_lighting_density_profile_for_bldg(
            occ_prof_gen.get_occupancy_profile_for_room_method,
            nighttime_pattern_profile,
            monthly_variation.get_monthly_variation_per_room,
        )
        lighting_dens = lighting_gen.get_lighting_density_for_bldg()
        dhw_demand = dhw_gen.get_dhw_power_per_area_for_bldg()
        dhw_profile = dhw_gen.get_dhw_profile_for_bldg()

        sia2024params.occupancy_fraction_schedule = self._wrap_profile(occ_profile)
        sia2024params.activity_schedule = self._wrap_profile(activity_prof)
        sia2024params.floor_area_per_person = area_pp_bldg
        sia2024params.electric_appliances_fraction_schedule = self._wrap_profile(appliance_prof)
        sia2024params.electric_appliances_power_demand = appliance_level
        sia2024params.lighting_fraction_schedule = self._wrap_profile(lighting_dens_prof)
        sia2024params.lighting_power_demand = lighting_dens
        sia2024params.dhw_fraction_schedule = self._wrap_profile(dhw_profile)
        sia2024params.dhw_power_demand = dhw_demand

    def __add_hvac(self, sia2024params, bldg_type, nighttime_pattern_profile, occ_prof_gen, area_pp_gen, variability_active: bool):
        var_band_setpoint = None
        if variability_active:
            var_band_setpoint = self.ureg(self._cfg_variability["VERTICAL_VARIABILITY_THERMOSTAT_SETPOINT"])

        thermostat_gen = ThermostatDemandGenerator(bldg_type, self.sia_base_data, var_band_setpoint)
        (heating_prof, cooling_prof) = thermostat_gen.get_thermostat_profiles_for_bldg(occ_prof_gen.get_occupancy_profile_for_room_method, nighttime_pattern_profile)

        ventilation_gen = VentilationDemandGenerator(bldg_type, self.sia_base_data, variability_active, area_pp_gen.get_area_pp_for_room)
        ventilation_prof = ventilation_gen.get_yearly_ventilation_profile_for_bldg(occ_prof_gen.get_occupancy_profile_for_room_method, nighttime_pattern_profile)

        sia2024params.heating_setpoint_schedule = self._wrap_profile(heating_prof)
        sia2024params.cooling_setpoint_schedule = self._wrap_profile(cooling_prof)
        sia2024params.ventilation_fraction_schedule = self._wrap_profile(ventilation_prof)
        sia2024params.ventilation_outdoor_air_flow = ventilation_gen.get_ventilation_rate_for_bldg()

    def __add_infiltration(self, sia2024params, bldg_type, variability_active: bool):
        inf_gen = InfiltrationRateGenerator(bldg_type, self.sia_base_data)
        if variability_active:
            var_prc = self.ureg(self._cfg_variability["INFILTRATION_RATE_VARIABILITY_PRC"])
            assert var_prc.u == self.ureg.dimensionless, f"unit of INFILTRATION_RATE_VARIABILITY_FRACTION must be dimensionless, but is {var_prc.u}"
            inf_gen.activate_infiltrat_rate_variability(var_prc.m)
        inf_prof = inf_gen.get_infiltration_profile_for_bldg()
        infiltration_rate = inf_gen.get_infiltration_for_bldg()
        sia2024params.infiltration_rate = infiltration_rate
        sia2024params.infiltration_fraction_schedule = self._wrap_profile(inf_prof)

    def _wrap_profile(self, profile_values: List[cesarp.common.NUMERIC]):
        limits = cesarp.common.ScheduleTypeLimits.get_limits_base_on_profile(profile_values, self.ureg)
        return cesarp.common.ScheduleValues(profile_values, limits)
