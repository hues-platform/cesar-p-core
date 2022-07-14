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
from pint import Quantity
from enum import Enum
from typing import List, Dict
from pandas.io.excel._util import _range2cols
import os

from cesarp.common.CesarpException import CesarpException
import cesarp.common
from cesarp.common.DatasetMetadata import DatasetMetadata
from cesarp.SIA2024 import COL_STD, COL_MIN, COL_MAX
from cesarp.SIA2024 import _default_config_file
from cesarp.SIA2024.SIA2024_2016_RoomType import SIA2024_2016_RoomType
from cesarp.SIA2024.SIA2024BuildingType import SIA2024BuildingType, SIA2024BldgTypeKeys


class SIA2024DataAccessor:
    """
    Reads data from SIA Excel sheet and some additional values from the configuration and builindg type YAML specification (path and name defined in configuration)
    The SIA Excel sheet and building type should refer to the room types as defined in SIA2024_2016_RoomType.py.
    """

    __PROFILE_SETTINGS_KEY = "PROFILE_SETTINGS"

    def __init__(self, ureg, custom_config=None):
        self.ureg = ureg
        cfg = cesarp.common.config_loader.load_config_for_package(_default_config_file, __package__, custom_config)
        sia_sheet_cfg_file = cfg["PROFILE_GENERATION"]["SIA_SHEET_CONFIG_FILE"]
        if not os.path.isfile(sia_sheet_cfg_file):
            raise CesarpException(f"Cannot initialize SIA2024DataAccessor because configuration SIA_SHEET_CONFIG_FILE points to non-existing file {sia_sheet_cfg_file}")
        self._cfg_sia_sheet = cesarp.common.config_loader.load_config_for_package(sia_sheet_cfg_file, "cesarp.SIA2024.ressources")
        self._cfg_profiles = cfg["PROFILE_GENERATION"][self.__PROFILE_SETTINGS_KEY]
        self.__load_sia_sheet_data()
        self.data_source = self.get_data_source_description()
        bldg_types_cfg_file = cfg["PROFILE_GENERATION"]["BUILDING_TYPES_CONFIG_FILE"]
        if not os.path.isfile(bldg_types_cfg_file):
            raise CesarpException(f"Cannot initialize SIA2024DataAccessor because configuration BUILDING_TYPES_CONFIG_FILE points to non-existing file {bldg_types_cfg_file}")
        self.__bldg_type_cfg = cesarp.common.config_loader.load_config_full(bldg_types_cfg_file, ignore_metadata=True)

    def __load_sia_sheet_data(self):
        data_file = self._cfg_sia_sheet["FILE_PATH"]
        if not os.path.isfile(data_file):
            raise CesarpException(f"Cannot load SIA2024 data because file {data_file} does not exist.")
        self._raw_input_data = pd.read_excel(data_file, sheet_name=self._cfg_sia_sheet["SHEET_NAME"], header=None, index_col=self._cfg_sia_sheet["ROOM_NAME_COL"])
        str_to_enum_room_name = {room.name: room for room in SIA2024_2016_RoomType}
        self._raw_input_data.rename(index=str_to_enum_room_name, inplace=True)

        self.area_per_person_triple: pd.DataFrame = self.__extract_triple_from_raw_data(self._cfg_sia_sheet["AREA_PER_PERSON"], has_unit=True, additional_unit=1 / self.ureg.person)
        self.activity_level_per_person: pd.DataFrame = self.__extract_from_raw_data(self._cfg_sia_sheet["ACTIVITY_LEVEL_PER_PERSON"], has_unit=True)
        self.variation_year_profile_monthly_nominal: pd.DataFrame = self.__extract_from_raw_data(self._cfg_sia_sheet["MONTHLY_VARIATION_NOMINAL"])
        self.occ_day_profile_hourly_nominal: pd.DataFrame = self.__extract_from_raw_data(self._cfg_sia_sheet["DAILY_OCCUPANCY_NOMINAL"])
        self.occ_breaks: pd.DataFrame = self.__extract_array_from_raw_data(self._cfg_sia_sheet["OCCUPANCY_BREAKS"], data_type=int)
        self.occupancy_nominal_during_night: pd.DataFrame = self.__extract_from_raw_data(self._cfg_sia_sheet["IS_OCCUPANCY_NOMINAL_DURING_NIGHT"], has_unit=False)
        self.appliances_day_profile_hourly_nominal: pd.DataFrame = self.__extract_from_raw_data(self._cfg_sia_sheet["DAILY_APPLIANCES_NOMINAL"])
        self.appliances_breaks: pd.DataFrame = self.__extract_array_from_raw_data(self._cfg_sia_sheet["APPLIANCES_BREAKS"], data_type=int)
        self.appliances_level_triple: pd.DataFrame = self.__extract_triple_from_raw_data(self._cfg_sia_sheet["APPLIANCES_LEVEL"], has_unit=True)
        data_appliance_level_prc = self.__extract_from_raw_data(self._cfg_sia_sheet["APPLIANCE_LEVEL_STANDBY_PRC"], has_unit=False)
        self.appliances_level_standby_prc: pd.DataFrame = data_appliance_level_prc.apply(lambda x: x / 100 * self.ureg.dimensionless)
        self.nr_of_rest_days_per_week: pd.DataFrame = self.__extract_from_raw_data(self._cfg_sia_sheet["REST_DAYS"], has_unit=True)
        self.setpoint_heating: pd.DataFrame = self.__extract_from_raw_data(self._cfg_sia_sheet["HEATING_SETPOINT"], has_unit=True)
        self.setpoint_cooling: pd.DataFrame = self.__extract_from_raw_data(self._cfg_sia_sheet["COOLING_SETPOINT"], has_unit=True)
        self.do_setback_thermostat_when_unoccupied = self.__extract_from_raw_data(self._cfg_sia_sheet["DO_SETBACK_THERMOSTAT_WHEN_UNOCCUPIED"], has_unit=False)
        self.do_setback_thermostat_during_night = self.__extract_from_raw_data(self._cfg_sia_sheet["DO_SETBACK_THERMOSTAT_DURING_NIGHT"], has_unit=False)
        self.heating_setback: pd.DataFrame = self.__extract_from_raw_data(self._cfg_sia_sheet["HEATING_SETBACK"], has_unit=True)
        self.cooling_setback: pd.DataFrame = self.__extract_from_raw_data(self._cfg_sia_sheet["COOLING_SETBACK"], has_unit=True)
        self.ventilation_rate_per_m2_nominal = self.__extract_from_raw_data(
            self._cfg_sia_sheet["VENTILATION_RATE_PER_M2_NOMINAL"],
            has_unit=True,
            convert_to_unit=self.ureg.m ** 3 / self.ureg.seconds / self.ureg.m ** 2,
        )
        self.ventilation_rate_per_p_nominal = self.__extract_from_raw_data(
            self._cfg_sia_sheet["VENTILATION_RATE_PER_P_NOMINAL"],
            has_unit=True,
            additional_unit=1 / self.ureg.person,
            convert_to_unit=self.ureg.m ** 3 / self.ureg.seconds / self.ureg.person,
        )
        self.ventilation_rate_night_per_p_nominal = self.__extract_from_raw_data(
            self._cfg_sia_sheet["VENTILATION_RATE_NIGHT_PER_P_NOMINAL"],
            has_unit=True,
            additional_unit=1 / self.ureg.person,
            convert_to_unit=self.ureg.m ** 3 / (self.ureg.seconds * self.ureg.person),
        )
        self.dhw_power_per_area_triple = self.__extract_triple_from_raw_data(self._cfg_sia_sheet["DHW_POWER_PER_AREA"], has_unit=True)
        self.dhw_liter_per_day_pp_triple = self.__extract_triple_from_raw_data(
            self._cfg_sia_sheet["DHW_LITER_PER_DAY_PER_PERSON"], has_unit=True, additional_unit=1 / self.ureg.person
        )
        self.dhw_off_during_night = self.__extract_from_raw_data(self._cfg_sia_sheet["IS_DHW_OFF_DURING_NIGHT"], has_unit=False)
        self.lighting_follow_occupancy = self.__extract_from_raw_data(self._cfg_sia_sheet["LIGHTING_FOLLOW_OCCUPANCY"], has_unit=False)
        self.light_off_during_night = self.__extract_from_raw_data(self._cfg_sia_sheet["IS_LIGHT_OFF_DURING_NIGHT"], has_unit=False)
        self.lighting_setpoint = self.__extract_from_raw_data(self._cfg_sia_sheet["LIGHTING_SETPOINT"], has_unit=True)
        self.lighting_density_triple = self.__extract_triple_from_raw_data(self._cfg_sia_sheet["LIGHTING_DENSITY"], has_unit=True)
        self.infiltration_rate_stock = self.__extract_from_raw_data(self._cfg_sia_sheet["INFILTRATION_RATE_STOCK"], has_unit=True)

        self._raw_input_data = None  # free up memory

    def __extract_triple_from_raw_data(self, data_loc_info, has_unit=False, additional_unit=1, convert_to_unit=None) -> pd.DataFrame:
        required_columns = [COL_STD, COL_MIN, COL_MAX]
        header_mapping = data_loc_info["HEADER_LABELS"]
        assert list(header_mapping.keys()) == required_columns, f"keys of given header_mapping {list(header_mapping.keys())} do not match required ones {required_columns}"

        data = self.__extract_from_raw_data(data_loc_info, has_unit, additional_unit, convert_to_unit)

        labels_orig_to_cesar = dict([(value, key) for key, value in header_mapping.items()])  # reverse dict
        data.columns = data.columns.to_series().fillna("NoLabel")
        data = data.rename(columns=labels_orig_to_cesar, errors="raise")
        return data

    def __extract_from_raw_data(self, data_loc_info, has_unit=False, additional_unit=1, convert_to_unit=None) -> pd.DataFrame:
        header_row = data_loc_info["HEADER_ROW"] - 1
        data_start_row = self._cfg_sia_sheet["DATA_START_ROW"] - 1
        if has_unit:
            unit_row = data_loc_info["UNIT_ROW"] - 1

        col_range_data = data_loc_info["COL_RANGE"]
        required_cols_index = _range2cols(col_range_data)

        dataset = self._raw_input_data.loc[:, required_cols_index]
        header = dataset.iloc[header_row]
        dataset.rename(columns=header, inplace=True)
        if has_unit:
            units = dataset.iloc[unit_row]
        dataset = dataset.iloc[data_start_row:]

        if has_unit:
            for column in dataset:
                unit_str = units.loc[column]
                dataset[column] = dataset[column].map(lambda x: self.__convert_to_quantitiy(x, unit_str, additional_unit, convert_to_unit))
        elif additional_unit != 1:
            for column in dataset:
                dataset[column] = dataset[column].map(lambda x: x * additional_unit)
        return dataset

    def __extract_array_from_raw_data(self, data_loc_info, has_unit=False, additional_unit=1, convert_to_unit=None, data_type=str) -> pd.DataFrame:
        data = self.__extract_from_raw_data(data_loc_info, has_unit, additional_unit, convert_to_unit)
        data.iloc[:, 0] = data.iloc[:, 0].map(lambda values: [] if pd.isna(values) else [data_type(single_val) for single_val in values.split(",")])
        return data

    def __convert_to_quantitiy(self, value, unit_str, additional_unit=1, convert_to_unit=None):
        if unit_str == "%":
            return value / 100
        if unit_str in ["", " ", "-"]:
            return value
        val_with_unit = value * self.ureg(unit_str) * additional_unit
        if convert_to_unit:
            val_with_unit.ito(convert_to_unit)
        return val_with_unit

    def is_lighting_following_occupancy(self, room_type: Enum) -> bool:
        return self.lighting_follow_occupancy.loc[room_type].iat[0]

    def is_light_off_during_night(self, room_type: Enum) -> bool:
        return self.light_off_during_night.loc[room_type].iat[0]

    def get_lighting_setpoint(self, room_type: Enum) -> Quantity:
        return self.lighting_setpoint.loc[room_type].iat[0]

    def get_lighting_density_std(self, room_type: Enum) -> Quantity:
        return self.lighting_density_triple.loc[room_type, COL_STD]

    def get_lighting_density_triple(self, room_type: Enum) -> Quantity:
        """
        Returns dict with entries COL_MIN, STD, MAX (defined in cesarp.common.profiles.__init__.py)
        """
        return self.lighting_density_triple.loc[room_type]

    def get_heating_setpoint(self, room_type) -> Quantity:
        return self.setpoint_heating.loc[room_type].iat[0]

    def get_cooling_setpoint(self, room_type) -> Quantity:
        return self.setpoint_cooling.loc[room_type].iat[0]

    def get_ventilation_rate_day_per_person(self, room_type) -> Quantity:
        return self.ventilation_rate_per_p_nominal.loc[room_type].iat[0]

    def get_ventilation_rate_night_per_person(self, room_type) -> Quantity:
        return self.ventilation_rate_night_per_p_nominal.loc[room_type].iat[0]

    def get_ventilation_rate_per_area(self, room_type) -> Quantity:
        # pint converts m3/m2/h to m/h... don't know how to avoid that
        return self.ventilation_rate_per_m2_nominal.loc[room_type].iat[0]

    def get_activity_level_per_person(self, room_type) -> float:
        return self.activity_level_per_person.loc[room_type].iat[0]

    def get_appliance_day_profile_hourly(self, room_type) -> List[float]:
        return self.appliances_day_profile_hourly_nominal.loc[room_type]

    def get_appliance_level_std(self, room_type) -> Quantity:
        return self.appliances_level_triple.loc[room_type, COL_STD]

    def get_appliance_level_triple(self, room_type) -> Dict[str, Quantity]:
        """
        Returns dict with entries COL_MIN, STD, MAX (defined in cesarp.common.profiles.__init__.py)
        """
        return self.appliances_level_triple.loc[room_type]

    def get_area_per_person_std(self, room_type) -> Quantity:
        return self.area_per_person_triple.loc[room_type, COL_STD]

    def get_area_per_person_triple(self, room_type) -> Dict[str, Quantity]:
        """
        Returns dict with entries COL_MIN, STD, MAX (defined in cesarp.common.profiles.__init__.py)
        """
        return self.area_per_person_triple.loc[room_type]

    def get_dhw_demand_std(self, room_type) -> Quantity:
        return self.dhw_power_per_area_triple.loc[room_type, COL_STD]

    def get_dhw_demand_triple(self, room_type) -> Dict[str, Quantity]:
        """
        Returns dict with entries COL_MIN, STD, MAX (defined in cesarp.common.profiles.__init__.py)
        """
        return self.dhw_power_per_area_triple.loc[room_type]

    def get_dhw_demand_liter_per_day_pp_std(self, room_type) -> Quantity:
        return self.dhw_liter_per_day_pp_triple.loc[room_type, COL_STD]

    def get_dhw_demand_liter_per_day_pp_triple(self, room_type) -> Dict[str, Quantity]:
        """
        Returns dict with entries COL_MIN, STD, MAX (defined in cesarp.common.profiles.__init__.py)
        """
        return self.dhw_liter_per_day_pp_triple.loc[room_type]

    def get_monthly_variation(self, room_type) -> List[float]:
        return self.variation_year_profile_monthly_nominal.loc[room_type]

    def get_nr_of_rest_days_per_week(self, room_type) -> Quantity:
        return self.nr_of_rest_days_per_week.loc[room_type].iat[0]

    def get_occ_day_profile_hourly_nominal(self, room_type) -> List[float]:
        return self.occ_day_profile_hourly_nominal.loc[room_type]

    def _do_setback_thermostat_when_unoccupied(self, room_type):
        return self.do_setback_thermostat_when_unoccupied.loc[room_type].iat[0]

    def _do_setback_thermostat_during_night(self, room_type):
        return self.do_setback_thermostat_during_night.loc[room_type].iat[0]

    def get_night_setback_heating(self, room_type) -> Quantity:
        if self._do_setback_thermostat_during_night(room_type):
            return self.heating_setback.loc[room_type].iat[0]
        else:
            return 0 * self.ureg.delta_degC

    def get_unoccupied_setback_heating(self, room_type) -> Quantity:
        if self._do_setback_thermostat_when_unoccupied(room_type):
            return self.heating_setback.loc[room_type].iat[0]
        else:
            return 0 * self.ureg.delta_degC

    def get_night_setback_cooling(self, room_type) -> Quantity:
        if self._do_setback_thermostat_during_night(room_type):
            return self.cooling_setback.loc[room_type].iat[0]
        else:
            return 0 * self.ureg.delta_degC

    def get_unoccupied_setback_cooling(self, room_type) -> Quantity:
        if self._do_setback_thermostat_when_unoccupied(room_type):
            return self.cooling_setback.loc[room_type].iat[0]
        else:
            return 0 * self.ureg.delta_degC

    def get_appliance_profile_min_value_allowed(self, room_type) -> Quantity:
        return self.appliances_level_standby_prc.loc[room_type].iat[0]

    def get_appliance_profile_fixed_weekend_value(self, room_type) -> Quantity:
        return self.get_appliance_profile_min_value_allowed(room_type)

    def get_dhw_night_value(self) -> Quantity:
        return self.ureg(self._cfg_profiles["DHW_NIGHT_VALUE"])

    def get_light_off_fraction_profile_value(self) -> Quantity:
        """
        :return: value to be set in the lighting fraction profile when lighting is off (e.g. during night, unoccupied)
        """
        return self.ureg(self._cfg_profiles["LIGHTING_OFF_VALUE"])

    def get_infiltration_rate_stock(self, room_type) -> Quantity:
        return self.infiltration_rate_stock.loc[room_type].iat[0]

    def get_infiltration_fraction_profile_base_value(self) -> Quantity:
        return self.ureg(self._cfg_profiles["INFILTRATION_RATE_FRACTION_BASE_VALUE"])

    def get_wakeup_hour(self) -> int:
        return self._cfg_profiles["WAKEUP_HOUR"]

    def get_sleeptime_hour(self) -> int:
        return self._cfg_profiles["SLEEPTIME_HOUR"]

    def get_horizontal_breaks_occupancy(self, room_type: Enum) -> List[int]:
        return self.occ_breaks.loc[room_type].iat[0]

    def get_horizontal_breaks_appliances(self, room_type: Enum) -> List[int]:
        return self.appliances_breaks.loc[room_type].iat[0]

    def is_dhw_off_during_night(self, room_type) -> bool:
        return self.dhw_off_during_night.loc[room_type].iat[0]

    def is_occupancy_nominal_during_night(self, room_type: Enum) -> bool:
        return self.occupancy_nominal_during_night.loc[room_type].iat[0]

    def get_occupancy_profile_restday_value(self, room_type) -> Quantity:
        return self.ureg(self._cfg_profiles["OCCUPANCY_RESTDAY_VALUE"])

    def get_data_source_description(self):
        return DatasetMetadata(
            source=self._cfg_sia_sheet["DATA_SOURCE_DESCRIPTION"],
            source_link=f'{self._cfg_sia_sheet["FILE_PATH"]} sheet {self._cfg_sia_sheet["SHEET_NAME"]}',
            config_entries={self.__PROFILE_SETTINGS_KEY: self._cfg_profiles},
        )

    def get_bldg_type(self, bldg_type_key):
        """
        Get a SIA2024BuildingType object describing the building matching the given bldg_type_key. Available building types see file specified in
        configuration ['SIA2024']['BUILDING_TYPES_CONFIG_FILE']

        :param bldg_type_key: String or Enum SIA2024BldgTypeKeys defining the building type.
        """
        if isinstance(bldg_type_key, str):
            bldg_type_key = SIA2024BldgTypeKeys[bldg_type_key]
        cfg_bldg_type = self.__bldg_type_cfg[bldg_type_key.name]
        rooms = {SIA2024_2016_RoomType[room_type_str]: room_area_fraction for room_type_str, room_area_fraction in cfg_bldg_type["ROOM_TYPES"].items()}
        return SIA2024BuildingType(bldg_type_key, cfg_bldg_type["SIA_NAME"], cfg_bldg_type["SIA_NR"], rooms, cfg_bldg_type["IS_RESIDENTIAL"])
