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
import pytest
from pathlib import Path
import shutil

from cesarp.eplus_adapter.RelativeAuxiliaryFilesHandler import RelativeAuxiliaryFilesHandler

_TESTDEST_PATH = os.path.dirname(__file__) / Path("testdest")

_EFH_PROFILES_PATH_SRC = os.path.dirname(__file__) / Path("./testfixture/aux_file_handler/EFH/profiles.csv")
_MFH_PROFILES_PATH_SRC = os.path.dirname(__file__) / Path("./testfixture/aux_file_handler/MFH/profiles.csv")
_MFH_PROFILES_VAR_1_PATH_SRC = os.path.dirname(__file__) / Path("./testfixture/aux_file_handler/MFH/profiles_var_1.csv")
_MFH_PROFILES_VAR_1_PATH_DEST = _TESTDEST_PATH / Path("./profiles/profiles_var_1.csv")
_MFH_PROFILES_VAR_2_PATH_SRC = os.path.dirname(__file__) / Path("./testfixture/aux_file_handler/MFH/profiles_var_2.csv")
_MFH_PROFILES_VAR_2_PATH_DEST = _TESTDEST_PATH / Path("./profiles/profiles_var_2.csv")



@pytest.fixture
def testdest():
    testdest = Path(_TESTDEST_PATH)
    yield testdest
    shutil.rmtree(testdest)

def test_saving_basic(testdest):
    aux_files_handler = RelativeAuxiliaryFilesHandler()
    aux_files_handler.set_destination(testdest, "profiles")
    rel_path_var_1 = aux_files_handler.add_file(_MFH_PROFILES_VAR_1_PATH_SRC)
    assert rel_path_var_1 == Path("profiles/profiles_var_1.csv")
    rel_path_var_1 = aux_files_handler.add_file(_MFH_PROFILES_VAR_1_PATH_SRC) # try adding same file again, that should be possible
    assert rel_path_var_1 == Path("profiles/profiles_var_1.csv")
    assert os.path.isfile(_MFH_PROFILES_VAR_1_PATH_DEST)
    rel_path_var_2 = aux_files_handler.add_file(_MFH_PROFILES_VAR_2_PATH_SRC)
    assert rel_path_var_2 == Path("profiles/profiles_var_2.csv")
    assert os.path.isfile(_MFH_PROFILES_VAR_2_PATH_DEST)


def test_save_clashing_name(testdest):
    with pytest.raises(Exception):
        aux_files_handler = RelativeAuxiliaryFilesHandler()
        aux_files_handler.set_destination(testdest, "profiles")
        rel_path_efh = aux_files_handler.add_file(_EFH_PROFILES_PATH_SRC)
        rel_path_mfh = aux_files_handler.add_file(_MFH_PROFILES_PATH_SRC)