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

from cesarp.manager.BldgModelFactory import BldgModelFactory
from cesarp.eplus_adapter.RelativeAuxiliaryFilesHandler import RelativeAuxiliaryFilesHandler
from cesarp.eplus_adapter.CesarIDFWriter import CesarIDFWriter
import cesarp.eplus_adapter
import cesarp.common


def run_single_bldg(bldg_fid: int, epw_file: str, idf_path: str, eplus_output_dir: str, custom_config, unit_reg=None):
    """
    Does run all the steps for the simulation for one building. Does not use multiprocessing.
    THIS IS NOT EFFICIENT TO SIMULATE MANY BUILINGS. The goal of this mehtod is to provide a way to debug the
    simulation for one building or for development purposes.

    :param bldg_fid: fid of the building to simulate
    :param epw_file: full path to weather file to use for simulation
    :param idf_path: full path where to save the generated IDF
    :param eplus_output_dir: full path to directory where EnergyPlus simulation output files are saved to
    :param custom_config: configuration parameters, either full path to config (path-like or str) or Dict[str, Any]
    """
    if not unit_reg:
        unit_reg = cesarp.common.init_unit_registry()
    if not isinstance(custom_config, dict):
        custom_config = cesarp.common.load_config_full(custom_config)
    bldg_models_factory = BldgModelFactory(unit_reg, custom_config)
    bldg_model = bldg_models_factory.create_bldg_model(bldg_fid)
    assert bldg_model is not None, "Bldg model could not be created. See logging output."
    prof_files_handler = RelativeAuxiliaryFilesHandler()
    prof_files_handler.set_destination(os.path.dirname(idf_path), "profiles")
    CesarIDFWriter(idf_path, unit_reg, custom_config=custom_config, profiles_files_handler=prof_files_handler).write_bldg_model(bldg_model)
    assert idf_path is not None, "IDF could not be created based on the Bldg model. See logging output."
    cesarp.eplus_adapter.eplus_sim_runner.run_single(idf_path, epw_file, eplus_output_dir, custom_config=custom_config)
    sim_res = cesarp.eplus_adapter.eplus_eso_results_handling.collect_cesar_simulation_summary(eplus_output_dir, unit_reg)
    print(sim_res)
    return sim_res
