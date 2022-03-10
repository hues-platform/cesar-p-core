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
import os
import cesarp.common
from cesarp.retrofit.RetrofitLog import RetrofitLog
from cesarp.model.BuildingElement import BuildingElement

def test_basic_log():
    ureg = cesarp.common.init_unit_registry()
    myLogger = RetrofitLog()
    myLogger.log_retrofit_measure(bldg_fid=33,
                                  bldg_element=BuildingElement.WINDOW,
                                  retrofitted_area=200*ureg.m**2,
                                  year_of_retrofit=2020,
                                  retrofit_target="SIA380_MIN",
                                  costs=200*ureg.CHF/ureg.m**2,
                                  non_renewable_pen=0.02 *ureg.MJ*ureg.Oileq/ureg.m**2,
                                  co2_emission=3 * ureg.kg * ureg.CO2eq / ureg.m**2,
                                  old_construction_name="bad_construction",
                                  new_construction_name="good_construction",
                                  )
    assert(len(myLogger.my_log_entries) == 1) 
    assert(len(myLogger.convert_to_df()) == 1)
    the_log = "test_retrofit_log.csv"
    myLogger.save(the_log)
    assert os.path.isfile(the_log)
    os.remove(the_log)

def test_retrofitted_in():
    ureg = cesarp.common.init_unit_registry()
    myLogger = RetrofitLog()
    # empty log
    assert myLogger.was_construction_retrofitted_in(2022) == False
    myLogger.log_retrofit_measure(bldg_fid=22,
                                  bldg_element=BuildingElement.ROOF,
                                  retrofitted_area=100*ureg.m**2,
                                  year_of_retrofit=2020,
                                  retrofit_target="SIA380_MIN",
                                  costs=200 * ureg.CHF / ureg.m ** 2,
                                  non_renewable_pen=0.02 * ureg.MJ * ureg.Oileq / ureg.m ** 2,
                                  co2_emission=3 * ureg.kg * ureg.CO2eq / ureg.m ** 2,
                                  old_construction_name="bad_construction",
                                  new_construction_name="good_construction",
                                  )

    assert myLogger.was_construction_retrofitted_in(2022) == False
    assert myLogger.was_construction_retrofitted_in(2020) == True
    assert myLogger.was_construction_retrofitted_in(year=2022, bldg_fid=22) == False
    assert myLogger.was_construction_retrofitted_in(year=2020, bldg_fid=22) == True
    assert myLogger.was_construction_retrofitted_in(year=2020, bldg_fid=33) == False