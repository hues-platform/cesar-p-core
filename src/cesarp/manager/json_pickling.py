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
from typing import Any
import json
from importlib.metadata import version
import jsonpickle
import jsonpickle.ext.pandas
import jsonpickle.ext.numpy

from cesarp.manager.BuildingContainer import BuildingContainer
from cesarp.common.CesarpException import CesarpException


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
    # encode and decode with make_refs=False allows for json serialized files really
    # independent of the pickling method. With make_refs=True there are magic py/id for id-identical objects...
    # Befor jsonpickling version 2.0.0 setting make_refs=False failed becasue then a object that was previously
    # encoded with a py/id then is a string instead of proper object
    # With jsonpickling 2.0.0 it works. The backward-compatibility test files do work as well, so I hope projects
    # which have building models safed with jsonpickling prior to 2.0.0 with make_refs set to True will still be loaded
    json_string = jsonpickle.encode(obj_to_save, keys=True, unpicklable=True, make_refs=False)
    with open(filepath, "w") as fh:
        fh.write(json_string)


def read_from_disk(filepath: str) -> Any:
    prepare_pickler()
    with open(filepath, "r") as fh:
        json_string = fh.read()
    return jsonpickle.decode(json_string, keys=True, safe=True)


def is_jsonpickle_incompatible(filepath: str) -> bool:
    with open(filepath, "w") as fh:
        json_string = fh.read()
    raw_json = json.loads(json_string)
    return ("container_version" not in raw_json["container"] or raw_json["container"]["container_version"] < 4) and (int(version("jsonpickle").split(".")[0]) >= 2)


def read_bldg_container_from_disk(filepath: str) -> BuildingContainer:
    try:
        bldg_cont = read_from_disk(filepath)
    except Exception as ex:
        if is_jsonpickle_incompatible:
            raise CesarpException(
                f"You try to load a serialized BuildingContainer from {filepath}. \
The container was serialized using a jsonpickle library version below 2.0.0, which is not compatible with the cesar-p {version('cesar-p')} \
respectively jsonpickle version {version('jsonpickle')} isntalled. \
Either you install cesar-p version < 2.0.0, or if you need some functionalities from cesar-p version 2 or above you can try to manually \
downgrade jsonpickle with pip install jsonpickle==1.5.2 and ignore warnings that cesar-p requires jsonpickle versin xxx"
            )
        else:
            raise ex

    assert isinstance(bldg_cont, BuildingContainer)
    bldg_cont.upgrade_if_necessary()
    return bldg_cont
