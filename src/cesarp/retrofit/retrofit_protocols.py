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
from typing import Protocol
from cesarp.model.WindowConstruction import WindowConstruction
from cesarp.model.Construction import Construction


class ConstructionRetrofitterProtocol(Protocol):
    def get_retrofitted_construction(self, construction: Construction) -> Construction:
        """return retrofitted version of passed construction element as a NEW object"""
        ...

    def get_retrofitted_window(self, base_win_constr: WindowConstruction) -> WindowConstruction:
        """return retrofitted version of passed window construction as a NEW object"""
        ...

    def get_retrofit_target_info(self) -> str:
        """should retrun a descriptive string of the retrofit target intended to meet, e.g. SIA380-2016 Minimal"""
        ...


class ConstructionRetrofitCostProtocol(Protocol):
    def get_costs_for_window_retrofit(self, window_constr: WindowConstruction) -> pint.Quantity:
        ...

    def get_costs_for_construction_retrofit(self, constr: Construction) -> pint.Quantity:
        ...


class ConstructionRetrofitEmbodiedEmissionsProtocol(Protocol):
    def get_constr_ret_emb_co2(self, constr: Construction) -> pint.Quantity:
        ...

    def get_constr_ret_emb_non_renewable_pen(self, constr: Construction) -> pint.Quantity:
        ...

    def get_win_ret_glass_emb_co2(self, win_constr: WindowConstruction) -> pint.Quantity:
        ...

    def get_win_ret_glass_emb_non_renewable_pen(self, win_constr: WindowConstruction) -> pint.Quantity:
        ...

    def get_win_ret_frame_emb_co2(self, win_constr: WindowConstruction) -> pint.Quantity:
        ...

    def get_win_ret_frame_emb_non_renewable_pen(self, win_constr: WindowConstruction) -> pint.Quantity:
        ...
