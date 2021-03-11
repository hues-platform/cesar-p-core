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
from typing import Any
import jsonpickle
import jsonpickle.ext.pandas
import jsonpickle.ext.numpy
from cesarp.manager.BuildingContainer import BuildingContainer


def prepare_pickler():
    jsonpickle.ext.pandas.register_handlers()
    jsonpickle.ext.numpy.register_handlers()
    jsonpickle.set_encoder_options("json", sort_keys=True, indent=4)


def save_to_disk(obj_to_save, filepath: str):
    """
    You can actually use this method to serialize any object. intention for CESAR-P is to serialize
    BuildingContainer objects
    """
    prepare_pickler()
    # TODO can we encode and decode without make_refs=True? That would make the json building files really
    #  independent of the pickling method because with the make_refs there are magic py/id for id-identical objects...
    #  Setting make_refs=False fails becasue then a object that was previously encoded with a py/id then is a string
    #  instead of proper object
    json_string = jsonpickle.encode(obj_to_save, keys=True, unpicklable=True, make_refs=True)
    with open(filepath, "w") as fh:
        fh.write(json_string)


def read_from_disk(filepath: str) -> Any:
    prepare_pickler()
    with open(filepath, "r") as fh:
        json_string = fh.read()
    return jsonpickle.decode(json_string, keys=True)


def read_bldg_container_from_disk(filepath: str) -> BuildingContainer:
    bldg_cont = read_from_disk(filepath)
    assert isinstance(bldg_cont, BuildingContainer)
    bldg_cont.upgrade_if_necessary()
    return bldg_cont
