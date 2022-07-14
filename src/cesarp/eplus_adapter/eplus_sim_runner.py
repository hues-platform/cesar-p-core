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
"""
Manages running simulations of IDF files with EnergyPlus.
In order to work a local EnergyPlus copy/installation is needed. The path to EnergyPlus is set in the
configuration or the environment variables.
To avoid reading configuration for each EnergyPlus call from disk there is the option for all methods to either pass
the custom/main configuration with only the project specific values or a fully loaded configuration dictionary for the
eplus_adapter package (parameter ep_config).
"""

import logging
import os
import platform
import sys
from subprocess import check_call, CalledProcessError
from six import StringIO
from typing import Dict, Any, Optional, Sequence

try:
    import multiprocessing as mp
except ImportError:
    pass

from cesarp.eplus_adapter import _default_config_file
from cesarp.common import config_loader

EPLUS_LOG_FILE_NAME = "eplusout.err"
EPLUS_MAIN_RES_FILE_NAME = "eplusout.eso"


def get_eplus_version(custom_config: Optional[Dict[str, Any]] = None, ep_config: Optional[Dict[str, Any]] = None):
    """
    Returns energy plus version
    When called from top level, e.g. to log used eplus version, make sure to pass custom/main config which was used for simulation run (important if EnergyPlus version is set in that custom configuration, which can always be the case...)

    :param ep_config: eplus adapter configuration (full, including custom configuration)
    :param custom_config: only custom configuration parameters, eplus adapter config will be loaded from disk and merged with custom config. Ignored if full_config is passed.
    :return: the energy plus version configured.
    """
    try:
        eplus_ver = os.environ["ENERGYPLUS_VER"]
        if eplus_ver:
            logging.getLogger(__name__).info(f"using energyplus version set in environment: {eplus_ver}")
            return eplus_ver
    except KeyError:  # if environment variable is not set, KeyError is raised
        pass

    if ep_config is None:
        ep_config = get_config(custom_config)

    eplus_ver = ep_config["EPLUS_VERSION"]
    logging.getLogger(__name__).info(f"using energyplus version set in config: {eplus_ver}")
    return eplus_ver


def get_idd_path(custom_config: Optional[Dict[str, Any]] = None, ep_config: Optional[Dict[str, Any]] = None):
    """
    Get Eplus IDD path.

    :param ep_config: eplus adapter configuration (full, including custom configuration)
    :param custom_config: only custom configuration parameters, eplus adapter config will be loaded from disk and merged with custom config. Ignored if full_config is passed.
    :raises EnergyPlusRunError: [description]
    :return: [description]
    :rtype: [type]
    """
    if ep_config is None:
        ep_config = get_config(custom_config)
    ep_version = get_eplus_version(ep_config=ep_config)
    if "8.5" in ep_version:
        idd_path = ep_config["CUSTOM_IDD_8_5"]
    # there is no reason that 8.6 is missing, I just didn't have the installtion
    elif "8.7" in ep_version:
        idd_path = ep_config["CUSTOM_IDD_8_7"]
    elif "8.8" in ep_version:
        idd_path = ep_config["CUSTOM_IDD_8_8"]
    elif "8.9" in ep_version:
        idd_path = ep_config["CUSTOM_IDD_8_9"]
    elif "9.0" in ep_version:
        idd_path = ep_config["CUSTOM_IDD_9_0"]
    # there is no reason that 9.1 is missing, I just didn't have the installtion
    elif "9.2" in ep_version:
        idd_path = ep_config["CUSTOM_IDD_9_2"]
    elif "9.3" in ep_version:
        idd_path = ep_config["CUSTOM_IDD_9_3"]
        # there is no reason that 9.1 is missing, I just didn't have the installtion
    elif "9.5" in ep_version:
        idd_path = ep_config["CUSTOM_IDD_9_5"]
    else:
        raise EnergyPlusRunError(
            f"CESAR-P does not support extended IDD for EnergyPlus version {ep_version}. See cesarp.eplus_adapter.eplus_sim_runner.py::get_idd_path for supported versions."
        )
    logging.getLogger(__name__).debug(f"using energyplus IDD {idd_path}")
    return idd_path


def get_eplus_executable(custom_config: Optional[Dict[str, Any]] = None, ep_config: Optional[Dict[str, Any]] = None) -> str:
    """
    Get the EnergyPlus install directory and executable path.

    :param ep_config: eplus adapter configuration (full, including custom configuration)
    :param custom_config: only custom configuration parameters, eplus adapter config will be loaded from disk and merged with custom config. Ignored if full_config is passed.
    :return: Full path to the EnergyPlus executable.
    """
    try:
        eplus_exe = os.environ["ENERGYPLUS_EXE"]
        if eplus_exe:
            logging.getLogger(__name__).info(f"using energyplus executable path set in environment: {eplus_exe}")
            return eplus_exe
    except KeyError:  # if environment variable is not set, KeyError is raised
        pass

    if ep_config is None:
        ep_config = get_config(custom_config)

    version = get_eplus_version(ep_config=ep_config).replace(".", "-")
    if platform.system() == "Windows":
        eplus_home = ep_config["EPLUS_WINDOWS_DEFAULT_PATH"].format(version=version)
        eplus_exe = os.path.join(eplus_home, "energyplus.exe")
    elif platform.system() == "Linux":
        eplus_home = ep_config["EPLUS_LINUX_DEFAULT_PATH"].format(version=version)
        eplus_exe = os.path.join(eplus_home, "energyplus")
    else:
        eplus_home = ep_config["EPLUS_MAC_DEFAULT_PATH"].format(version=version)
        eplus_exe = os.path.join(eplus_home, "energyplus")
    logging.getLogger(__name__).info(f"using energyplus default executable path set in configuration: {eplus_exe}")
    return eplus_exe


