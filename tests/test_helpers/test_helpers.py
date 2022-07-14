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
import filecmp
import os
import string
from fnmatch import fnmatch


def _filter(flist, skip):
    return [item for item in flist if not any(fnmatch(item, pat) for pat in skip)]


filecmp._filter = _filter


def compare_folders_recursivly(pathExpected, pathResult):
    foldersAreIdentical = True
    compareRes = filecmp.dircmp(pathExpected, pathResult, ignore=["*.xlsx", "*.html", "*.err"])

    if (
        compareRes.diff_files
        or compareRes.funny_files
        or compareRes.right_only
        or compareRes.left_only
    ):
        print("Files diff/funny:")
        print(compareRes.diff_files)
        print(compareRes.funny_files)
        print("Files only existing in one folder:")
        print(compareRes.right_only)
        print(compareRes.left_only)
        foldersAreIdentical = False
    for y in compareRes.common_dirs:
        print(y)
        if not compare_folders_recursivly(
            os.path.join(pathExpected, y), os.path.join(pathResult, y)
        ):
            foldersAreIdentical = False
    return foldersAreIdentical

def are_files_equal(file_result, file_expected, ignore_line_nrs=None, ignore_case=False, ignore_filesep_mismatch=False,
                    ignore_changing_config=False):
    if ignore_line_nrs is None:
        ignore_line_nrs = []
    res = list(open(file_result))
    exp = list(open(file_expected))
    if len(res) != len(exp):
        print("Files do not have equal number of lines! Result file has ", len(res), " expected files has ", len(exp))
        return False

    files_equal = True
    print()
    withspacedict = str.maketrans(dict.fromkeys(string.whitespace))
    file_sep_dict = str.maketrans("\\", "/")
    for i, res_line in enumerate(res):
        res_line_to_cmp = res_line.translate(withspacedict)
        exp_line_to_cmp = exp[i].translate(withspacedict)
        if ignore_case:
            res_line_to_cmp = res_line_to_cmp.upper()
            exp_line_to_cmp = exp_line_to_cmp.upper()
        if ignore_filesep_mismatch:
            res_line_to_cmp = res_line.translate(file_sep_dict)
            exp_line_to_cmp = exp[i].translate(file_sep_dict)
        if ignore_changing_config:
            keys_to_ignore = ["PATH", "WEATHER_FILE", "DATE_CREATED", "GIT-", "_FILE", "Version"]
            if any([to_ignore in res_line_to_cmp for to_ignore in keys_to_ignore]):
                print(f"Ignoring line nr with changing config {i+1}:\n{res_line_to_cmp}")
                continue
        if res_line_to_cmp != exp_line_to_cmp\
                and i+1 not in ignore_line_nrs:
            files_equal = False
            print("Line Nr ", i+1, "not ok")
            print(f'RESULT:\t\t {res_line.strip()}')
            print(f'EXPECTED:\t {exp[i].strip()}')

    return files_equal