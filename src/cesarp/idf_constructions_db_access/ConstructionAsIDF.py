# coding=utf-8
#
# Copyright (c) 2021, Empa, Leonie Fierz, Aaron Bojarski, Ricardo Parreira da Silva, Sven Eggimann.
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
from dataclasses import dataclass
import re
import logging


@dataclass
class ConstructionAsIDF:
    idf_file_path: str
    materials_idf_file_path: str

    @property
    def name(self):
        return self.idf_file_path

    @property
    def emb_co2_emission_per_m2(self):
        raise NotImplementedError(f"no embodied CO2 emission avaiable for ConstructionAsIDF objects; ConstructionAsIDF with " f"path {self.idf_file_path}")

    @property
    def emb_non_ren_primary_energy_per_m2(self):
        raise NotImplementedError(f"no embodied non renewable pen avaiable for ConstructionAsIDF objects; ConstructionAsIDF " f"with path {self.idf_file_path}")

    def get_idf_obj_name(self) -> str:
        """
        Extract idf obj name out of IDF file of this construction

        :return: idf_obj_name of the construction defined in the linked IDF file
        """
        regexp: str = "\s*(\w+\s?\w+),\s*!-\s?Name\s*"  # noqa W605

        matches = [
            re.match(regexp, line).groups(0)[0]  # type: ignore
            for line in open(self.idf_file_path)
            if re.match(regexp, line) is not None
        ]
        if len(matches) != 1:
            raise Exception(f"no or more than one line with matching for element idf_obj_name found in {self.idf_file_path}")
        idf_obj_name = matches[0]

        logging.getLogger(__name__).debug(f"For {self.idf_file_path} idf object idf_obj_name {idf_obj_name} was extracted")

        return idf_obj_name

    def __eq__(self, other):
        return self.idf_file_path == other.idf_file_path and self.materials_idf_file_path == other.materials_idf_file_path

    def __hash__(self):
        return hash((self.idf_file_path, self.materials_idf_file_path))
