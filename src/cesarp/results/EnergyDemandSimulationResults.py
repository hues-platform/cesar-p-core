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
from dataclasses import dataclass


@dataclass
class EnergyDemandSimulationResults:
    tot_heating_demand: pint.Quantity
    tot_dhw_demand: pint.Quantity
    tot_electricity_demand: pint.Quantity
    tot_cooling_demand: pint.Quantity
    total_floor_area: pint.Quantity

    def __str__(self):
        return (
            f"Heating demand:\t{self.tot_heating_demand}\n"
            f"DHW demand: \t{self.tot_dhw_demand}\n"
            f"Electricity demand: \t{self.tot_electricity_demand}\n"
            f"Cooling demand: \t{self.tot_cooling_demand}\n"
            f"Total floor area:\t{self.total_floor_area}"
        )

    @property
    def specific_heating_demand(self):
        return self.tot_heating_demand / self.total_floor_area

    @property
    def specific_dhw_demand(self) -> pint.Quantity:
        return self.tot_dhw_demand / self.total_floor_area

    @property
    def specific_electricity_demand(self) -> pint.Quantity:
        return self.tot_electricity_demand / self.total_floor_area

    @property
    def specific_cooling_demand(self) -> pint.Quantity:
        return self.tot_cooling_demand / self.total_floor_area
