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
from typing import TypedDict, Dict, Any, List
import pandas as pd
from dataclasses import dataclass


class WindowFrame(TypedDict):
    WIDTH: float  # in meter


@dataclass
class BldgShapeEnvelope:
    """
    - 'groundfloor' - DataFrame[columns=[x,y,z]] defining groundfloor, bottom side facing outside ground
    - 'roof' - DataFrame[columns=[x,y,z]] defining groundfloor, top side facing outside
    - 'walls' - List[index=floor-nr 0..n, value=List[index=wall-nr 0...n, value=DataFrame[columns=[x,y,z]]]]
    """

    groundfloor: pd.DataFrame
    roof: pd.DataFrame
    walls: List[List[pd.DataFrame]]


@dataclass
class BldgShapeDetailed(BldgShapeEnvelope):
    """
    - 'internal_floors' - List(DataFrame[columns=[x,y,z]]) defining floor vertices
    - 'windows' - List[index=floor-nr 0..n, value=List[index=wall-nr 0...n, value=DataFrame[columns=[x,y,z]]]] value is None if there is no window in the wall
    - 'adjacent_walls_bool' - DataFrame[index=floor-nr, columns=wall-nr], entry True if wall is adjacent, False otherwise
    - 'window_frame' - Dict defining geometry properties of frame for all windows
    - 'window_divider' -  Dict defining geometry properties of dividers for all windows
    """

    windows: List[List[pd.DataFrame]]
    window_frame: Dict[str, Any]
    adjacent_walls_bool: pd.DataFrame
    internal_floors: List[pd.DataFrame]

    def get_bldg_height(self) -> float:
        # upper z-coordinate of last floor minus lower z-coordinate of first floor
        return max(self.walls[-1][0]["z"]) - min(self.walls[0][0]["z"])

    def get_nr_of_floors(self) -> int:
        return len(self.walls)

    def get_floor_height(self) -> float:
        #  assuming all floors have same height, taking heigth of first floor
        return max(self.walls[0][0]["z"])
