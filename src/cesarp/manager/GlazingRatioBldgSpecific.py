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
from typing import Dict
import logging

from cesarp.manager.manager_protocols import GlazingRatioProviderProtocol


class GlazingRatioBldgSpecific(GlazingRatioProviderProtocol):
    def __init__(self, glz_ratio_per_fid: Dict[int, float]):
        # convert from percentage in range 0..100 to 0..1 if necessary
        if all([glz_ratio > 1 or glz_ratio == 0 for glz_ratio in glz_ratio_per_fid.values()]):
            self.glz_ratio_per_fid = {fid: glz_ratio / 100 for fid, glz_ratio in glz_ratio_per_fid.items()}
            logging.getLogger(__name__).debug("converted glazing ratio per building from percentage range 0...100 to 0...1")
        else:
            self.glz_ratio_per_fid = glz_ratio_per_fid

    def get_for_bldg_fid(self, bldg_fid):
        return self.glz_ratio_per_fid[bldg_fid]
