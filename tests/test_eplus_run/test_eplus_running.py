# coding=utf-8
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
configuration, which you can overwrite with passing a custom_config when initializing this class.
"""

import logging
import os
import platform
from pathlib import Path
import sys
import shutil
from subprocess import check_call, CalledProcessError
from six import StringIO
from typing import Dict, Any, Optional, Sequence
import pytest

def __trace_error(value):
    logging.error("Exception happened during EnergyPlus Simulation")
    logging.error(value)


def run_eplus(
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
    finally:
        sys.stderr = sys.__stderr__
        os.chdir(cwd)


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

def abs_path(path, basepath) -> str:
    """
    Converts given path to an absolute path. If path exists and is relative to current execution directory,
    the latter is used to create the absolute path. If path does not exist and is relative, "basepath" is prepended
    to form the absolute path.

    :param path: path to file or directory, which will be converted to an absolute one if not already the case
    :param basepath: can either be a directory path or a file path, for the latter filename will be ignored
    """
    if os.path.exists(path):
        return str(os.path.abspath(path))
    elif os.path.isabs(path):
        return str(path)
    else:
        if os.path.isfile(basepath):
            basepath = os.path.abspath(os.path.dirname(basepath))
        return str(basepath / Path(path))


def __abs_path(path):
    return abs_path(path, os.path.abspath(__file__))

# Test can be used for debugging if you want to check if EnergyPlus Installation on CI system works correctly
@pytest.mark.skipif(sys.platform == "win32", reason="E+ pathes setup for gitlab-CI run")
def test_eplus():
    out_dir = __abs_path("./eplus_out")
    shutil.rmtree(out_dir, ignore_errors = True)
    os.mkdir(out_dir)
    #eplus_path = "C:/EnergyPlusV8-5/"
    eplus_path = "/usr/local/bin"
    eplus_exe = eplus_path / Path("EnergyPlus")
    idd_path = eplus_path / Path("Energy+.idd")
    run_eplus(idf_path=__abs_path("./test.idf"),
                weather=__abs_path("./Zurich_1.epw"),
                idd=idd_path,
                ep_executable_path=eplus_exe,
                output_directory=out_dir,
                expandobjects=True,
                verbose="v")
    assert os.path.exists(out_dir / Path("eplustbl.csv"))
