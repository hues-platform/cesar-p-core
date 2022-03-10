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
from collections import OrderedDict
import pint

from typing import Dict, List
import cesarp.common
from cesarp.retrofit.embodied.InsulationCosts import InsulationCosts
from cesarp.model.Layer import LayerFunction
from cesarp.model.BuildingElement import BuildingElement


def read_insulation_costs(yml_input_file: str, ureg: pint.UnitRegistry) -> List[InsulationCosts]:
    """
    Note: currently we just expect certain categories for the costs. when needed the applicable_to and
    layer_function parameters for the InsulationCosts objects could be read from config as well to allow for
    other groups to specify costs
    :return: list of InsulationCost objects
    """
    yml_cost_config = cesarp.common.load_config_full(yml_input_file, ignore_metadata=True)
    cost_lookup = []
    out_compact_costs = _order_by_key(_convert_key_value_to_quantity(yml_cost_config["WALL_OUTSIDE_COMPACT"], ureg))
    cost_lookup.append(
        InsulationCosts(
            cost_per_thickness=out_compact_costs,
            applicable_to=[BuildingElement.WALL],
            layer_function=LayerFunction.INSULATION_OUTSIDE,
        )
    )
    backv_costs = _order_by_key(_convert_key_value_to_quantity(yml_cost_config["WALL_OUTSIDE_BACK_VENTILATED"], ureg))
    cost_lookup.append(
        InsulationCosts(
            cost_per_thickness=backv_costs,
            applicable_to=[BuildingElement.WALL],
            layer_function=LayerFunction.INSULATION_OUTSIDE_BACK_VENTILATED,
        )
    )
    roof_inside_costs = _order_by_key(_convert_key_value_to_quantity(yml_cost_config["ROOF_INSIDE"], ureg))
    cost_lookup.append(
        InsulationCosts(
            cost_per_thickness=roof_inside_costs,
            applicable_to=[BuildingElement.ROOF],
            layer_function=LayerFunction.INSULATION_INSIDE,
        )
    )
    roof_outside_costs = _order_by_key(_convert_key_value_to_quantity(yml_cost_config["ROOF_OUTSIDE"], ureg))
    cost_lookup.append(
        InsulationCosts(
            cost_per_thickness=roof_outside_costs,
            applicable_to=[BuildingElement.ROOF],
            layer_function=LayerFunction.INSULATION_OUTSIDE,
        )
    )
    inb_costs = _order_by_key(_convert_key_value_to_quantity(yml_cost_config["WALL_ROOF_GROUNDFLOOR_INBETWEEN"], ureg))
    cost_lookup.append(
        InsulationCosts(
            cost_per_thickness=inb_costs,
            applicable_to=[BuildingElement.WALL, BuildingElement.ROOF, BuildingElement.GROUNDFLOOR],
            layer_function=LayerFunction.INSULATION_IN_BETWEEN,
        )
    )
    gf_costs = _order_by_key(_convert_key_value_to_quantity(yml_cost_config["GROUNDFLOOR_INSULATION_TO_UNHEATED_SPACE"], ureg))
    cost_lookup.append(
        InsulationCosts(
            cost_per_thickness=gf_costs,
            applicable_to=[BuildingElement.GROUNDFLOOR],
            layer_function=LayerFunction.INSULATION_INSIDE,
        )
    )
    return cost_lookup


def read_window_costs(yml_input_file: str, ureg: pint.UnitRegistry) -> Dict[str, pint.Quantity]:
    """
    :param yml_input_file: file containint "COST_PER_WINDOW_TYPE" config
    :return: dict with entries beeing window construction names (URI), value frame+window glass cost per m2 glass area
    """
    yml_cost_config = cesarp.common.load_config_full(yml_input_file, ignore_metadata=True)
    return _convert_value_to_quantity(yml_cost_config["COST_PER_WINDOW_TYPE"], ureg)


def _convert_key_value_to_quantity(the_dict: Dict[str, str], ureg: pint.UnitRegistry) -> Dict:
    return {ureg(key): ureg(value) for key, value in the_dict.items()}


def _convert_value_to_quantity(the_dict: Dict[str, str], ureg: pint.UnitRegistry) -> Dict:
    return {key: ureg(value) for key, value in the_dict.items()}


def _order_by_key(the_dict) -> OrderedDict:
    return OrderedDict(sorted(the_dict.items(), key=lambda t: t[0]))
