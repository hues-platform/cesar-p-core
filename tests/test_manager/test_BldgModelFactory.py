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
import shutil
import pandas as pd
from pathlib import Path
from cesarp.manager.BldgModelFactory import BldgModelFactory
import cesarp.common
from cesarp.model.EnergySource import EnergySource

def test_EnergySource_mapping():
    # test mapping between value as string, name as string or matlab cesar legacy number for energy carriers to
    # EnergySource
    KEY_DHW = "ECarrierDHW"
    KEY_HEATING = "ECarrierHeating"
    e_carriers_raw = pd.read_csv(str(os.path.dirname(__file__) / Path("./testfixture/BuildingECarriers.csv")),
                               index_col="ORIG_FID")
    e_carriers = e_carriers_raw.loc[:, [KEY_DHW, KEY_HEATING]].applymap(
        lambda x: EnergySource(x)
    )
    assert(e_carriers.loc[2, KEY_DHW]) == EnergySource.DHW_OTHER
    assert (e_carriers.loc[2, KEY_HEATING]) == EnergySource.HEATING_OTHER
    assert(e_carriers.loc[8, KEY_DHW]) == EnergySource.ELECTRICITY
    assert (e_carriers.loc[8, KEY_HEATING]) == EnergySource.HEATING_OIL

def test_factory_init():
    bldg_age_file = str(os.path.dirname(__file__) / Path("./testfixture/BuildingYearOfCreation.csv"))
    bldg_sia_type = str(os.path.dirname(__file__) / Path("./testfixture/BuildingSIAType.csv"))
    # test mapping between value as string, name as string or matlab cesar legacy number for energy carriers to
    # EnergySource
    bldg_e_carriers = str(os.path.dirname(__file__) / Path("./testfixture/BuildingECarriers.csv"))
    site_vertices = str(os.path.dirname(__file__) / Path("./testfixture/SiteVertices.csv"))
    weather = str(os.path.dirname(__file__) / Path("./testfixture/Zurich_1.epw"))
    config ={"MANAGER":
                 {
                     "BLDG_AGE_FILE": {"PATH": bldg_age_file},
                     "SITE_VERTICES_FILE": {"PATH": site_vertices},
                     "BLDG_TYPE_PER_BLDG_FILE": {"PATH": bldg_sia_type},
                     "BLDG_INSTALLATION_FILE": {"PATH": bldg_e_carriers},
                     "SINGLE_SITE": {"WEATHER_FILE": weather}
                 }
             }
    myFact = BldgModelFactory(cesarp.common.init_unit_registry(), config)

    assert myFact._site_factory != None
    assert myFact._glazing_ratio_provider == None # no per building glazing ratio, thus None
    assert myFact._bldg_operation_factory != None
    assert myFact._geometry_builder_factory != None
    assert myFact._neighbouring_bldg_constr_factory != None

    assert len(myFact.per_bldg_infos_used) == 9

    my_bldg_model = myFact.create_bldg_model(1)
    assert not my_bldg_model.bldg_operation_mapping.get_operation_for_floor(0).night_vent.is_active
    assert my_bldg_model.bldg_operation_mapping.get_operation_for_floor(0).win_shading_ctrl.is_active

