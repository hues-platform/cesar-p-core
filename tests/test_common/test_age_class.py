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
from cesarp.common.AgeClass import AgeClass

def test_age_class_init_from_string():
    the_ac = AgeClass.from_string(" < 1918")
    assert the_ac.min_age == None
    assert the_ac.max_age == 1917

    the_ac = AgeClass.from_string("<=1922")
    assert the_ac.min_age == None
    assert the_ac.max_age == 1922

    the_ac = AgeClass.from_string("1918-1947")
    assert the_ac.min_age == 1918
    assert the_ac.max_age == 1947

    the_ac = AgeClass.from_string(" 1955  -2020")
    assert the_ac.min_age == 1955
    assert the_ac.max_age == 2020

    the_ac = AgeClass.from_string(">2050")
    assert the_ac.min_age == 2051
    assert the_ac.max_age == None

    the_ac = AgeClass.from_string(">= 2050")
    assert the_ac.min_age == 2050
    assert the_ac.max_age == None

def test_age_classes_consecutive_ok():
    myAgeClasses = [
            AgeClass(None, 1918),
            AgeClass(1919, 1925),
            AgeClass(1926, None)            
    ]
    assert AgeClass.are_age_classes_consecutive(myAgeClasses)

def test_age_classes_consecutive_ok_fully_defined():
    myAgeClasses = [
            AgeClass(1900, 1918),
            AgeClass(1919, 1925),
            AgeClass(1926, 1933)            
    ]
    assert AgeClass.are_age_classes_consecutive(myAgeClasses)

def test_age_classes_consecutive_gap():
    myAgeClasses = [
        AgeClass(None, 1918),
        AgeClass(1919, 1925),
        AgeClass(1926, 1933),
        AgeClass(1935, None)  # it's not consecutive here, gap of 2 years
    ]
    assert AgeClass.are_age_classes_consecutive(myAgeClasses) == False

def test_age_classes_consecutive_overlap():
    myAgeClasses = [
        AgeClass(1900, 1918),
        AgeClass(1919, 1925),
        AgeClass(1922, None)  # overlap here!
    ]
    assert AgeClass.are_age_classes_consecutive(myAgeClasses) == False

def test_age_classes_consecutive_open_range_max():
    myAgeClasses = [
        AgeClass(1900, 1918),
        AgeClass(1919, None),  # open range in between!
        AgeClass(1921, None) 
    ]
    assert AgeClass.are_age_classes_consecutive(myAgeClasses) == False

def test_age_classes_consecutive_open_range_min():
    myAgeClasses = [
        AgeClass(1900, 1918),
        AgeClass(None, 1933),  # open range in between!
        AgeClass(1934, None) 
    ]
    assert AgeClass.are_age_classes_consecutive(myAgeClasses) == False    