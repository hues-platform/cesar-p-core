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
import logging
from typing import Dict, Any, Optional, Union
from cesarp.common.CesarpException import CesarpException
from cesarp.common import config_loader
from cesarp.geometry import building
from cesarp.geometry import neighbourhood
from cesarp.geometry import vertices_basics
from cesarp.geometry import _default_config_file
from cesarp.model.BldgShape import BldgShapeEnvelope, BldgShapeDetailed


class GeometryBuilder:
    """
    Builds geometry of a building and with the same origin vertex the shapes of neighbouring buildings.
    The class is not safe for multithreading due to the "caching" of neighbour buildings.
    For configuration options, please see default_config.yml.
    Manages the geometry data for one building, including neighbouring buildings.
    All returned coordinates have the first vertex of the main building set as the origin.
    The layout of the dataframe for the site_bldgs parameter matches the one
    returned by cesarp.geometry.vertices_basics.convert_flat_site_vertices_to_per_bldg_footprint.
    """

    def __init__(self, main_bldg_fid, site_bldgs: pd.DataFrame, glazing_ratio: float, custom_config: Optional[Dict[str, Any]] = None):
        """
        :param main_bldg_fid: gis_fid of main building which will be simulated. gis_fid must be containted in
                                  site_bldgs

        :param site_bldgs: pandas DataFrame with one row for each building, columns being 'gis_fid', 'height', 'footprint_shape' and main_vertex_x/main_vertex_y
                            for convenience in lookup of reference vertex for a building 'footprint_shape' is a pandas DataFrame[columns=[x,y]] all vertices of one building
        :param flat_site_vertices: pandas DataFrame with columns gis_fid, x, y, height having several rows per gis_fid.
                                    vertex are expected in counter-clockwise sequence
        """
        self.site_bldgs = site_bldgs
        self.bldg_main = self.site_bldgs.loc[main_bldg_fid].to_dict()  # as it contains a nested DF, for pickling we need to convert to dict....
        self.origin_vertex = {"x": self.bldg_main["main_vertex_x"], "y": self.bldg_main["main_vertex_y"], "z": 0}
        self.glazing_ratio = glazing_ratio
        self._cfg = config_loader.load_config_for_package(_default_config_file, __package__, custom_config)
        self._custom_config = custom_config
        self._neighbours: Optional[pd.DataFrame] = None
        self._logger = logging.getLogger(__name__)

    def _init_neighbours(self):
        self._neighbours = neighbourhood.search_neighbouring_buildings_for(self.bldg_main, self.site_bldgs, radius=self._cfg["NEIGHBOURHOOD"]["RADIUS"])

    def get_bldg_shape_detailed(self) -> BldgShapeDetailed:
        """
        Get building shape of main building, all coordinates are translated to origin vertex (first vertex of main bldg)
        Walls adjacent

        :param glazing_ratio: wall to window ratio to be used, 0..1
        :return: building shape as dict, details of definition see return value of
                :py:func:`cesarp.geometry.building.create_bldg_shape_detailed`
        """
        if self._neighbours is None:
            self._init_neighbours()

        bldg_shape = building.create_bldg_shape_detailed(
            self.bldg_main,
            self.glazing_ratio,
            neighbourhood.find_adjacent_footprint_vertices_for,
            self._neighbours,
            self._cfg["NEIGHBOURHOOD"]["MAX_DISTANCE_ADJACENCY"],
            custom_config=self._custom_config,
        )
        self.overall_glazing_ratio = self._check_glz_ratio(bldg_shape)
        bldg_shape_translated: BldgShapeDetailed = self.__translate_bldg_shape_to_origin(bldg_shape)  # type: ignore
        self._logger.info(
            "Bldg with gis_fid {}: shape created with glazing ratio {}, {} stories, {} walls per story".format(
                self.bldg_main["gis_fid"], round(self.overall_glazing_ratio, ndigits=4), bldg_shape_translated.get_nr_of_floors(), len(bldg_shape_translated.walls[0])
            )
        )

        return bldg_shape_translated  # type: ignore

    def get_bldg_shape_of_neighbours(self) -> Dict[int, BldgShapeEnvelope]:
        """
        Search neighbouring buildings in the radius defined in the configuration as ["NEIGHBOURHOOD"]["RADIUS"]

        :return: series of dicts defining the envelopes of all neighbours, details see return value of
                 :py:func:`cesarp.geometry.building.create_bldg_shape_envelope`
        """
        if self._neighbours is None:
            self._init_neighbours()

        if self._neighbours:
            envelop_shapes = {neighbour["gis_fid"]: self.__translate_bldg_shape_to_origin(building.create_bldg_shape_envelope(neighbour)) for neighbour in self._neighbours}
            return envelop_shapes  # type: ignore
        else:
            return {}

    def __translate_bldg_shape_to_origin(self, bldg_shape: Union[BldgShapeEnvelope, BldgShapeDetailed]) -> Union[BldgShapeEnvelope, BldgShapeDetailed]:
        """
        Translates all values coordinates found in bldg shape definition in place.
        Following types are translated:
            DataFrame[columns='x','y','z'],
            list(DataFrame[columns='x','y','z'])
            DataFame(DataFrame[columns='x','y','z'])
            list(list(DataFrame[columns='x','y','z']))

        :param bldg_shape - either BldgshapeEnvelope or BldgShapeDetailed
        :return: passed bldg_shape (the same object, not a copy)
        """
        bldg_shape.groundfloor = vertices_basics.translate_to_origin(self.origin_vertex, bldg_shape.groundfloor)
        bldg_shape.roof = vertices_basics.translate_to_origin(self.origin_vertex, bldg_shape.roof)
        bldg_shape.walls = [[vertices_basics.translate_to_origin(self.origin_vertex, w) for w in wof] for wof in bldg_shape.walls]
        if isinstance(bldg_shape, BldgShapeDetailed):
            bldg_shape.windows = [[vertices_basics.translate_to_origin(self.origin_vertex, w) for w in wof] for wof in bldg_shape.windows]
            bldg_shape.internal_floors = [vertices_basics.translate_to_origin(self.origin_vertex, intfloor) for intfloor in bldg_shape.internal_floors]

        return bldg_shape

    def _check_glz_ratio(self, bldg_shape: BldgShapeDetailed):
        glz_check_cfg = self._cfg["MAIN_BLDG_SHAPE"]["GLAZING_RATIO_CHECK"]
        overall_glz_ratio = building.calc_glz_ratio_for_bldg(bldg_shape)
        if any(bldg_shape.adjacent_walls_bool) and not glz_check_cfg["DO_CHECK_BLD_WITH_ADJACENCIES"]:
            return overall_glz_ratio

        allowed_deviation = glz_check_cfg["ALLOWED_GLZ_RATIO_DEV"]
        assert (
            allowed_deviation > 0 and allowed_deviation < 1
        ), f"expected a percentage in range 0 to 1 for GLAZING_RATIO_CHECK:ALLOWED_GLZ_RATIO_DEV config, but got a value of {allowed_deviation}"

        if abs(self.glazing_ratio - overall_glz_ratio) > allowed_deviation:
            log_pre = 4  # floting point number precision for log messages
            log_msg = f"GLAZING RATIO MISMATCH for bldg with fid {self.bldg_main['gis_fid']}: glazing ratio set is {round(self.glazing_ratio, ndigits=log_pre)}, modeled overall glazing ratio is {round(overall_glz_ratio, ndigits=log_pre)}."
            if any(bldg_shape.adjacent_walls_bool):
                log_msg += (
                    " Building has adjacent walls which are modeled without windows, thus overall building glazing ratio is smaller than the one set, which is applied per wall."
                )
            else:
                log_msg += " Mismatch is most probably due to many walls which are too small for windows."

            if glz_check_cfg["EXCEPTION_ON_MISMATCH"]:
                self._logger.error(log_msg)
                raise CesarpException(log_msg)
            else:
                self._logger.warning(log_msg)
