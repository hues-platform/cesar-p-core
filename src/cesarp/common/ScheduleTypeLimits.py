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
class ScheduleTypeLimits:
    def __init__(self, name, min_value, max_value, value_type):
        self.name = name
        self.min_value = min_value
        self.max_value = max_value
        self.value_type = value_type

    @classmethod
    def ON_OFF(cls):
        return cls("ON_OFF", 0, 1, int)

    @classmethod
    def FRACTION(cls):
        return cls("FRACTION", 0.0, 1.0, float)

    @classmethod
    def CONTROL_TYPE(cls):
        return cls("CONTROL_TYPE", 0, 4, int)

    @classmethod
    def TEMPERATURE(cls):
        return cls("TEMPERATURE", -60, 200, int)

    @classmethod
    def ANY(cls):
        return cls("ANY", None, None, None)

    @classmethod
    def get_limits_by_name(cls, name):
        try:
            return getattr(cls, name)()
        except AttributeError:
            raise Exception(f"{__class__} does not support type {name}")

    @classmethod
    def get_limits_base_on_profile(cls, profile, ureg):
        """
        Get the best fitting description of the profile's values as a ScheduleTypeLimit object.
        For a profile with all values 1 or 0 type FRACTION is assigned (it could also be of type ON_OFF, but there is not way to
        resolve which of the two is correct, so FRACTION is always used meaning that this method never returns a type ON_OFF)
        :param profile:
        :param ureg:
        :return:
        """
        try:
            unit = profile[0].u
            values = [val.m for val in profile]
        except AttributeError:
            unit = None
            ureg = None
            values = profile

        if ureg and unit == ureg.degreeC:
            limits = cls.TEMPERATURE()
        # elif all([val == 1 or val == 0 for val in values]):
        #    limits = cls.ON_OFF()
        elif all([val <= 1 and val >= 0 for val in values]):
            if not unit or unit.dimensionless:
                limits = cls.FRACTION()
            else:
                limits = cls.ANY()
        elif all([val in [0, 1, 2, 3, 4] for val in values]):
            limits = cls.CONTROL_TYPE()
        else:
            limits = cls.ANY()

        return limits

    def __hash__(self):
        return hash((self.name, self.min_value, self.max_value, self.value_type))

    def __eq__(self, other) -> bool:
        if self.name != other.name:
            return False
        if self.min_value != other.min_value:
            return False
        if self.max_value != other.max_value:
            return False
        if self.value_type != other.value_type:
            return False
        return True
