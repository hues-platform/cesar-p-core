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
from typing import Dict, List, Set, Any, Tuple, Mapping, Union
import pint
from eppy.modeleditor import IDF
import copy

from cesarp.model.BuildingElement import BuildingElement
from cesarp.model.Construction import Construction
from cesarp.model.WindowConstruction import WindowGlassConstruction
from cesarp.model.ShadingObjectConstruction import ShadingObjectConstruction
from cesarp.model.BuildingConstruction import BuildingConstruction
from cesarp.eplus_adapter import idf_writer_construction


class ConstructionIDFWritingHandler:
    """
    Handles looking up the name of the construction for ConstructionAsIDF objects.
    On initialization, constructions to be used for the main building and the neighbouring shading objects are passed.
    The class caches the names so that the lookup is not done repeatedly, which increases the runtime a lot (name lookup is done for each wall, window, and each neighbour,
    leading to many calls making the caching worse it...)
    """

    def __init__(
        self,
        main_building_construction: BuildingConstruction,
        shading_surfaces_construction: Mapping[str, ShadingObjectConstruction],
        unit_reg: pint.UnitRegistry,
    ):
        self.unit_reg = unit_reg
        self._main_building_construction = main_building_construction
        self._shading_surfaces_construction = shading_surfaces_construction
        self.__constr_idf_obj_names_cache: Dict[str, str] = dict()
        self.__win_idf_obj_names_cache: Dict[str, str] = dict()

    def add_construction(self, idf: IDF, bldg_elem: BuildingElement) -> str:
        """
        Adds the window glass construcction to the IDF, modifies the python IDF object in place!
        :param idf: IDF python object to add construction, object is modified in place
        :param bldg_elem: building element for which to add the construction. special handling for window not included, see separate methods below.
        :return: name of added idf construction
        """
        assert bldg_elem != BuildingElement.WINDOW, "please use add_window_frame/glass_construction() for BuildingElement WINDOW instead of using add_construction()"
        if bldg_elem == BuildingElement.INTERNAL_FLOOR:
            construction: Union[WindowGlassConstruction, Construction] = self._main_building_construction.get_construction_for_bldg_elem(BuildingElement.INTERNAL_CEILING)
            if isinstance(construction, Construction):
                construction = copy.deepcopy(construction)
                construction.name = f"{construction.name}_mirrored"
                construction.layers.reverse()
        else:
            construction = self._main_building_construction.get_construction_for_bldg_elem(bldg_elem)
        if construction.name in self.__constr_idf_obj_names_cache.keys():
            return self.__constr_idf_obj_names_cache[construction.name]
        if isinstance(construction, Construction):
            idf_obj_name = idf_writer_construction.add_detailed_construction(idf, construction, self.unit_reg)
        else:
            raise Exception(f"{__name__} cannot handle construction of tpye {type(construction)} used for building element {bldg_elem}")

        self.__constr_idf_obj_names_cache[construction.name] = idf_obj_name
        return idf_obj_name

    def add_window_glass_construction(self, idf: IDF) -> str:
        """
        Adds the window glass construcction of the main building to the IDF, modifies the python IDF object in place!
        :param idf: IDF python object to add window glass construction
        :return: name of added idf construction
        """
        win_glass_constr = self._main_building_construction.window_constr.glass
        return self.__add_specific_window_glass_construction(idf, win_glass_constr, ureg=self.unit_reg)

    def add_win_frame_construction(self, idf: IDF) -> Tuple[str, Any]:
        """
        :param idf_win_frame_obj: eppy EpBunch object for window frame and divider
        :return: nothing, passed object is adapted in place
        """
        return idf_writer_construction.add_win_frame_construction(idf, self._main_building_construction.window_constr.frame, self.unit_reg)

    def add_shading_surface_construction(self, idf: IDF, bldg_elem: BuildingElement) -> Any:
        """
        Adds a ShadingProperty:Reflectance idf object. The object is not linked to a surface geometry here,
        thus make sure to set property "Shading_Surface_Name" on the EpBunch object to link it to a geometry!

        :param idf: IDF python object to add construction, object is modified in place
        :param bldg_elem: building element which to add as a shading construction, either ROOF or WALL are available (for EnergyPlus it makes no difference,
                          but Cesar has different reflectance parameters for those two BuildingElement when used as a shading surface
        :return: eppy EpBunch of added ShadingProperty:Reflectance idf object, make sure to set "Shading_Surface_Name" on returned object!
        """
        assert bldg_elem in [BuildingElement.ROOF, BuildingElement.WALL], f"only ROOF and WALL supported as shading surfaces, but {bldg_elem.name} was requested"
        shading_constr = self._shading_surfaces_construction[bldg_elem.name]
        glass_constr = shading_constr.window_glass_construction
        glass_construction_idf_obj_name = self.__add_specific_window_glass_construction(idf, glass_constr, ureg=self.unit_reg)
        return idf_writer_construction.add_shading_surface_construction(idf, shading_constr, glass_construction_idf_obj_name, self.unit_reg)

    def __add_specific_window_glass_construction(self, idf: IDF, win_glass_constr: WindowGlassConstruction, ureg: pint.UnitRegistry) -> str:
        if win_glass_constr.name in self.__win_idf_obj_names_cache:
            return self.__win_idf_obj_names_cache[win_glass_constr.name]
        return idf_writer_construction.add_win_glass_construction(idf, win_glass_constr, ureg)

    @staticmethod
    def unique_elements_of_list(orig_list: List[Any]):
        """
        Removes double entries from orig_list preserving the order of its items, creating a new list

        :param orig_list: original list
        :return: List[Any] with unique entries
        """
        seen: Set[Any] = set()
        seen_add = seen.add
        return [x for x in orig_list if not (x in seen or seen_add(x))]
