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
from typing import List, Tuple
from cesarp.model.BuildingOperation import BuildingOperation
from cesarp.common.CesarpException import CesarpException


class BuildingOperationMapping:
    def __init__(self):
        self._op_assignments: List[Tuple[List[int], BuildingOperation]] = []
        self.all_assigned_floor_nrs: List[int] = []

    def get_operation_assignments(self) -> List[Tuple[List[int], BuildingOperation]]:
        return sorted(self._op_assignments, key=lambda assignment: assignment[0][0])

    def add_operation_assignment(self, floor_nrs: List[int], building_op: BuildingOperation):
        assert floor_nrs, "you passed empty floor list to add_operation_assignment which is not expected."
        already_assigned = set.intersection(set(self.all_assigned_floor_nrs), set(floor_nrs))
        assert not already_assigned, f"for floor nrs {already_assigned} building operation has already been assigned."
        self.all_assigned_floor_nrs += list(floor_nrs)
        self._op_assignments.append((sorted(floor_nrs), building_op))

    def add_operation_assignment_all_floors(self, nr_of_floors: int, building_op: BuildingOperation) -> None:
        # sourcery skip: remove-zero-from-range
        self.add_operation_assignment(list(range(0, nr_of_floors)), building_op)

    def get_operation_for_floor(self, floor_nr: int):
        """for fast access to all building operation assignment please use get_operation_assignment"""
        for floor_nrs, bldg_op in self._op_assignments:
            if floor_nr in floor_nrs:
                return bldg_op

        raise CesarpException(f"for floor nr {floor_nr} there is no building operation assigned, available are floor nrs {self.all_assigned_floor_nrs}")
