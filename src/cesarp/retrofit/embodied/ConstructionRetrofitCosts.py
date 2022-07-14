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
from typing import Dict, Any, Optional
import logging

import cesarp.common
from cesarp.retrofit.embodied import _default_config_file
from cesarp.retrofit.embodied import retrofit_input_parser
from cesarp.model.Construction import Construction, BuildingElement
from cesarp.model.WindowConstruction import WindowConstruction
from cesarp.model.Layer import LayerFunction


class ConstructionRetrofitCosts:
    def __init__(self, ureg: pint.UnitRegistry, custom_config: Optional[Dict[str, Any]] = None):
        self._cfg = cesarp.common.load_config_for_package(_default_config_file, __package__, custom_config)
        self.ureg = ureg
        self.insulation_cost_lookup = retrofit_input_parser.read_insulation_costs(self._cfg["INSULATION_COST_LOOKUP"], ureg)
        self._window_cost_lookup = retrofit_input_parser.read_window_costs(self._cfg["WINDOW_COST_LOOKUP"], ureg)
        self.logger = logging.getLogger(__name__)

    def _get_cost_for_layer_retrofit(self, bldg_elem: BuildingElement, layer_function: LayerFunction, insulation_thickness: pint.Quantity):
        """
        Go through the cost table and find costs matching for the passed bldg element and layer function.
        Return the costs for matching layer thickness or interpolate if necessary.
        Extrapolation:
        - between thickness 0 and first entry assuming 0 costs for thickness 0.
        - for thickness bigger than the last entry, extrapolate with the costs/m of the last entry (assuming linear growth in costs)

        :param bldg_elem: BuildingElement for which to get retrofit costs
        :param layer_function: function of the layer that got retrofitted
        :param insulation_thickness: thickness of added insulation
        :return: costs for retrofit in CHF/m2, returns 0 if no matching cost entry was found
        """
        return_unit_chf_m2 = self.ureg.CHF / self.ureg.m ** 2
        insulation_thickness_in_m = insulation_thickness.to(self.ureg.m)
        for retrofit_cost in self.insulation_cost_lookup:
            if retrofit_cost.layer_function == layer_function and bldg_elem in retrofit_cost.applicable_to:
                last_thickness_in_m = 0 * self.ureg.m
                last_costs = 0 * self.ureg.CHF / self.ureg.m ** 2
                for thickness_entry, current_costs in retrofit_cost.cost_per_thickness.items():
                    current_thickness_in_m = thickness_entry.to(self.ureg.m)
                    if insulation_thickness_in_m == current_thickness_in_m:
                        return current_costs.to(return_unit_chf_m2)
                    if insulation_thickness_in_m > thickness_entry.to(self.ureg.m):
                        last_thickness_in_m = current_thickness_in_m
                        last_costs = current_costs
                    else:
                        delta_thickness = current_thickness_in_m - last_thickness_in_m
                        delta_costs = current_costs - last_costs
                        delta_costs_per_m = delta_costs / delta_thickness
                        delta_costs = delta_costs_per_m * (insulation_thickness_in_m - last_thickness_in_m)
                        costs = last_costs + delta_costs
                        return costs.to(return_unit_chf_m2)
                if last_thickness_in_m.m != 0:
                    cost_per_m = last_costs / last_thickness_in_m
                    return (cost_per_m * insulation_thickness_in_m).to(return_unit_chf_m2)

        # no matching cost entry was found
        raise Exception(f"No cost information found for {bldg_elem.name} {layer_function.name}")

    def get_costs_for_construction_retrofit(self, constr: Construction):
        """
        Returns the specific costs per m2 of ALL retrofit measures applied to the construction.
        Assumes that thickness of an isolation layer was incresed, the old and new part are
        modeled as separate layers.
        Returns 0 if no retrofit measures were applied to that construction.
        """
        sum_of_costs = 0 * self.ureg.CHF / self.ureg.m ** 2
        for layer in constr.layers:
            if layer.retrofitted:
                try:
                    sum_of_costs += self._get_cost_for_layer_retrofit(constr.bldg_element, layer.function, layer.thickness)
                except Exception:
                    pass  # we do not care if one layer has no costs for retrofit, eg outside finish has no cost attribute
        if sum_of_costs.m == 0:
            self.logger.info(f"no retrofit costs for construction {constr} assigned")
        return sum_of_costs

    def get_costs_for_window_retrofit(self, window_constr: WindowConstruction):
        """
        The returned costs should include costs for window glass and frame per window glass area, so costs for window
        frame have to be included and scale with the window glass area.

        :param window_constr:
        :return: costs for glass + frame per m2 window glass area as pint.Quantity with unit CHF/m2,
                 returns 0 CHF/m2 if no costs for given window was found
        """
        try:
            costs = self._window_cost_lookup[window_constr.glass.name]
        except KeyError:
            self.logger.info(f"No retrofit costs assigned for {window_constr}.")
            costs = 0 * self.ureg.CHF / self.ureg.m ** 2
        return costs
