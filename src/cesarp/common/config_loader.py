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
Keep an eye on handling relative pathes. When loading the configuration all detected relative pathes are converted to absolute ones. The detection relies on some keywords of the config keys and values, such as known file extensions. Details see cesarp.common.config_loader.
"""
from typing import Any, List, Dict, Union, Optional
import logging
import yaml
import os
import pkgutil
import importlib
from pathlib import Path
from cesarp.common.CesarpException import CesarpException

_PATH_IDENTIFIERS_IN_VALUE = [".csv", ".idf", ".txt", ".xls", ".xlsx", ".epw", ".yml"]
_PATH_IDENTIFIERS_IN_KEY = ["PATH", "FILE", "path", "file", "DIR", "dir", "FOLDER", "folder", "IDD"]

__YAML_SEPARATOR = "---\n"


class DuplicateConfigKeyException(CesarpException):
    def __init__(self, duplicated_key, cfg_file_path):
        super().__init__(f"{duplicated_key} exists twice in your YAML configuration file {cfg_file_path}")
        self.duplicated_key = duplicated_key
        self.cfg_file_path = cfg_file_path


# special loader with duplicate key checking
class UniqueKeyLoader(yaml.SafeLoader):
    def construct_mapping(self, node, deep=False):
        mapping = []
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if key not in mapping:
                mapping.append(key)
            else:
                raise DuplicateConfigKeyException(key, "")
        return super().construct_mapping(node, deep)


def load_config_for_package(cfg_file_name, full_package_name, custom_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Loads the parameters for given package from the configuration file and custom config

    :param cfg_file_name: absolute path (full path) to configuration file
    :param full_package_name: name of the package for which to get the configuration entries
    :param custom_config: dict of dict of... containing custom configuration entries, which overwrite the ones from
            the config file passed as first parameter. can contain entries belonging to other packages as well, but just
            the ones for full_package_name are considered.
    :return: dict with configuration entries for the package given. might be hierarchical, thus having another dict
                as entry
    """
    if custom_config is None:
        custom_config = {}
    package_name_parts: List[str] = full_package_name.split(".")
    default_cfg: Dict[str, Any] = load_config_full(cfg_file_name)
    default_cfg_for_pckg: Dict[str, Any] = __get_config_for_package(default_cfg, package_name_parts)
    custom_cfg_for_pckg: Dict[str, Any] = __get_config_for_package(custom_config, package_name_parts)
    return merge_config_recursive(default_cfg_for_pckg, custom_cfg_for_pckg)


def __get_config_for_package(cfg_dict: Dict[str, Any], package_name_parts: List[str]):
    """
    Lookup configuration for package recursively trying to get entry for parent package if there is none for the last package in package_name_parts
    """

    pckg_key = package_name_parts[-1].upper()
    if pckg_key in cfg_dict:
        return cfg_dict[pckg_key]
    elif len(package_name_parts) > 1:
        parent_pckg_cfg = __get_config_for_package(cfg_dict, package_name_parts[0:-1])
        if parent_pckg_cfg is not None:
            if pckg_key in parent_pckg_cfg:
                return parent_pckg_cfg[pckg_key]
    else:
        return None


def merge_config_recursive(default: Dict[str, Any], custom: Dict[str, Any]):
    if not custom or custom is None:
        return default

    res_dict = custom.copy()  # shallow copy, but it's ok for our case
    for key, default_entry in default.items():
        if key in custom:
            if isinstance(default_entry, dict) and isinstance(custom[key], dict):
                res_dict[key] = merge_config_recursive(default_entry, custom[key])
            else:
                res_dict[key] = custom[key]
        else:
            res_dict[key] = default_entry

    return res_dict


def load_config_full(cfg_file_name, ignore_metadata=True) -> Dict[str, Any]:
    """
    Load all entries form given file. Convert relative path or file declarations to absolute pathes using the
    path of the configuration file as base
    """
    logging.getLogger(__name__).debug("loading config from: %s", cfg_file_name)
    with open(cfg_file_name, "r", encoding="utf-8") as ymlfile:
        try:
            cfg = yaml.load(ymlfile, Loader=UniqueKeyLoader)
        except DuplicateConfigKeyException as ex:
            raise DuplicateConfigKeyException(ex.duplicated_key, cfg_file_name)
    __convert_entries_to_abs_pathes(cfg, os.path.abspath(os.path.dirname(cfg_file_name)))
    if ignore_metadata:
        try:
            del cfg["METADATA"]
        except Exception:
            pass  # never mind if METADATA did not exist
    return cfg