def run_single(idffile, epwfile, output_path, ep_config: Optional[Dict[str, Any]] = None, custom_config: Optional[Dict[str, Any]] = None):
    """
    :param idffile: IDF file to run simulation for (full path)
    :param epwfile: Weather file to use for simulation (full path)
    :param output_path: Folder where the EnergyPlus output is stored
    :param ep_config: eplus adapter configuration (full, including custom configuration)
    :param custom_config: only custom configuration parameters, eplus adapter config will be loaded from disk and merged with custom config. Ignored if full_config is passed.
    :return: None, result is stored to output_path
    """
    if ep_config is None:
        ep_config = get_config(custom_config)
    args = __get_eplus_run_args(output_path, ep_config)
    os.makedirs(output_path)
    __run_eplus(idf_path=str(idffile), weather=epwfile, ep_executable_path=get_eplus_executable(ep_config=ep_config), **args)


def run_batch(
    idf_files: Dict[int, Any],
    epw_files: Dict[int, Any],
    output_folders: Dict[int, Any],
    nr_of_parallel_workers,
    custom_config: Optional[Dict[str, Any]] = None,
):
    ep_config = get_config(custom_config)
    logger = logging.getLogger(__name__)
    simulation_list = list()
    eplus_executable = get_eplus_executable(custom_config=custom_config)
    for bldg_fid, idf_file in idf_files.items():
        try:
            if idf_file is not None:
                output_path_for_current = output_folders[bldg_fid]
                os.makedirs(output_path_for_current)
                args = __get_eplus_run_args(str(output_path_for_current), ep_config)
                simulation_list.append([(str(idf_file), epw_files[bldg_fid], eplus_executable), args])
            else:
                logger.warning(f"Not simulating {bldg_fid}, IDF file is None!")
        except Exception as ex:
            logger.warning(f"Not simulating {bldg_fid}, something missing or bad inputs")
            logger.exception(ex)

    __run_eplus_in_pool(simulation_list, nr_of_parallel_workers)


def get_config(custom_config: Optional[Dict[str, Any]] = None):
    return config_loader.load_config_for_package(_default_config_file, __package__, custom_config)


def __get_eplus_run_args(output_path, ep_config):
    return {
        "expandobjects": True,
        "output_directory": output_path,
        "idd": get_idd_path(ep_config=ep_config),
        "readvars": ep_config["DO_CREATE_CSV_RESULTS"],
        "verbose": "v" if ep_config["EPLUS_RUN_VERBOSE"] else "q",
    }


def __run_eplus_in_pool(jobs, processors):
    """
    adapted from eppy.run_function.runIDFs
    # Copyright (c) 2016 Jamie Bull
    # =======================================================================
    #  Distributed under the MIT License.
    #  (See accompanying file LICENSE or copy at
    #  http://opensource.org/licenses/MIT)
    # =======================================================================

    Run energy plus simulation on a worker pool. The method can only be called from a main process, so if you created CesarEPlusRunner in a subprocess this method will fail...

    :param: jobs : iterable
        A list or generator made up of an lisst [(idf_path, epw_path), kwargs] (see `cesarp.eplus_adpater.eplus_sim_runner.run_eplus` for valid keywords).
    :param: processors : int, optional
        Number of processors to run on (default: 1). If 0 is passed then
        the process will run on all CPUs, -1 means one less than all CPUs, etc.

    """
    if processors <= 0:
        processors = max(1, mp.cpu_count() + processors)

    # prepared_runs = (eppy.runner.prepare_run(run_id, run_data) for run_id, run_data in enumerate(jobs))
    try:
        pool = mp.Pool(processors)
        pool.map_async(__eplus_multirunner, jobs, error_callback=__trace_error)
        pool.close()
        pool.join()
    except NameError:
        # multiprocessing not present so pass the jobs one at a time
        for job in jobs:
            __eplus_multirunner(job)


def __trace_error(value):
    logging.error("Exception happened during EnergyPlus Simulation")
    logging.error(value)


