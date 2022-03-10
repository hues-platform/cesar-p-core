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
import importlib.metadata
import subprocess
import sys
from platform import python_version
import os


def get_git_describe():
    return pretty_str(subprocess.run(["git", "describe", "--long"], capture_output=True, text=True).stdout)


def get_git_remote():
    return pretty_str(subprocess.run(["git", "remote", "get-url", "origin"], capture_output=True, text=True).stdout)


def get_git_branch():
    return pretty_str(subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True).stdout)


def get_cesarp_version():
    return importlib.metadata.version("cesar-p")


def get_version_info():
    info = dict()
    info["Cesar-P Version"] = get_cesarp_version()
    try:
        info["GIT-INFO"] = get_git_describe()
        info["GIT-BRANCH"] = get_git_branch()
        info["GIT-REMOTE"] = get_git_remote()
    except Exception:
        pass  # when cesar-p is not installed for development git might not be installed
        info["GIT-INFO"] = None
        info["GIT-BRANCH"] = None
        info["GIT-REMOTE"] = None
    return info


def pretty_str(the_str):
    return the_str.replace("\n", "").replace("'", "")


def __get_script_location():
    return os.path.dirname(os.path.realpath(__file__))


def is_git_clone():
    script_location = __get_script_location()
    return subprocess.call(["git", "status"], stderr=subprocess.STDOUT, stdout=open(os.devnull, "w"), cwd=script_location) == 0


def is_poetry_installed():
    return subprocess.run(["poetry", "-V"], shell=True, cwd=get_git_clone_root()).returncode == 0


def get_git_clone_root():
    if is_git_clone():
        script_location = __get_script_location()
        return subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, cwd=script_location).stdout.decode("utf-8").strip()
    else:
        return None


def get_git_extended_status(fd_git_infos):
    basic_infos = get_version_info()
    print(basic_infos, file=fd_git_infos)
    fd_git_infos.flush()
    if basic_infos["GIT-INFO"]:
        command_to_file(["git", "status"], fd_git_infos)
        command_to_file(["git", "diff"], fd_git_infos)
        command_to_file(["git", "diff", "origin"], fd_git_infos)
    else:
        print(
            "CESAR-P seems to be installed as a package, as not git reference can be found or no GIT CLI is properly installed on the system...",
            file=fd_git_infos,
        )


def command_to_file(git_command_args, fd):
    write_title(" ".join(git_command_args), fd)
    subprocess.call(git_command_args, stderr=fd, stdout=fd)


def get_env_info(file_descriptor):
    write_title("CESAR-P Version", file_descriptor)
    file_descriptor.writelines(f"{get_cesarp_version()}")
    if is_git_clone():
        file_descriptor.writelines("\nCESAR-P run from local git clone, there might be local changes!\n")
    write_title("OS", file_descriptor)
    file_descriptor.writelines(f"{sys.platform}\n")
    write_title("Python version", file_descriptor)
    file_descriptor.writelines(get_python_version())
    file_descriptor.writelines("Full version info: " + sys.version)
    file_descriptor.write("\n")
    if is_poetry_installed():
        write_title("poetry version", file_descriptor)
        subprocess.run(["poetry", "-V"], shell=True, stdout=file_descriptor)


def get_python_version():
    return python_version()


def write_title(title, fd):
    fd.write(f"\n============ {title} ============\n\n")
    fd.flush()


def write_python_pip_freeze(file_descriptor):
    subprocess.call(["pip", "freeze"], stdout=file_descriptor)