def __convert_entries_to_abs_pathes(config_dict: Dict[str, Any], basepath: str) -> None:
    """
    Converts relative pathes in the config dict to absolute pathes using given basepath as base dir for the relative
    pathes defined.
    Config entries with either PATH/path, FILE/file, DIR/dir in the key or .csv, .idf, .txt, .xls, .xlsx,
    .epw in the value string are considered as path entries
    ! ATTENTION does manipulate config dict in place!
    :param config_dict: dictionary with config entries, non-path entries are ignored
    :param basepath: path to use as prefix for all pathes defined relative
    :return: nothing, it does manipulate config_dict in place
    """
    for key, value in config_dict.items():
        if isinstance(value, dict):
            __convert_entries_to_abs_pathes(config_dict[key], basepath)
        else:
            if isinstance(value, str):
                key_keywords = _PATH_IDENTIFIERS_IN_KEY
                value_keywords = _PATH_IDENTIFIERS_IN_VALUE
                if "REL" not in key and "rel" not in key:
                    if any(([True if keyword in key else False for keyword in key_keywords])) or any(([True if keyword in value else False for keyword in value_keywords])):
                        config_dict[key] = abs_path(value, basepath)


def abs_path(path: Union[str, Path], basepath: Union[str, Path]) -> str:
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


def save_config_to_file(config: Dict[str, Any], filepath: Union[str, Path]):
    """
    Write config entries to file in YAML format.

    param: config configuration entries to be saved
    param: filepath file with full path to save config to, if file exists it will be overwritten!
    """
    with open(filepath, "w") as fd:
        yaml.dump(config, fd)


def combine_configs(all_cfg_files: List[str]):
    all_config_dict: Dict[str, Any] = {}
    for cfg_file in all_cfg_files:
        cfg_entries = load_config_full(cfg_file, ignore_metadata=False)
        if any(k in all_config_dict for k in cfg_entries.keys()):
            all_config_dict = merge_config_recursive(all_config_dict, cfg_entries)
        else:
            all_config_dict.update(cfg_entries)
    return all_config_dict


def validate_custom_cesarp_config(custom_config_to_validate: Dict[str, Any], the_logger: logging.Logger = logging.getLogger(__name__)):
    return validate_custom_config(get_config_file_pathes("cesarp"), custom_config_to_validate, the_logger)


def validate_custom_config(
    all_cfg_files: List[str],
    custom_config_to_validate: Dict[str, Any],
    the_logger: logging.Logger = logging.getLogger(__name__),
):
    """
    Checks if all the entries in the custom_config_to_validate are valid keys be searching them in all the default configuration entries.
    The default configuration entries are loaded from all the file config file pathes passed with all_cfg_files

    :param all_cfg_files ([type]): pathes of all configuration files against which to validate
    :param custom_config_to_validate: custom resp main configuration dictionary to be validated
    :param the_logger: logger instance to log invalid entries to; in case you do not want automatic log output, pass None

    Returns:
        [type]: [description]
    """
    all_default_config = combine_configs(all_cfg_files)
    wrong_entries = _compare_dicts(all_default_config, custom_config_to_validate)
    if wrong_entries:
        (corrected_entries, not_found_keys) = _find_possible_position_for(wrong_entries, all_default_config)
        if the_logger:
            the_logger.error(f"Sorry, your main configuration seems not valid, check following entries:\n{yaml.dump(wrong_entries)}")
            if corrected_entries:
                the_logger.error(f"For following entries, the correct hierarchy MIGHT be (attention, it might also be totally wrong):\n{yaml.dump(corrected_entries)}")
            if not_found_keys:
                the_logger.error(f"Those keys were not found at all:\n{yaml.dump(not_found_keys)}")
        return (wrong_entries, corrected_entries, not_found_keys)
    return ({}, {}, {})


