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
from pathlib import Path
from shutil import copyfile
import multiprocessing as mp
import os


class RelativeAuxiliaryFilesHandler:
    """
    Copies exactly one time each file which is added by add_file() to the destination folder.
    If a file with the same name, but another source location is added, an exception is thrown.
    Instance of this class is multithreading save, as access to r/w member self.files_copied is protected with a lock.
    """

    def __init__(self):
        """
        Use set_destination to initialize.
        Setting folder path after initialization is necessary to be able to create an instance of this class handled by multiprocessing Manager,
        but not needing the folder path in the global environment.
        """
        self.files_copied_lock = mp.Lock()

    def set_destination(self, parent_folder, subfolder_name):
        """
        This method should only be called once!
        :param parent_folder: parent folder, profile pathes returned by add_file() will be relative to this parent folder
        :param subfolder_name: name of folder where files should be stored to, folder will be created as a child of parent_folder
        :return: nothing
        """
        self.initialized = True
        self.subfolder_name = subfolder_name
        self.files_copied = dict()  # full path, filename - to keep track which files were already added to destination folder
        self.dest_folder_path = parent_folder / Path(self.subfolder_name)
        os.makedirs(self.dest_folder_path)

    def add_file(self, src_file_path):
        """
        :param src_file_path:
        :return: path of the file in the destination folder, relative to the parant folder passed in the object initialization
        """
        assert self.initialized, "please call set_destination() before calling add_file()"
        file_name = Path(src_file_path).name
        copying_needed = False

        self.files_copied_lock.acquire()
        if src_file_path not in self.files_copied.keys():
            if file_name in self.files_copied.values():
                raise Exception(f"trying to add {src_file_path} to {self.dest_folder_path}, but file with same name already present.")
            else:
                self.files_copied[src_file_path] = file_name
                copying_needed = True
        self.files_copied_lock.release()

        dst_file_path = self.dest_folder_path / Path(file_name)
        if copying_needed:
            assert not os.path.exists(dst_file_path), f"trying to copy {src_file_path} to {dst_file_path}, but destination file already exists!"
            copyfile(src_file_path, dst_file_path)

        return self.subfolder_name / Path(file_name)