def __run_eplus(
    idf_path: str,
    weather: str,
    ep_executable_path: str,
    idd: str = None,
    output_directory: str = "",
    annual: bool = False,
    design_day: bool = False,
    epmacro: bool = False,
    expandobjects: bool = False,
    readvars: bool = False,
    output_prefix: Optional[str] = None,
    output_suffix: Optional[str] = None,
    verbose: str = "v",
) -> None:
    """
    adapted from eppy.run_function.runIDFs
    # Copyright (c) 2016 Jamie Bull
    # =======================================================================
    #  Distributed under the MIT License.
    #  (See accompanying file LICENSE or copy at
    #  http://opensource.org/licenses/MIT)
    # =======================================================================

    Wrapper around the EnergyPlus command line interface.

    :param idf_path: full path to the IDF file to be run
    :param weather: full path to the weather file.
    :param ep_executable_path: full path of energy plus executable
    :param idd: optional, Input data dictionary (default: Energy+.idd in EnergyPlus directory)
    :param output_directory: Full or relative path to an output directory (default: 'run_outputs)
    :param annual: If True then force annual simulation (default: False)
    :param design_day: Force design-day-only simulation (default: False)
    :param epmacro: Run EPMacro prior to simulation (default: False).
    :param expandobjects: Run ExpandObjects prior to simulation (default: False)
    :param readvars: Run ReadVarsESO after simulation (default: False)
    :param output_prefix: Prefix for output file names (default: eplus)
    :param output_suffix: Suffix style for output file names (default: L)
                          L: Legacy (e.g., eplustbl.csv), C: Capital (e.g., eplusTable.csv), D: Dash (e.g., eplus-table.csv)
    :param verbose: Set verbosity of runtime messages (default: v)
                    v: verbose, q: quiet
    :return: Nothing if everything did run,  otherwise Exception is raised
    """
    args = locals().copy()
    # get unneeded params out of args ready to pass the rest to energyplus.exe
    verbose = args.pop("verbose")
    idf_path = str(args.pop("idf_path"))
    ep_executable_path = str(args.pop("ep_executable_path"))
    args["idd"] = str(args["idd"])
    args["output_directory"] = str(args["output_directory"])
    if not os.path.isfile(idf_path):
        raise EnergyPlusRunError("ERROR: Could not find input data file: {}".format(idf_path))

    # convert paths to absolute paths if required
    if not os.path.isfile(args["weather"]):
        raise EnergyPlusRunError(f"Wheater File {args['weather']} not found.")

    # store the directory we start in, switch to output_directory which is necessary on linux to have the expandobjects writing the expanded idf to the this folder...
    cwd = os.getcwd()
    os.chdir(args["output_directory"])

    # build a list of command line arguments
    cmd = [ep_executable_path]
    for arg in args:
        if args[arg]:
            if isinstance(args[arg], bool):
                args[arg] = ""
            cmd.extend(["--{}".format(arg.replace("_", "-"))])
            if args[arg] != "":
                cmd.extend([args[arg]])
    cmd.extend([idf_path])

    # send stdout to tmp filehandle to avoid issue #245
    tmp_err = StringIO()
    sys.stderr = tmp_err
    try:
        if verbose == "v":
            print("\r\n" + " ".join(cmd) + "\r\n")
            check_call(cmd)
        elif verbose == "q":
            check_call(cmd, stdout=open(os.devnull, "w"))
    except CalledProcessError:
        message = __parse_error(tmp_err, args["output_directory"])
        raise EnergyPlusRunError(message)
    except Exception as e:
        raise EnergyPlusRunError(f"\r\nEnergyPlus command: {' '.join(cmd)}\r\n", e)
    finally:
        sys.stderr = sys.__stderr__
        os.chdir(cwd)


def __eplus_multirunner(args: Sequence[Any]):
    """
    copied from eppy.run_function.runIDFs
    # Copyright (c) 2016 Jamie Bull
    # =======================================================================
    #  Distributed under the MIT License.
    #  (See accompanying file LICENSE or copy at
    #  http://opensource.org/licenses/MIT)
    # =======================================================================

    Wrapper for run_eplus() to be used when running IDF and EPW runs in parallel.
    :param args: A list made up of a two-item list (IDF and EPW) and a kwargs dict.

    """
    __run_eplus(*args[0], **args[1])


def __parse_error(tmp_err, output_dir):
    """
    copied from eppy.run_function.runIDFs
    # Copyright (c) 2016 Jamie Bull
    # =======================================================================
    #  Distributed under the MIT License.
    #  (See accompanying file LICENSE or copy at
    #  http://opensource.org/licenses/MIT)
    # =======================================================================

    Add contents of stderr and eplusout.err and put it in the exception message.

    :param tmp_err: file-like
    :param output_dir: str
    :param cmd: list, containing called command parts
    :return: str
    """
    std_err = tmp_err.getvalue()
    err_file = os.path.join(output_dir, "eplusout.err")
    if os.path.isfile(err_file):
        with open(err_file, "r") as f:
            ep_err = f.read()
    else:
        ep_err = "<File not found>"
    message = "\r\n{std_err}\r\nContents of EnergyPlus error file at {err_file}\r\n{ep_err}".format(**locals())
    return message


class EnergyPlusRunError(Exception):
    pass
