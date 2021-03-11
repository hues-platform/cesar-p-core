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
import logging
import os
import pytest
from pathlib import Path

import cesarp.common
from cesarp.model.EnergySource import EnergySource
from cesarp.idf_constructions_db_access.IDFConstructionArchetypeFactory import IDFConstructionArchetypeFactory

__test_config_path = os.path.dirname(__file__) / Path("./testfixture/test_config.yml")


def test_get_constructional_archetype():
    logging.getLogger().setLevel(logging.WARNING)
    local_cfg = cesarp.common.config_loader.load_config_full(__test_config_path)
    ureg = cesarp.common.init_unit_registry()
    bldg_fid = 1
    arch_fact = IDFConstructionArchetypeFactory({bldg_fid: 1910},
                                                {bldg_fid: EnergySource.SOLAR_THERMAL},
                                                {bldg_fid: EnergySource.HEATING_OIL},
                                                ureg,
                                                local_cfg)
    archetype_age_class_1 = arch_fact.get_archetype_for(bldg_fid)
    assert len(archetype_age_class_1.window_glass_constr._all_options) == 1
    assert archetype_age_class_1.window_frame_construction.frame_visible_absorptance.m == 0.5
    assert len(archetype_age_class_1.wall_constr._all_options) == 5
    assert archetype_age_class_1.glazing_ratio.get_default() == 0.13
    assert archetype_age_class_1.infiltration_rate.m == pytest.approx(0.55, abs=0.005)
    assert ureg.ACH == archetype_age_class_1.infiltration_rate.u


def test_chaching():
    local_cfg = cesarp.common.config_loader.load_config_full(__test_config_path)

    oil = EnergySource.HEATING_OIL
    el = EnergySource.ELECTRICITY
    solar = EnergySource.SOLAR_THERMAL
    arch_fact = IDFConstructionArchetypeFactory({1: 1910, 2: 1912, 3: 1980},
                                                {1: solar, 2: oil, 3: el},
                                                {1: el, 2: oil, 3: oil},
                                                cesarp.common.init_unit_registry(),
                                                local_cfg)
    arch_call_1 = arch_fact.get_archetype_for(1)
    arch_call_2 = arch_fact.get_archetype_for(2)
    arch_call_other_age_class = arch_fact.get_archetype_for(3)
    assert id(arch_call_1) == id(arch_call_2)
    assert id(arch_call_1) != id(arch_call_other_age_class)