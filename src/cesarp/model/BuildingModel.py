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
from typing import Mapping, Dict, Any
import pandas as pd

from cesarp.model.Site import Site
from cesarp.model.BuildingConstruction import BuildingConstruction
from cesarp.model.BuildingOperationMapping import BuildingOperationMapping
from cesarp.model.BldgShape import BldgShapeDetailed, BldgShapeEnvelope
from cesarp.model.ShadingObjectConstruction import ShadingObjectConstruction
from cesarp.model.BldgType import BldgType
from cesarp.model.BuildingOperation import NightVent, WindowShadingControl
from cesarp.model.WindowConstruction import WindowShadingMaterial


class BuildingModel:
    """
    In case you change the structure, add parameters in any of the sub-classes,
    make sure old versions stored to disk can be reloaded by adapting the upgrade_if_necessary() method
    and you increse the self._class_version

    Version 1.0: first version pushed to master
    Version 1.1: added year_of_construction, cooling parameters
    Version 1.2: merged Version 1.1 from feature/cooling branch, but without cooling parameters, but adding bldg_type
    Verstion 1.3: changed BldgShapeEnvelope and BldgShapeDetailed from typed dict to dataclasses
    Version 1.4: adding night ventilation and shading to bldg operation and construction
    Version 1.5: changing BuildingOperation to BuildingOperationMapping to allow for per-floor BuildingOperation assignment
    Version 1.6: adding name parameter to BuildingOperation
    Version 1.7: removing internal floor from construction, as it must be mirrored construction to internal ceiling
    """

    def __init__(
        self,
        fid: int,
        year_of_construction: int,
        site: Site,
        bldg_shape: BldgShapeDetailed,
        neighbours: pd.DataFrame,
        neighbours_construction_props: Mapping[str, ShadingObjectConstruction],  # keys should be name of cesarp.model.Construction.BuildingElement Enum instances
        bldg_construction: BuildingConstruction,
        bldg_operation_mapping: BuildingOperationMapping,
        bldg_type: BldgType,
    ):
        self._class_version = 1.7
        self.fid = fid
        self.year_of_construction = year_of_construction
        self.site = site
        self.bldg_shape = bldg_shape
        self.neighbours = neighbours
        self.neighbours_construction_props = neighbours_construction_props
        self.bldg_construction = bldg_construction
        self.bldg_operation_mapping = bldg_operation_mapping
        self.bldg_type = bldg_type

    def upgrade_if_necessary(self):
        if self._class_version <= 1.2:

            def convert_envelope(old_envelope: Dict[str, Any]) -> BldgShapeEnvelope:
                return BldgShapeEnvelope(groundfloor=old_envelope["groundfloor"], roof=old_envelope["roof"], walls=old_envelope["walls"])

            self.bldg_shape = BldgShapeDetailed(
                groundfloor=self.bldg_shape["groundfloor"],
                roof=self.bldg_shape["roof"],
                walls=self.bldg_shape["walls"],
                windows=self.bldg_shape["windows"],
                window_frame=self.bldg_shape["window_frame"],
                adjacent_walls_bool=self.bldg_shape["adjacent_walls_bool"],
                internal_floors=self.bldg_shape["internal_floors"],
            )
            self.neighbours = {fid: convert_envelope(shape) for fid, shape in self.neighbours.items()}
            self._class_version = 1.3

        if self._class_version <= 1.3:
            setattr(self.bldg_operation, "night_vent", NightVent.create_empty_inactive())
            setattr(self.bldg_operation, "win_shading_ctrl", WindowShadingControl.create_empty_inactive())
            setattr(self.bldg_construction.window_constr, "shade", WindowShadingMaterial.create_empty_unavailable())
            self._class_version = 1.4

        if self._class_version <= 1.4:
            setattr(self, "bldg_operation_mapping", BuildingOperationMapping())
            self.bldg_operation_mapping.add_operation_assignment(range(0, self.bldg_shape.get_nr_of_floors()), self.bldg_operation)
            del self.bldg_operation
            self._class_version = 1.5

        if self._class_version <= 1.5:
            for (floor_nrs, bldg_op) in self.bldg_operation_mapping.get_operation_assignments():
                setattr(bldg_op, "name", "UNKNOWN")
            self._class_version = 1.6

        if self._class_version <= 1.6:
            self.bldg_construction.upgrade_model_remove_floor()
            self._class_version = 1.7