def _find_possible_position_for(wrong_entries: Dict[str, Any], all_cfg: Dict[str, Any]):
    """
    Iterates through the available configuratio entries (all_cfg) to find a matching key.
    In case of keys that are reused as subkeys under several parent-keys, that result might lead to a wrong suggestion...

    :param wrong_entries: dictionary with the configuration entries that do not match to the given config structure
    :param all_cfg_files: list with all default config files holding all available configuration parameters

    Returns: dictionary with a suggested positioning for the wrong_entries, in case the key given is found at any other level in the dict
    """
    corrected_entries: Dict[str, Any] = {}
    keys_not_found: Dict[str, Any] = {}
    for key, value in wrong_entries.items():
        print(f"wrong entry {key}: {value}")
        if isinstance(value, dict):
            (subdict_corrected, subdict_not_found) = _find_possible_position_for(value, all_cfg)
            if subdict_not_found:
                keys_not_found[key] = subdict_not_found
            else:
                corrected_entries.update(subdict_corrected)
        else:
            correct_entry_path = _find_key(key, all_cfg)
            if correct_entry_path:
                corrected_entries.update(correct_entry_path)
            else:
                keys_not_found[key] = value
    return (corrected_entries, keys_not_found)


def _find_key(key_to_search: str, nested_dict: Dict[str, Any], key_matched_value: str = "YOUR_VALUE"):
    """
    Find the entry with matching key in a recursive dictionary and return dictionary with all levels and the matching entry set to the passed value.
    Returns only first occurance of given key.

    :param key_to_search (str): dictionary key to search for
    :param nested_dict (Dict[str, Any]): nested dictionry to search for given key
    :param key_matched_value (str, optional): value of dict entry matching for given key in the returned dictionary. Defaults to "YOUR_VALUE".

    Returns: dictionary indicating the probably right nested position of the given key, value set to key_matched_value
    """
    hierarchical_key = {}
    for key, val in nested_dict.items():
        if key == key_to_search:
            hierarchical_key[key] = key_matched_value
            return hierarchical_key
        elif isinstance(val, dict):
            sub_key_path = _find_key(key_to_search, val, key_matched_value)
            if sub_key_path:
                hierarchical_key[key] = sub_key_path
                return hierarchical_key
    return hierarchical_key


def _compare_dicts(
    superset: Dict[str, Any],
    subset: Dict[str, Any],
    missing_value: str = "!!! THIS PARAM NAME IS NOT VALID OR WRONG POSITION !!!",
):
    """
    Compare two dicts and return dictionary with enties from subset which are not present in the superset dict.
    Value of those missing entries are set to a special value, see parameters

    Args:
    :param superset (Dict[str, Any]): dict to search in, having e.g. all configuration entries
    :param subset (Dict[str, Any]): dict entreis which should be contained in superset
    :param missing_value (str): value to be used in result dictionary to indicate that a certain entry is not valid
    :return dictionary of entries of subset which are not present in superset, their value set to missin_value

    Returns:
        [type]: [description]
    """
    wrong_entries = {}
    for key, value in subset.items():
        if key in superset:
            if isinstance(subset[key], dict):
                subdict_wrong_entries = _compare_dicts(superset[key], subset[key])
                if subdict_wrong_entries:
                    wrong_entries[key] = subdict_wrong_entries
        else:
            wrong_entries[key] = missing_value
    return wrong_entries


def get_config_file_pathes(package, config_file_attr: str = "_default_config_file", recursive=True):
    """
    Get all configuration files within a package

    :param package: package (name or actual module) to search in
    :param config_file_attr: name of attribute to look for, defaults to "_default_config_file"
    :param recursive: if true, go through modules recursively

    :return List[str] filepathes of config files
    """
    if isinstance(package, str):
        package = importlib.import_module(package)
    configs = set()
    for loader, name, is_pkg in pkgutil.walk_packages(package.__path__):
        full_name = package.__name__ + "." + name
        the_mod = importlib.import_module(full_name)
        if hasattr(the_mod, config_file_attr):
            configs.add(getattr(the_mod, config_file_attr))
        if recursive and is_pkg:
            configs.update(get_config_file_pathes(full_name))
    return configs
