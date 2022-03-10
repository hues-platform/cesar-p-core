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
from pathlib import Path
import pint


class ScheduleFile:
    def __init__(
        self,
        schedule_file,
        type_limit,
        header_rows,
        separator,
        num_hours,
        data_column,
        unit_of_values: pint.Unit,
        name=None,
    ):
        """
        Make sure to provide a name when using the same file for multiple schedules, as per default the filename is used as schedule name

        :param schedule_file: file path to file containing schedule
        :param type_limit:
        :param header_rows:
        :param separator:
        :param num_hours:
        :param data_column:
        :param unit_of_values:
        :param name:
        """
        if not name:
            name = Path(schedule_file).stem
        self.name = name
        self.schedule_file = schedule_file
        self.num_hours = num_hours
        self.type_limit = type_limit
        self.header_rows = header_rows
        self.separator = separator
        self.data_column = data_column
        # saving pint unit gives problems when unpickling model...
        self.unit_of_values: str = str(unit_of_values)

    @classmethod
    def from_template(cls, template):
        return cls(
            template.schedule_file,
            template.type_limit,
            template.header_rows,
            template.separator,
            template.num_hours,
            template.data_column,
            template.unit_of_values,
        )
