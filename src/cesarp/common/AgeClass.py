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
import logging
from typing import Iterable, Any, List


class AgeClass:
    """
    Defines an age class with minimal and maximal year/age. Year set as min/max are INCLUDED.
    Either min or max age can be None, which means only a lower or upper bound is set.
    For example, if you create an AgeClass(min_age=None, max_age=1917), this age class includes all year up to and
    including 1917.
    """

    def __init__(self, min_age=None, max_age=None):
        if min_age and max_age:
            if min_age > max_age:
                raise Exception("cannot create an age class with lower max age of {max_age} than min age {min_age}")
        self.min_age = min_age
        self.max_age = max_age

    def isInClass(self, year) -> bool:
        """
        Checks if the given age is within AgeClass (including min and max);
        If neighter min_age nor max_age was defined for this AgeClass the method returns always True

        :param age: year
        :return: True if in age class, false otherwise
        """
        isInRange = True
        if self.min_age is not None:
            isInRange = year >= self.min_age
        if self.max_age is not None:
            isInRange &= year <= self.max_age
        return isInRange

    def __hash__(self):
        return hash((self.min_age, self.max_age))

    def __eq__(self, other) -> bool:
        if self.min_age != other.min_age:
            logging.getLogger(__name__).debug("min_age not equal, self {}, other {}".format(self.min_age, other.min_age))
            return False
        if self.max_age != other.max_age:
            logging.getLogger(__name__).debug("max_age not equal, self {}, other {}".format(self.max_age, other.max_age))
            return False
        return True

    def __str__(self):
        return f"{self.min_age} to {self.max_age}"

    @staticmethod
    # can't use AgeClass in typing, thus List[Any]
    def get_age_class_for(year_of_construction: int, age_classes: Iterable[Any]):
        """
        Looks up age class. Raises Exception if no matching age class was found.

        :param year_of_construction: year in which building or element of building was created
        :param age_classes: all available age classes
        :return: age class out of passed age_classes which contains year_of_construction.
        """
        age_class_matched = [age_cl for age_cl in age_classes if age_cl.isInClass(year_of_construction)]
        if len(age_class_matched) != 1:
            raise Exception(f"no or several age classes found for {year_of_construction}")
        return age_class_matched[0]

    @staticmethod
    def are_age_classes_consecutive(all_age_classes: List[Any]):
        """
        all_age_classes: list of age classes to be checked
        """
        all_age_classes.sort(key=lambda x: x.min_age if x.min_age else 0, reverse=False)  # replace None with 0, as None means open range
        for i in range(len(all_age_classes) - 1):
            ac_older = all_age_classes[i]
            ac_newer = all_age_classes[i + 1]
            if not (ac_older.max_age and ac_newer.min_age and ac_older.max_age + 1 == ac_newer.min_age):
                return False
        return True

    @classmethod
    def from_string(cls, age_class_def: str):
        """
        Parses a string defining an age class. Following patterns are allowed:

        < 1918      => excludes 1918
        <= 1918     => includes 1918
        1918 - 1947 => includes 1919 and 1947
        > 1947      => excludes 1947
        >= 1947     => includes 1947

        Withespaces are ignored.
        """
        age_class_def = age_class_def.strip()

        min = None
        max = None

        parts = age_class_def.split("-")

        if len(parts) == 2:
            min = int(parts[0])
            max = int(parts[1])
        elif "<=" in age_class_def:  # must be before "<" test, otherwise already consumed by "<" check
            max = int(age_class_def[2:].strip())
        elif "<" in age_class_def:
            max = int(age_class_def[1:].strip()) - 1
        elif ">=" in age_class_def:  # must be before ">" test, otherwise already consumed by ">" check
            min = int(age_class_def[2:].strip())
        elif ">" in age_class_def:
            min = int(age_class_def[1:].strip()) + 1

        if not min and not max:
            raise Exception(f"could not init AgeClass for {age_class_def}")

        return cls(min_age=min, max_age=max)
