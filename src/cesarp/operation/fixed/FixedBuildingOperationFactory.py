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

from cesarp.model.BuildingOperation import BuildingOperation, HVACOperation, Occupancy, InstallationOperation
from cesarp.model.BuildingOperationMapping import BuildingOperationMapping
from cesarp.common.ScheduleFile import ScheduleFile
from cesarp.common import config_loader
from cesarp.operation.fixed import _default_config_file
from cesarp.common.ScheduleTypeLimits import ScheduleTypeLimits
from cesarp.operation.protocols import PassiveCoolingOperationFactoryProtocol


class FixedBuildingOperationFactory:
    """
    Assembles internal condition properties based on configuration settings pointing to schedule files.
    For all buildings the same schedules and parameters are applied.

    Implements the :py:class:`cesarp.manager.manager_protocols.BuildingOperationFactoryProtocol` and thus can be set as "BUILDING_OPERATION_FACTORY_CLASS" in the config of package :py:class:`cesarp.manager`
    """

    def __init__(self, passive_cooling_op_fact: PassiveCoolingOperationFactoryProtocol, unit_registry, custom_config=None):
        self._unit_registry = unit_registry
        self._cfg = config_loader.load_config_for_package(_default_config_file, __package__, custom_config)
        self._passive_cooling_op_fact = passive_cooling_op_fact

    def get_building_operation(self, bldg_fid: int, nr_of_floors: int) -> BuildingOperationMapping:
        """
        Get fixed schedule files and demand values from configuration

        :param bldg_fid: fid of building for which to get building operation. Has no influence here, as parameters
                         and scheudles are fixed
        :return: BuildinOperation object
        """
        occupancy = Occupancy(
            self._unit_registry(self._cfg["FLOOR_AREA_PER_PERSON"]),
            self._get_schedule_for(self._cfg["SCHED_OCCUPANCY_PATH"], ScheduleTypeLimits.FRACTION()),
            self._get_schedule_for(self._cfg["SCHED_ACTIVITY_PATH"], ScheduleTypeLimits.ANY(), unit_of_values=self._unit_registry.W / self._unit_registry.person),
        )
        appliances = InstallationOperation(
            self._get_schedule_for(self._cfg["SCHED_APPLIANCES_PATH"], ScheduleTypeLimits.FRACTION()), self._unit_registry(self._cfg["APPLIANCES_WATT_PER_ZONE_AREA"])
        )
        lighting = InstallationOperation(
            self._get_schedule_for(self._cfg["SCHED_LIGHTING_PATH"], ScheduleTypeLimits.FRACTION()), self._unit_registry(self._cfg["LIGHTING_WATT_PER_ZONE_AREA"])
        )
        dhw = InstallationOperation(self._get_schedule_for(self._cfg["SCHED_DHW_PATH"], ScheduleTypeLimits.FRACTION()), self._unit_registry(self._cfg["DHW_WATTS_PER_ZONE_AREA"]))
        hvac_op = HVACOperation(
            self._get_schedule_for(self._cfg["SCHED_THERMOSTAT_HEATING"], ScheduleTypeLimits.TEMPERATURE()),
            self._get_schedule_for(self._cfg["SCHED_THERMOSTAT_COOLING"], ScheduleTypeLimits.TEMPERATURE()),
            self._get_schedule_for(self._cfg["SCHED_VENTILATION"], ScheduleTypeLimits.FRACTION()),
            self._unit_registry(self._cfg["OUTDOOR_AIR_FLOW_PER_ZONE_FLOOR_AREA"]),
        )
        night_vent = self._passive_cooling_op_fact.create_night_vent(bldg_fid, hvac_op.cooling_setpoint_schedule)
        win_shading_ctrl = self._passive_cooling_op_fact.create_win_shading_ctrl(bldg_fid)
        bldg_op = BuildingOperation("FIXED", occupancy, appliances, lighting, dhw, hvac_op, night_vent, win_shading_ctrl)
        bldg_op_mapping = BuildingOperationMapping()
        bldg_op_mapping.add_operation_assignment_all_floors(nr_of_floors, bldg_op)
        return bldg_op_mapping

    def _get_schedule_for(self, schedule_file_path, type_limits, unit_of_values=None):
        assert type_limits != ScheduleTypeLimits.ANY() or unit_of_values, "if schedule type is ANY unit_of_values must be defined"
        if not unit_of_values:
            if type_limits in [
                ScheduleTypeLimits.FRACTION(),
                ScheduleTypeLimits.ON_OFF(),
                ScheduleTypeLimits.CONTROL_TYPE(),
            ]:
                unit_of_values = self._unit_registry.dimensionless
            elif type_limits == ScheduleTypeLimits.TEMPERATURE():
                unit_of_values = self._unit_registry.degC
            else:
                raise Exception(f"unkonw type limits {type_limits.name} for schedule without defined unit")
        sched_prop_cfg = self._cfg["SCHED_PROPS"]
        return ScheduleFile(
            schedule_file_path,
            type_limits,
            sched_prop_cfg["NUM_OF_HEADER_ROWS"],
            sched_prop_cfg["SEPARATOR"],
            sched_prop_cfg["NUM_OF_HOURS"],
            sched_prop_cfg["DATA_COLUMN"],
            unit_of_values,
        )
