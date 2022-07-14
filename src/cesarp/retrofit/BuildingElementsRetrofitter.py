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
import pint
import logging
from typing import List, Dict, Any, Optional, Union
import pandas as pd

from cesarp.retrofit.retrofit_protocols import (
    ConstructionRetrofitCostProtocol,
    ConstructionRetrofitEmbodiedEmissionsProtocol,
    ConstructionRetrofitterProtocol,
)
import cesarp.common
from cesarp.retrofit import _default_config_file
from cesarp.graphdb_access.GraphDBFacade import GraphDBFacade
from cesarp.model.BldgShape import BldgShapeDetailed
from cesarp.model.BuildingElement import BuildingElement
from cesarp.model.BuildingConstruction import BuildingConstruction
from cesarp.model.Construction import Construction
from cesarp.model.WindowConstruction import WindowConstruction
from cesarp.retrofit.RetrofitLog import RetrofitLog
from cesarp.retrofit.embodied.ConstructionRetrofitCosts import ConstructionRetrofitCosts
from cesarp.retrofit.embodied.RetrofitEmbodiedEmissions import RetrofitEmbodiedEmissions
from cesarp.geometry import area_calculator
from cesarp.geometry.CesarGeometryException import CesarGeometryException


class BuildingElementsRetrofitter:
    """
    Handles retrofit for all or part of the building elements.
    In case of window retrofitting the infiltration rate is changed to the value set in configuration
    (INFILRATION_RATE_AFTER_WINDOW_RETROFIT), the actual window construction used for retrofitting has no
    influence on that value.

    Depending on the retrofit target (initialization parameter retrofit_target) using the
    cesarp.retrofit.ConstructionRetrofitter the retrofited consruction is assigend. Furthermore, costs for retrofit
    and embodied emissions (non-renewable PEN & CO2) are calculated and saved in the retrofit log.

    All retrofit measures are logged, which is accessible as member "retrofit_log" as instance of
    cesarp.retrofit.RetrofitLog class. It includes the embodied costs and emissions. Depending on your needs,
    you can reset the log by calling reset_retrofit_log() before calling retrofit_bldg_construction(....) and
    retrieving the log right afterwards, which gives you the log only for that one building. Otherwise, log entries
    for the different buildings are appended (log entries contain building fid).
    """

    _retrofittable_bldg_elems = [
        BuildingElement.ROOF,
        BuildingElement.WALL,
        BuildingElement.GROUNDFLOOR,
        BuildingElement.WINDOW,
    ]

    def __init__(self, ureg: pint.UnitRegistry, custom_config: Optional[Dict[str, Any]] = None):
        """
        Initialize. See set_year_of_retrofit() and set_bldgs_elems_to_retrofit() for further
        configuration options.

        :param ureg: pint unit registry
        """
        self._ureg = ureg
        self._year_of_retrofit: Optional[int] = None
        self._bldg_elems_to_retrofit = self._retrofittable_bldg_elems
        self._logger = logging.getLogger(__name__)
        self._cfg = cesarp.common.load_config_for_package(_default_config_file, __package__, custom_config)

        # can be changed after initialization if needed...
        self.construction_retrofitter: ConstructionRetrofitterProtocol = GraphDBFacade(self._ureg, custom_config).get_graph_construction_retrofitter()
        # can be changed after initialization if needed...
        self.costs: ConstructionRetrofitCostProtocol = ConstructionRetrofitCosts(ureg=ureg)
        self.emissions: ConstructionRetrofitEmbodiedEmissionsProtocol = RetrofitEmbodiedEmissions(ureg)
        # log is not written to disk or anything, it is intended that the caller gets the log after all retrofit
        # operations are done
        self.retrofit_log = RetrofitLog()

        # methods must return the area in m2 (as float, not as pint.Quantity)
        self.area_calc_methods = {
            BuildingElement.WALL: area_calculator.calc_wall_area_without_window_glass_area,
            BuildingElement.ROOF: area_calculator.calc_roof_area,
            BuildingElement.GROUNDFLOOR: area_calculator.calc_groundfloor_area,
        }
        self.area_calc_win_glass_method = area_calculator.calc_window_glass_area
        self.area_calc_win_frame_method = area_calculator.calc_window_frame_area

    def reset_retrofit_log(self):
        self.retrofit_log = RetrofitLog()

    def save_retrofit_log(self, filepath: str):
        self.retrofit_log.save(filepath)

    def get_retrofit_log_as_df(self) -> pd.DataFrame:
        return self.retrofit_log.convert_to_df()

    def set_year_of_retrofit(self, year_of_retrofit: int):
        self._year_of_retrofit = year_of_retrofit

    def set_bldg_elems_to_retrofit(self, bldg_elems_to_retrofit: List[BuildingElement]):
        self._bldg_elems_to_retrofit = bldg_elems_to_retrofit

    def retrofit_bldg_construction(self, bldg_fid: int, bldg_construction: BuildingConstruction, bldg_shape_detailed: BldgShapeDetailed):
        """
        Modifies building construction in place according to set parameters in constructor.

        :param bldg_fid: currently only used for logging
        :param bldg_construction: bldg construction model object
        :return: nothing, bldg_construction is modified in-place
        """
        for bldg_elem in self._bldg_elems_to_retrofit:
            current_construction = bldg_construction.get_construction_for_bldg_elem(bldg_elem)

            retrofitted_construction: Union[Construction, WindowConstruction]
            try:
                if bldg_elem == BuildingElement.WINDOW:
                    retrofitted_construction = self.construction_retrofitter.get_retrofitted_window(current_construction)
                    bldg_construction.infiltration_rate = self._ureg(self._cfg["INFILRATION_RATE_AFTER_WINDOW_RETROFIT"])
                else:
                    retrofitted_construction = self.construction_retrofitter.get_retrofitted_construction(current_construction)
            except KeyError:
                self._logger.warning(
                    f"bldg_fid {bldg_fid}: no retrofit construction found for bldg elem {bldg_elem} "
                    f"with current construction {current_construction.name}. no retrofit is applied."
                )
                continue

            bldg_construction.set_construction_for_bldg_elem(bldg_elem, retrofitted_construction)

            try:
                (area_for_elem, co2_emission, costs, pen) = self._get_emission_and_costs(bldg_elem, bldg_shape_detailed, retrofitted_construction)
            except CesarGeometryException as cge:
                self._logger.warning(f"no emission and costs calculated for fid {bldg_fid}, element {bldg_elem.name}", exc_info=cge)
                area_for_elem, co2_emission, costs, pen = None, None, None, None

            self.retrofit_log.log_retrofit_measure(
                bldg_fid=bldg_fid,
                bldg_element=bldg_elem,
                retrofitted_area=area_for_elem,
                year_of_retrofit=self._year_of_retrofit,
                retrofit_target=self.construction_retrofitter.get_retrofit_target_info(),
                costs=costs,
                non_renewable_pen=pen,
                co2_emission=co2_emission,
                old_construction_name=current_construction.name,
                new_construction_name=retrofitted_construction.name,
            )

    def _get_emission_and_costs(self, bldg_elem, bldg_shape_detailed, retrofitted_constr):
        """
        Calculates retrofit emission and costs for the given building element and building shape.
        """
        if bldg_elem == BuildingElement.WINDOW:
            # glass and frame area for all windows of building
            win_glass_area = self.area_calc_win_glass_method(bldg_shape_detailed) * self._ureg.m ** 2
            win_frame_area = self.area_calc_win_frame_method(bldg_shape_detailed) * self._ureg.m ** 2
            costs = self.costs.get_costs_for_window_retrofit(retrofitted_constr) * win_glass_area
            co2_emission = (
                self.emissions.get_win_ret_glass_emb_co2(retrofitted_constr) * win_glass_area + self.emissions.get_win_ret_frame_emb_co2(retrofitted_constr) * win_frame_area
            )
            pen = (
                self.emissions.get_win_ret_glass_emb_non_renewable_pen(retrofitted_constr) * win_glass_area
                + self.emissions.get_win_ret_frame_emb_non_renewable_pen(retrofitted_constr) * win_frame_area
            )
            elem_area = win_glass_area + win_frame_area
        else:
            # area e.g. for all walls of building
            elem_area = self.area_calc_methods[bldg_elem](bldg_shape_detailed) * self._ureg.m ** 2
            costs = self.costs.get_costs_for_construction_retrofit(retrofitted_constr) * elem_area
            co2_emission = self.emissions.get_constr_ret_emb_co2(retrofitted_constr) * elem_area
            pen = self.emissions.get_constr_ret_emb_non_renewable_pen(retrofitted_constr) * elem_area
        return elem_area, co2_emission, costs, pen
